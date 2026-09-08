with source as (
    select *
    from {{ ref('raw_loads') }}
),

normalized as (
    select
        cast(loadsmart_id as bigint) as loadsmart_id,
        trim(lane) as lane,
        try_strptime(quote_date, '%m/%d/%Y %H:%M') as quote_at,
        try_strptime(book_date, '%m/%d/%Y %H:%M') as booked_at,
        try_strptime(source_date, '%m/%d/%Y %H:%M') as sourced_at,
        try_strptime(pickup_date, '%m/%d/%Y %H:%M') as pickup_at,
        try_strptime(delivery_date, '%m/%d/%Y %H:%M') as delivered_at,
        cast(book_price as double) as book_price,
        cast(source_price as double) as source_price,
        cast(pnl as double) as pnl,
        cast(mileage as double) as mileage,
        upper(trim(equipment_type)) as equipment_type,
        cast(carrier_rating as double) as carrier_rating,
        nullif(trim(sourcing_channel), '') as sourcing_channel,
        cast(vip_carrier as boolean) as vip_carrier,
        cast(carrier_dropped_us_count as integer) as carrier_dropped_us_count,
        nullif(trim(carrier_name), '') as carrier_name,
        nullif(trim(shipper_name), '') as shipper_name,
        cast(carrier_on_time_to_pickup as boolean) as carrier_on_time_to_pickup,
        cast(carrier_on_time_to_delivery as boolean) as carrier_on_time_to_delivery,
        cast(carrier_on_time_overall as boolean) as carrier_on_time_overall,
        try_strptime(pickup_appointment_time, '%m/%d/%Y %H:%M') as pickup_appointment_at,
        try_strptime(delivery_appointment_time, '%m/%d/%Y %H:%M') as delivery_appointment_at,
        cast(has_mobile_app_tracking as boolean) as has_mobile_app_tracking,
        cast(has_macropoint_tracking as boolean) as has_macropoint_tracking,
        cast(has_edi_tracking as boolean) as has_edi_tracking,
        cast(contracted_load as boolean) as contracted_load,
        cast(load_booked_autonomously as boolean) as load_booked_autonomously,
        cast(load_sourced_autonomously as boolean) as load_sourced_autonomously,
        cast(load_was_cancelled as boolean) as load_was_cancelled,
        row_number() over (partition by loadsmart_id order by quote_date, book_date) as duplicate_rank
    from source
),

parsed_lane as (
    select * exclude (duplicate_rank),
        trim(split_part(lane, ' -> ', 1)) as pickup_location,
        trim(split_part(lane, ' -> ', 2)) as delivery_location
    from normalized
    where duplicate_rank = 1
),

final as (
    select
        d.loadsmart_id,
        d.lane,
        trim(split_part(d.pickup_location, ',', 1)) as pickup_city,
        upper(trim(split_part(d.pickup_location, ',', 2))) as pickup_state,
        trim(split_part(d.delivery_location, ',', 1)) as delivery_city,
        upper(trim(split_part(d.delivery_location, ',', 2))) as delivery_state,
        d.quote_at,
        d.booked_at,
        d.sourced_at,
        d.pickup_at,
        d.delivered_at,
        d.book_price,
        d.source_price,
        d.pnl,
        d.mileage,
        d.equipment_type,
        d.carrier_rating,
        d.sourcing_channel,
        d.vip_carrier,
        d.carrier_dropped_us_count,
        d.carrier_name,
        d.shipper_name,
        d.carrier_on_time_to_pickup,
        d.carrier_on_time_to_delivery,
        d.carrier_on_time_overall,
        d.pickup_appointment_at,
        d.delivery_appointment_at,
        d.has_mobile_app_tracking,
        d.has_macropoint_tracking,
        d.has_edi_tracking,
        d.contracted_load,
        d.load_booked_autonomously,
        d.load_sourced_autonomously,
        d.load_was_cancelled,
        not d.load_was_cancelled and d.delivered_at is not null as is_delivered,
        case
            when upper(trim(split_part(d.pickup_location, ',', 2))) = upper(trim(split_part(d.delivery_location, ',', 2)))
                then 'intrastate'
            else 'interstate'
        end as haul_type
    from parsed_lane d
)
select * from final
