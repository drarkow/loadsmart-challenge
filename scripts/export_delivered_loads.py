"""Export delivered loads from the dimensional model for the latest full month with delivery activity."""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


SQL = """
with monthly as (
    select
        date_trunc('month', delivery_date) as delivery_month,
        count(*) as delivered_loads
    from analytics.fct_loads
    where is_delivered
    group by 1
),
latest_full as (
    select max(delivery_month) as delivery_month
    from monthly
    where delivery_month < (select max(delivery_month) from monthly)
),
export as (
    select
        f.loadsmart_id,
        s.shipper_name,
        f.delivery_date,
        l.pickup_city,
        l.pickup_state,
        l.delivery_city,
        l.delivery_state,
        f.book_price,
        c.carrier_name
    from analytics.fct_loads f
    left join analytics.dim_shipper s using (shipper_key)
    left join analytics.dim_carrier c using (carrier_key)
    left join analytics.dim_lane l using (lane_key)
    cross join latest_full m
    where f.is_delivered
      and date_trunc('month', f.delivery_date) = m.delivery_month
)
select * from export order by delivery_date, loadsmart_id
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duckdb", default="data/loadsmart.duckdb")
    parser.add_argument("--output", default="analysis/delivered_loads_latest_full_month.csv")
    args = parser.parse_args()

    with duckdb.connect(args.duckdb, read_only=True) as con:
        frame = con.execute(SQL).fetchdf()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(f"Exported {len(frame):,} rows to {output}")


if __name__ == "__main__":
    main()
