The challenge CSV is intentionally kept outside the dbt seed directory during setup.
Copy the supplied CSV to this folder as `raw_loads.csv` before running `dbt seed`.

This preserves the distinction between:
- the supplied raw artifact;
- the dbt-managed raw/seed relation; and
- downstream staging/mart models.
