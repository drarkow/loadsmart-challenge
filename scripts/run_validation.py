from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "loadsmart.duckdb"


QUERIES = {
    "Q1": """
        select
            count(*) as delivered_loads
        from main_analytics.fct_loads
        where is_delivered
          and delivery_date >= date '2025-02-01'
          and delivery_date < date '2025-03-01'
    """,

    "Q2": """
        select
            ds.shipper_name,
            sum(f.book_price) as total_book_price
        from main_analytics.fct_loads f
        join main_analytics.dim_shipper ds
            using (shipper_key)
        group by 1
        order by 2 desc
        limit 1
    """,

    "Q3": """
        select
            dl.pickup_state,
            avg(f.book_price) as avg_book_price,
            count(*) as load_count
        from main_analytics.fct_loads f
        join main_analytics.dim_lane dl
            using (lane_key)
        group by 1
        order by 1
    """,

    "Q4": """
        select
            dl.lane,
            count(*) as delivered_loads
        from main_analytics.fct_loads f
        join main_analytics.dim_lane dl
            using (lane_key)
        where f.is_delivered
        group by 1
        order by 2 desc, 1
        limit 5
    """,

    "Q5": """
        select
            dc.carrier_name,
            count(*) as delivered_loads_into_tx
        from main_analytics.fct_loads f
        join main_analytics.dim_carrier dc
            using (carrier_key)
        join main_analytics.dim_lane dl
            using (lane_key)
        where f.is_delivered
          and dl.delivery_state = 'TX'
        group by 1
        order by 2 desc, 1
        limit 1
    """,

    "Q6": """
        select
            haul_type,
            avg(book_price) as avg_book_price,
            count(*) as load_count
        from main_analytics.fct_loads
        group by 1
        order by 1
    """,

    "Q7": """
        with top_shipper as (
            select
                shipper_key
            from main_analytics.fct_loads
            where is_delivered
            group by 1
            order by count(*) desc, shipper_key
            limit 1
        ),

        monthly_volume as (
            select
                date_trunc('month', f.delivery_date) as delivery_month,
                count(*) as delivered_loads
            from main_analytics.fct_loads f
            join top_shipper t
                using (shipper_key)
            where f.is_delivered
            group by 1
        )

        select
            d.month_start_date as delivery_month,
            coalesce(m.delivered_loads, 0) as delivered_loads
        from main_analytics.dim_date d
        left join monthly_volume m
            on d.month_start_date = m.delivery_month
        where d.date_day = d.month_start_date
        and d.month_start_date between
            date '2024-01-01'
            and date '2025-03-01'
        order by d.month_start_date;
    """,

    "Q8": """
        select
            dl.lane,
            count(*) as delivered_loads,
            avg(f.book_price) as avg_book_price
        from main_analytics.fct_loads f
        join main_analytics.dim_lane dl
            using (lane_key)
        where f.is_delivered
        group by 1
        having count(*) >= 10
        order by 3 desc, 2 desc, 1
        limit 1
    """,
}


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    try:
        for question, sql in QUERIES.items():
            print("\n" + "=" * 70)
            print(question)
            print("=" * 70)

            result = con.execute(sql)

            if result.description is None:
                print("Query executed successfully but returned no result set.")
                continue

            dataframe = result.fetchdf()
            print(dataframe.to_string(index=False))

    finally:
        con.close()


if __name__ == "__main__":
    main()