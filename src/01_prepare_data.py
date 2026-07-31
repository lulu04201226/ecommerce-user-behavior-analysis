"""Clean the anonymous visit-level ecommerce dataset.

Input:  data/raw/user_behavior.csv
Output: data/processed/user_behavior_clean.csv
        analysis/data_quality_summary.json
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "user_behavior.csv"
PROCESSED = ROOT / "data" / "processed" / "user_behavior_clean.csv"
QUALITY = ROOT / "analysis" / "data_quality_summary.json"

REQUIRED_COLUMNS = [
    "new_user",
    "age",
    "sex",
    "market",
    "device",
    "operative_system",
    "source",
    "total_pages_visited",
    "home_page",
    "listing_page",
    "product_page",
    "payment_page",
    "confirmation_page",
]
FUNNEL_COLUMNS = [
    "home_page",
    "listing_page",
    "product_page",
    "payment_page",
    "confirmation_page",
]


def main() -> None:
    if not RAW.exists():
        raise FileNotFoundError(
            f"Missing {RAW}. See data/README.md for the required schema."
        )

    raw = pd.read_csv(RAW)
    missing = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = raw[REQUIRED_COLUMNS].copy()
    df.insert(0, "record_id", np.arange(1, len(df) + 1))

    for col in ["new_user", "total_pages_visited", *FUNNEL_COLUMNS]:
        df[col] = pd.to_numeric(df[col], errors="raise")

    invalid_binary = {
        col: sorted(set(df[col].dropna().unique()) - {0, 1})
        for col in ["new_user", *FUNNEL_COLUMNS]
    }
    invalid_binary = {k: v for k, v in invalid_binary.items() if v}
    if invalid_binary:
        raise ValueError(f"Non-binary funnel values found: {invalid_binary}")

    df["age_raw"] = pd.to_numeric(df["age"], errors="coerce")
    df["age_is_valid"] = df["age_raw"].between(17, 100)
    df["age"] = df["age_raw"].where(df["age_is_valid"])

    for col in ["sex", "device", "operative_system", "source"]:
        df[col] = df[col].replace({0: "未知", "0": "未知"}).fillna("未知")

    df["user_type"] = df["new_user"].map({0: "老用户", 1: "新用户"})
    df["market_label"] = "市场" + df["market"].astype(str)
    df["age_band"] = pd.cut(
        df["age"],
        bins=[16, 24, 29, 34, 39, 49, 100],
        labels=["17–24岁", "25–29岁", "30–34岁", "35–39岁", "40–49岁", "50岁以上"],
    ).astype("object")
    df["age_band"] = df["age_band"].fillna("异常/未知")
    df["pages_band"] = pd.cut(
        df["total_pages_visited"],
        bins=[0, 2, 4, 6, 8, 10, np.inf],
        labels=["1–2页", "3–4页", "5–6页", "7–8页", "9–10页", "11页以上"],
    ).astype("object")
    df["converted"] = df["confirmation_page"].astype(int)

    violations = {}
    for left, right in zip(FUNNEL_COLUMNS, FUNNEL_COLUMNS[1:]):
        violations[f"{left}->{right}"] = int(
            ((df[left] == 0) & (df[right] == 1)).sum()
        )

    quality = {
        "row_count": int(len(df)),
        "column_count_raw": int(raw.shape[1]),
        "grain": "one anonymous visit record per row; not a unique user",
        "null_cells_raw": int(raw.isna().sum().sum()),
        "exact_duplicate_rows": int(raw.duplicated().sum()),
        "invalid_age_count": int((~df["age_is_valid"]).sum()),
        "unknown_source_count": int((df["source"] == "未知").sum()),
        "logical_funnel_violations": violations,
        "has_user_id": False,
        "has_session_id": False,
        "has_timestamp": False,
    }

    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    QUALITY.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED, index=False, encoding="utf-8-sig")
    QUALITY.write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"rows={len(df):,}")
    print(f"overall_conversion={df['converted'].mean():.2%}")
    print(f"output={PROCESSED}")


if __name__ == "__main__":
    main()

