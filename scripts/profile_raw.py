from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "raw" / "loads.csv"
OUTPUT = ROOT / "analysis" / "raw_profile.json"


def main() -> None:
    df = pd.read_csv(INPUT)
    profile = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": {},
        "duplicate_row_count": int(df.duplicated().sum()),
    }

    for col in df.columns:
        series = df[col]
        profile["columns"][col] = {
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "null_pct": round(float(series.isna().mean() * 100), 3),
            "distinct_count": int(series.nunique(dropna=True)),
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(f"Profile written to {OUTPUT}")


if __name__ == "__main__":
    main()
