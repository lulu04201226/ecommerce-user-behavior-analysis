"""Create the main report charts from cleaned data and audit outputs."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "user_behavior_clean.csv"
ANALYSIS = ROOT / "analysis"
OUT = ROOT / "assets" / "generated"

BLUE = "#2F6BDE"
ORANGE = "#E69138"
INK = "#1F2937"
GRID = "#E5EAF2"

plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def style(ax: plt.Axes) -> None:
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def label_bars(ax: plt.Axes, bars, values, suffix: str = "") -> None:
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value}{suffix}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=INK,
        )


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError("Run src/01_prepare_data.py first.")

    df = pd.read_csv(DATA)
    OUT.mkdir(parents=True, exist_ok=True)

    # Funnel reach
    funnel = pd.read_csv(ANALYSIS / "funnel_audit.csv")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.bar(funnel["stage"], funnel["reached_records"], color=BLUE)
    label_bars(ax, bars, [f"{x:,}" for x in funnel["reached_records"]])
    ax.set_title("五级漏斗到达量", loc="left", weight="bold")
    ax.set_ylabel("访问记录")
    style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "funnel_reach.png", dpi=180, facecolor="white")
    plt.close(fig)

    # Visit depth: structural zeros are shown in gray.
    depth = pd.read_csv(ANALYSIS / "visit_depth_analysis.csv")
    rates = depth["conversion_rate"] * 100
    colors = ["#C9CED6" if "结构性" in x else BLUE for x in depth["zero_type"]]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.bar(depth["pages_band"], rates, color=colors)
    labels = [
        f"{rate:.2f}%\nn={n:,}" for rate, n in zip(rates, depth["records"])
    ]
    label_bars(ax, bars, labels)
    ax.set_title("访问深度与最终转化率", loc="left", weight="bold")
    ax.set_ylabel("最终转化率")
    style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "visit_depth_conversion.png", dpi=180, facecolor="white")
    plt.close(fig)

    # Channel raw vs standardized
    channel = pd.read_csv(ANALYSIS / "channel_standardization_summary.csv")
    x = range(len(channel))
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    raw = ax.bar(
        [i - 0.18 for i in x], channel["raw_rate"] * 100, 0.36, label="原始", color=ORANGE
    )
    adjusted = ax.bar(
        [i + 0.18 for i in x],
        channel["standardized_rate_user_device"] * 100,
        0.36,
        label="结构标准化",
        color=BLUE,
    )
    ax.set_xticks(list(x), channel["source"])
    ax.legend(frameon=False)
    ax.set_title("渠道原始与结构标准化转化率", loc="left", weight="bold")
    ax.set_ylabel("最终转化率")
    label_bars(ax, raw, [f"{x:.2f}%" for x in channel["raw_rate"] * 100])
    label_bars(
        ax,
        adjusted,
        [f"{x:.2f}%" for x in channel["standardized_rate_user_device"] * 100],
    )
    style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "channel_standardization.png", dpi=180, facecolor="white")
    plt.close(fig)

    print(f"charts={OUT}")


if __name__ == "__main__":
    main()
