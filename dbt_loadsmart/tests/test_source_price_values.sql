{{ config(severity="warn") }}

select
    loadsmart_id,
    source_price,
    load_was_cancelled,
    is_delivered
from {{ ref('stg_loads') }}
where source_price = 0
  and is_delivered