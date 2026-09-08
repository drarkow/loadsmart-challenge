-- Independent validation queries for the eight challenge questions.
-- These are NOT the Claude-generated queries; they are reviewer baselines.

-- Q1. February 2025 is the last complete calendar month before the March 15, 2025 endpoint.
select count(*) as delivered_loads
from analytics.fct_loads
where is_delivered
  and delivery_date >= date '2025-02-01'
  and delivery_date < date '2025-03-01';

-- Q2. Highest total book price across all modeled loads.
select ds.shipper_name, sum(f.book_price) as total_book_price
from analytics.fct_loads f
join analytics.dim_shipper ds using (shipper_key)
group by 1
order by 2 desc
limit 1;

-- Q3. Average book price by pickup state across all modeled loads.
select dl.pickup_state, avg(f.book_price) as avg_book_price
from analytics.fct_loads f
join analytics.dim_lane dl using (lane_key)
group by 1
order by 1;

-- Q4. Top 5 lanes by delivered-load count.
select dl.lane, count(*) as delivered_loads
from analytics.fct_loads f
join analytics.dim_lane dl using (lane_key)
where f.is_delivered
group by 1
order by 2 desc, 1
limit 5;

-- Q5. Carrier moving the most delivered loads into Texas.
select dc.carrier_name, count(*) as delivered_loads_into_tx
from analytics.fct_loads f
join analytics.dim_carrier dc using (carrier_key)
join analytics.dim_lane dl using (lane_key)
where f.is_delivered
  and dl.delivery_state = 'TX'
group by 1
order by 2 desc, 1
limit 1;

-- Q6. Average book price by modeled haul type across all loads.
select haul_type, avg(book_price) as avg_book_price, count(*) as load_count
from analytics.fct_loads
group by 1
order by 1;

-- Q7. Monthly delivered volume for the shipper with the most delivered loads.
with top_shipper as (
    select shipper_key
    from analytics.fct_loads
    where is_delivered
    group by 1
    order by count(*) desc, 1
    limit 1
)
select f.delivery_date, count(*) as delivered_loads
from analytics.fct_loads f
join top_shipper t using (shipper_key)
where f.is_delivered
group by 1
order by 1;

-- Q8. Highest average book price among lanes with at least 10 delivered loads.
select dl.lane, count(*) as delivered_loads, avg(f.book_price) as avg_book_price
from analytics.fct_loads f
join analytics.dim_lane dl using (lane_key)
where f.is_delivered
group by 1
having count(*) >= 10
order by 3 desc, 2 desc, 1
limit 1;
