"""电商用户行为漏斗与转化增长分析 Streamlit Dashboard。"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="电商转化增长分析", page_icon="🛍️", layout="wide")
ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
BLUE, RED, GREEN, SLATE = "#2563EB", "#DC2626", "#16A34A", "#64748B"


@st.cache_data(show_spinner=False)
def load_tables():
    files = {
        "funnel": "funnel_audit.csv",
        "user": "user_type_transition_audit.csv",
        "depth": "visit_depth_analysis.csv",
        "channel": "channel_standardization_summary.csv",
        "uplift": "uplift_scenarios.csv",
    }
    return {key: pd.read_csv(ANALYSIS / name) for key, name in files.items()}


def card(title, value, note, color=BLUE):
    st.markdown(
        f'<div class="metric-card" style="border-top:4px solid {color}">'
        f'<div class="metric-title">{title}</div><div class="metric-value">{value}</div>'
        f'<div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def funnel_figure(data):
    fig = go.Figure(go.Funnel(
        y=data["stage"], x=data["reached_records"],
        textinfo="value+percent initial+percent previous",
        marker={"color": ["#BFDBFE", "#93C5FD", "#60A5FA", "#3B82F6", BLUE]},
        hovertemplate="%{y}<br>到达量：%{x:,}<br>占首页：%{percentInitial:.2%}<br>环节保留：%{percentPrevious:.2%}<extra></extra>",
    ))
    fig.update_layout(height=450, margin={"l": 20, "r": 20, "t": 15, "b": 15})
    return fig


def loss_figure(data):
    plot = data.iloc[1:].copy()
    plot["环节"] = data["stage"].shift(1).iloc[1:].values + " → " + plot["stage"]
    plot["流失率"] = 1 - plot["step_rate"]
    fig = px.bar(plot, x="流失率", y="环节", orientation="h",
                 text=plot["流失率"].map(lambda x: f"{x:.2%}"),
                 custom_data=["lost_records", "denominator"], color="流失率",
                 color_continuous_scale=["#BFDBFE", "#FCA5A5", RED])
    fig.update_traces(textposition="outside", hovertemplate="%{y}<br>流失率：%{x:.2%}<br>流失量：%{customdata[0]:,}<br>样本 n=%{customdata[1]:,}<extra></extra>")
    fig.update_layout(height=390, xaxis_tickformat=".0%", xaxis_title="流失率", yaxis_title="", coloraxis_showscale=False, margin={"l": 10, "r": 70, "t": 15, "b": 10})
    return fig


def user_figure(data, users):
    plot = data[data["user_type"].isin(users)].copy()
    fig = px.bar(plot, x="transition", y="rate", color="user_type", barmode="group",
                 text=plot["rate"].map(lambda x: f"{x:.2%}"), custom_data=["numerator", "denominator"],
                 color_discrete_map={"新用户": "#60A5FA", "老用户": BLUE},
                 labels={"transition": "漏斗环节", "rate": "环节转化率", "user_type": "用户类型"})
    fig.update_traces(textposition="outside", hovertemplate="%{x}<br>转化率：%{y:.2%}<br>转化数 n=%{customdata[0]:,}<br>分母 n=%{customdata[1]:,}<extra></extra>")
    fig.update_layout(height=430, yaxis_tickformat=".0%", legend_title_text="", margin={"l": 10, "r": 10, "t": 15, "b": 10})
    return fig


def depth_figure(data, include_structural):
    order = ["1–2页", "3–4页", "5–6页", "7–8页", "9–10页", "11页以上"]
    plot = data.copy() if include_structural else data[data["zero_type"] == "可比较分组"].copy()
    plot["pages_band"] = pd.Categorical(plot["pages_band"], categories=order, ordered=True)
    plot = plot.sort_values("pages_band")
    colors = [SLATE if "结构性" in value else BLUE for value in plot["zero_type"]]
    fig = go.Figure(go.Bar(
        x=plot["pages_band"], y=plot["conversion_rate"], marker_color=colors,
        text=[f"{rate:.2%}<br>n={n:,}" for rate, n in zip(plot["conversion_rate"], plot["records"])],
        textposition="outside", customdata=plot[["records", "conversions", "zero_type"]],
        hovertemplate="%{x}<br>转化率：%{y:.2%}<br>样本 n=%{customdata[0]:,}<br>确认数：%{customdata[1]:,}<br>%{customdata[2]}<extra></extra>",
    ))
    fig.update_layout(height=430, yaxis_tickformat=".0%", xaxis_title="访问深度", yaxis_title="确认页转化率", margin={"l": 10, "r": 10, "t": 35, "b": 10})
    return fig


def channel_figure(data):
    plot = data.rename(columns={"raw_rate": "原始转化率", "standardized_rate_user_device": "结构标准化转化率"}).melt(
        id_vars=["source", "records"], value_vars=["原始转化率", "结构标准化转化率"], var_name="口径", value_name="转化率")
    fig = px.bar(plot, x="source", y="转化率", color="口径", barmode="group",
                 text=plot["转化率"].map(lambda x: f"{x:.2%}"), custom_data=["records"],
                 color_discrete_map={"原始转化率": "#94A3B8", "结构标准化转化率": BLUE}, labels={"source": "渠道"})
    fig.update_traces(textposition="outside", hovertemplate="%{x}<br>转化率：%{y:.2%}<br>渠道样本 n=%{customdata[0]:,}<extra></extra>")
    fig.update_layout(height=430, yaxis_tickformat=".1%", yaxis_title="确认页转化率", legend_title_text="", margin={"l": 10, "r": 10, "t": 20, "b": 10})
    return fig


def uplift_figure(data, lifts):
    plot = data[data["lift_pp"].isin(lifts)].copy()
    fig = px.bar(plot, x="lift_pp", y="extra_confirmations",
                 text=plot["extra_confirmations"].map(lambda x: f"+{x:,.0f}"),
                 custom_data=["extra_payments", "relative_confirmations_lift"],
                 color="relative_confirmations_lift", color_continuous_scale=["#BFDBFE", BLUE],
                 labels={"lift_pp": "商品页→支付页提升（百分点）", "extra_confirmations": "预计新增确认记录"})
    fig.update_traces(textposition="outside", hovertemplate="环节提升：%{x:.1f}pp<br>新增支付：%{customdata[0]:,.0f}<br>新增确认：%{y:,.0f}<br>确认量增幅：%{customdata[1]:.2%}<extra></extra>")
    fig.update_layout(height=410, coloraxis_showscale=False, margin={"l": 10, "r": 10, "t": 20, "b": 10})
    return fig


st.markdown("""
<style>
.block-container{padding-top:1.7rem;padding-bottom:3rem;max-width:1450px}
.metric-card{background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:15px 16px;min-height:150px;box-shadow:0 1px 3px rgba(15,23,42,.05)}
.metric-title{font-size:.88rem;font-weight:700;color:#64748B}.metric-value{font-size:1.82rem;font-weight:800;color:#0F172A;margin:11px 0 8px}.metric-note{font-size:.82rem;color:#64748B;line-height:1.45}
.insight{background:#EFF6FF;border-left:4px solid #2563EB;border-radius:8px;padding:13px 15px;margin:8px 0 18px;color:#1E3A8A}
.action-card{border-radius:12px;padding:16px 18px;min-height:164px;border:1px solid rgba(15,23,42,.08)}.action-title{font-weight:800;color:#0F172A;margin-bottom:9px}.action-body{font-size:.9rem;color:#334155;line-height:1.65}
</style>""", unsafe_allow_html=True)

st.title("🛍️ 电商用户行为漏斗与转化增长分析")
st.markdown("基于 **100,000 条匿名访问记录**，从五级漏斗定位转化瓶颈，拆解新老用户与访问深度差异，并通过用户类型 × 设备标准化校正渠道结构偏差。")

try:
    t = load_tables()
except (FileNotFoundError, pd.errors.ParserError) as exc:
    st.error(f"数据加载失败：{exc}")
    st.stop()

funnel, user, depth, channel, uplift = t["funnel"], t["user"], t["depth"], t["channel"], t["uplift"]
total, confirmations = int(funnel.iloc[0]["reached_records"]), int(funnel.iloc[-1]["reached_records"])
p0 = funnel.loc[funnel["stage"] == "支付页"].iloc[0]
direct = channel.loc[channel["source"] == "Direct"].iloc[0]

with st.sidebar:
    st.header("分析导航")
    focus = st.radio("当前关注", ["经营总览", "漏斗诊断", "用户拆解", "渠道校正", "增长测算"], label_visibility="collapsed")
    st.caption("所有图表均可悬停查看样本量与精确数值。")
    st.divider()
    st.markdown("**数据口径**")
    st.caption("粒度：匿名访问记录，不等同于独立用户")
    st.caption("样本：100,000 条｜渠道缺失：123 条")
    st.caption("来源：仓库内聚合审计表")

if focus != "经营总览":
    st.info(f"当前关注：{focus}。请切换下方同名标签页。")

st.subheader("核心指标概览")
for col, args in zip(st.columns(5), [
    ("访问记录", f"{total:,}", "全量匿名访问样本", SLATE),
    ("最终转化率", f"{confirmations / total:.2%}", f"确认记录 {confirmations:,} 条", BLUE),
    ("P0 环节转化率", f"{p0['step_rate']:.2%}", "商品页 → 支付页", RED),
    ("P0 绝对流失", f"{int(p0['lost_records']):,}", "全漏斗最大流失量", RED),
    ("Direct 标准化", f"{direct['standardized_rate_user_device']:.2%}", "原始 3.03%，校正结构后", GREEN),
]):
    with col: card(*args)

st.markdown('<div class="insight"><b>核心判断：</b>商品页 → 支付页同时具备较大的前序样本和最大的绝对流失，是首要实验对象；新用户与渠道结构用于预设分层和解释结果，不直接作为因果结论。</div>', unsafe_allow_html=True)

overview_tab, funnel_tab, user_tab, channel_tab, growth_tab = st.tabs(["经营总览", "漏斗诊断", "用户拆解", "渠道校正", "增长测算"])

with overview_tab:
    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("#### 五级漏斗到达量")
        st.plotly_chart(funnel_figure(funnel), use_container_width=True)
    with right:
        st.markdown("#### 环节流失率与绝对流失")
        st.plotly_chart(loss_figure(funnel), use_container_width=True)
    st.markdown("<b>30 秒结论：</b>整体确认页转化率为 <b>2.40%</b>；商品页 → 支付页流失 <b>42,756</b> 条，是优先级最高的增长瓶颈。", unsafe_allow_html=True)

with funnel_tab:
    st.markdown("#### 漏斗诊断")
    st.caption("同时展示环节分母、到达量与流失量，避免只看百分比造成优先级误判。")
    st.plotly_chart(funnel_figure(funnel), use_container_width=True)
    audit = funnel.rename(columns={"stage": "页面", "reached_records": "到达量", "denominator": "环节分母", "step_rate": "环节转化率", "lost_records": "流失量"}).copy()
    audit["环节转化率"] = audit["环节转化率"].map(lambda x: f"{x:.2%}")
    st.dataframe(audit, use_container_width=True)

with user_tab:
    st.markdown("#### 新老用户漏斗差异")
    selected_users = st.multiselect("选择用户类型", ["新用户", "老用户"], default=["新用户", "老用户"])
    if selected_users: st.plotly_chart(user_figure(user, selected_users), use_container_width=True)
    else: st.warning("请至少选择一种用户类型。")
    st.markdown("新老用户在漏斗前两步差异有限，差距主要在商品页之后扩大，因此新用户应作为 P0 实验的预设观察分层。")
    st.divider()
    st.markdown("#### 访问深度与最终转化")
    include_structural = st.checkbox("显示结构性不可达分组", value=True)
    st.plotly_chart(depth_figure(depth, include_structural), use_container_width=True)
    st.caption("注：访问深度＜5页的分组无法走完五级漏斗，0% 属于结构性零值，不纳入行为差异比较。所有柱均标注样本量 n。")

with channel_tab:
    st.markdown("#### 渠道原始转化率与结构标准化结果")
    st.caption("统一使用全体样本的“用户类型 × 设备”联合分布作为权重，减少渠道用户构成差异带来的偏差。")
    st.plotly_chart(channel_figure(channel), use_container_width=True)
    st.markdown("Direct 原始转化率 **3.03%**，标准化后约 **2.40%**，说明原始优势部分来自老用户占比较高。该结果接近整体均值是本次权重和分层组合后的数值结果，并非算法必然收敛。")
    display = channel.rename(columns={"source": "渠道", "records": "样本量 n", "raw_rate": "原始转化率", "standardized_rate_user_device": "结构标准化转化率", "empty_cells": "空分层数", "small_cells_lt30": "小样本分层数(<30)", "covered_weight": "覆盖权重"}).copy()
    for column in ["原始转化率", "结构标准化转化率", "覆盖权重"]: display[column] = display[column].map(lambda x: f"{x:.2%}")
    st.dataframe(display, use_container_width=True)
    st.caption("Direct、SEO、Ads 合计 99,877 条；其余 123 条渠道信息缺失，保留在整体转化率计算中但不参与渠道间比较。")

with growth_tab:
    st.markdown("#### 核心环节提升情景")
    lifts = st.multiselect("选择商品页 → 支付页提升幅度", uplift["lift_pp"].tolist(), default=uplift["lift_pp"].tolist(), format_func=lambda x: f"{x:.1f} 个百分点")
    if lifts: st.plotly_chart(uplift_figure(uplift, lifts), use_container_width=True)
    else: st.warning("请至少选择一个提升情景。")
    one = uplift.loc[uplift["lift_pp"] == 1.0].iloc[0]
    st.markdown(f"若核心环节提升 **1 个百分点**，约新增 **{one['extra_confirmations']:.0f} 条确认记录**，相当于当前确认量提升 **{one['relative_confirmations_lift']:.2%}**。")
    st.divider()
    st.markdown("#### 增长行动优先级")
    actions = [
        ("P0｜商品页决策效率", "优化核心卖点、信任元素、规格选择与购买入口；主指标为商品页→支付页转化率。", "#FEF2F2"),
        ("P1｜新用户首购路径", "预设新用户分层，测试首购权益与支付路径；同时监控老用户及下游护栏。", "#EFF6FF"),
        ("P1｜SEO / Ads 承接", "优化落地页与商品页一致性；同时报告原始值、用户结构与标准化结果。", "#F0FDF4"),
        ("P2｜移动端观察", "先验证设备交互，再决定是否独立立项，避免依据观察性差异直接追加投入。", "#FFFBEB"),
    ]
    for col, (title, body, bg) in zip(st.columns(4), actions):
        with col: st.markdown(f'<div class="action-card" style="background:{bg}"><div class="action-title">{title}</div><div class="action-body">{body}</div></div>', unsafe_allow_html=True)

st.divider()
st.caption("数据边界：每行代表匿名访问记录，不等同于独立用户；缺少用户、会话、时间、金额和成本字段，因此不计算 UV、留存、复购、趋势、GMV 或 ROI。情景测算用于确定实验优先级，不是上线效果承诺。")
