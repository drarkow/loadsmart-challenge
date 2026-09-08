select
    load_was_cancelled,
    is_delivered,
    count(*) as loads,
    sum(case when book_price = 0 then 1 else 0 end) as zero_book_price,
    sum(case when source_price = 0 then 1 else 0 end) as zero_source_price
from {{ ref('stg_loads') }}
group by 1, 2
order by 1, 2