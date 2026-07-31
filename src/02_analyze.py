"""Reproduce the main funnel, segment, channel and opportunity calculations."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "user_behavior_clean.csv"
OUT = ROOT / "analysis"

FUNNEL = [
    ("home_page", "首页"),
    ("listing_page", "列表页"),
    ("product_page", "商品页"),
    ("payment_page", "支付页"),
    ("confirmation_page", "确认页"),
]
CHANNELS = ["Direct", "Seo", "Ads"]


def funnel_audit(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    previous = len(df)
    for field, label in FUNNEL:
        reached = int(df[field].sum())
        rows.append(
            {
                "stage": label,
                "reached_records": reached,
                "denominator": previous,
                "step_rate": reached / previous,
                "lost_records": previous - reached,
            }
        )
        previous = reached
    return pd.DataFrame(rows)


def user_type_transitions(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for user_type, group in df.groupby("user_type"):
        for (left, left_label), (right, right_label) in zip(FUNNEL, FUNNEL[1:]):
            denominator = int(group[left].sum())
            numerator = int(group[right].sum())
            rows.append(
                {
                    "user_type": user_type,
                    "transition": f"{left_label}→{right_label}",
                    "numerator": numerator,
                    "denominator": denominator,
                    "rate": numerator / denominator if denominator else np.nan,
                }
            )
    return pd.DataFrame(rows)


def visit_depth(df: pd.DataFrame) -> pd.DataFrame:
    result = (
        df.groupby("pages_band", observed=False)["converted"]
        .agg(records="size", conversions="sum", conversion_rate="mean")
        .reset_index()
    )
    result["zero_type"] = np.where(
        result["pages_band"].isin(["1–2页", "3–4页"]),
        "结构性零值：不用于行为差异解释",
        "可比较分组",
    )
    return result


def channel_standardization(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    strata = ["user_type", "device"]
    weights = df.groupby(strata, dropna=False).size() / len(df)
    summaries = []
    cells = []

    for source in CHANNELS:
        channel = df[df["source"] == source]
        rates = (
            channel.groupby(strata, dropna=False)["converted"]
            .agg(records="size", conversions="sum", rate="mean")
        )
        aligned = weights.rename("weight").to_frame().join(rates)
        covered = aligned["rate"].notna()
        standardized = (
            aligned.loc[covered, "weight"] * aligned.loc[covered, "rate"]
        ).sum() / aligned.loc[covered, "weight"].sum()

        summaries.append(
            {
                "source": source,
                "records": int(len(channel)),
                "raw_rate": channel["converted"].mean(),
                "standardized_rate_user_device": standardized,
                "empty_cells": int((~covered).sum()),
                "small_cells_lt30": int((aligned["records"].fillna(0) < 30).sum()),
                "covered_weight": float(aligned.loc[covered, "weight"].sum()),
            }
        )
        cell = aligned.reset_index()
        cell["source"] = source
        cells.append(cell)

    return pd.DataFrame(summaries), pd.concat(cells, ignore_index=True)


def uplift_scenarios(df: pd.DataFrame) -> pd.DataFrame:
    product = int(df["product_page"].sum())
    payment = int(df["payment_page"].sum())
    confirmation = int(df["confirmation_page"].sum())
    downstream = confirmation / payment
    rows = []
    for lift_pp in [0.5, 1.0, 2.0, 3.0]:
        extra_payments = product * lift_pp / 100
        extra_confirmations = extra_payments * downstream
        rows.append(
            {
                "lift_pp": lift_pp,
                "extra_payments": extra_payments,
                "extra_confirmations": extra_confirmations,
                "relative_confirmations_lift": extra_confirmations / confirmation,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError("Run src/01_prepare_data.py first.")

    df = pd.read_csv(DATA)
    OUT.mkdir(parents=True, exist_ok=True)

    funnel_audit(df).to_csv(
        OUT / "funnel_audit.csv", index=False, encoding="utf-8-sig"
    )
    user_type_transitions(df).to_csv(
        OUT / "user_type_transition_audit.csv", index=False, encoding="utf-8-sig"
    )
    visit_depth(df).to_csv(
        OUT / "visit_depth_analysis.csv", index=False, encoding="utf-8-sig"
    )
    summary, cells = channel_standardization(df)
    summary.to_csv(
        OUT / "channel_standardization_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    cells.to_csv(
        OUT / "channel_standardization_cells.csv",
        index=False,
        encoding="utf-8-sig",
    )
    uplift_scenarios(df).to_csv(
        OUT / "uplift_scenarios.csv", index=False, encoding="utf-8-sig"
    )

    unknown = int((df["source"] == "未知").sum())
    print(f"overall_conversion={df['converted'].mean():.2%}")
    print(f"unknown_channel_records={unknown:,}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

