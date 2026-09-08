select
    md5(coalesce(shipper_name, '__unknown__')) as shipper_key,
    shipper_name
from (
    select distinct shipper_name from {{ ref('stg_loads') }}
)
