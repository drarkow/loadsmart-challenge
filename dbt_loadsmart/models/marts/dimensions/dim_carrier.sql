select
    md5(coalesce(carrier_name, '__unknown__')) as carrier_key,
    carrier_name
from (
    select distinct carrier_name from {{ ref('stg_loads') }}
)
