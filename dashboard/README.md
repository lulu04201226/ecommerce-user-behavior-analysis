# 电商转化增长分析 Dashboard

这是项目的 Streamlit 交互展示层，直接读取 `analysis/` 中的聚合审计表，不包含原始访问明细。

**在线体验：[打开 Dashboard](https://ecommerce-user-behavior-analysis.streamlit.app/)**

主要功能包括核心指标卡、五级漏斗、人群拆解、访问深度诊断、渠道结构校正和增长情景测算。

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

部署到 Streamlit Community Cloud 时，主文件路径填写 `dashboard/app.py`，无需配置 Secrets 或外部数据源。
