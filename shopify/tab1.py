import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import fmt_vnd, fmt_num, _ly, _hbar
from shopify.data import load_csv

_SAMPLE_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_shopify_orders.csv")

_REFUND_STATUSES     = {"refunded", "partially_refunded"}
_UNFULFILLED_STATUSES = {"unfulfilled", "partial"}


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df["Financial Status"]   = df["Financial Status"].str.lower().str.strip()
    df["Fulfillment Status"] = df["Fulfillment Status"].str.lower().str.strip()
    df["Total"]    = pd.to_numeric(df["Total"],    errors="coerce").fillna(0)
    df["Subtotal"] = pd.to_numeric(df["Subtotal"], errors="coerce").fillna(0)
    df["Created at"] = pd.to_datetime(df["Created at"])
    df["month_key"] = df["Created at"].dt.strftime("%Y-%m")
    df["month_str"] = df["Created at"].dt.strftime("%b %Y")
    return df


def render(uploaded_file=None):
    st.markdown("## 🏥 Business Health — Shopify")

    df_raw, source = load_csv(uploaded_file, _SAMPLE_CSV, parse_dates=["Created at"])
    if df_raw.empty:
        st.warning("Chưa có data. Upload file Orders (.csv) ở sidebar hoặc thêm sample data.")
        return
    df = _clean(df_raw.copy())

    # ── KPI metrics ────────────────────────────────────────────────────────────
    total_orders    = len(df)
    gmv             = df["Total"].sum()
    aov             = gmv / total_orders if total_orders > 0 else 0

    refund_count    = df["Financial Status"].isin(_REFUND_STATUSES).sum()
    refund_rate     = refund_count / total_orders * 100 if total_orders > 0 else 0

    fulfilled_count = (~df["Fulfillment Status"].isin(_UNFULFILLED_STATUSES)).sum()
    fulfillment_rate = fulfilled_count / total_orders * 100 if total_orders > 0 else 0

    net_revenue     = df[~df["Financial Status"].isin(_REFUND_STATUSES)]["Total"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Orders",     fmt_num(total_orders))
    c2.metric("GMV (gross)",      fmt_vnd(gmv))
    c3.metric("AOV",              fmt_vnd(aov))
    c4.metric("Refund Rate",      f"{refund_rate:.1f}%",
              delta=f"{refund_count} orders",
              delta_color="inverse")
    c5.metric("Fulfillment Rate", f"{fulfillment_rate:.1f}%",
              delta=f"{fulfilled_count} fulfilled")

    st.markdown(
        f'<div class="info-banner">'
        f'📦 {total_orders} orders &nbsp;|&nbsp; '
        f'Net Revenue (excl. refunds): <b>{fmt_vnd(net_revenue)}</b> &nbsp;|&nbsp; '
        f'{source}'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Monthly breakdown ──────────────────────────────────────────────────────
    monthly = (
        df.groupby("month_key", sort=True)
        .agg(
            orders=("Name", "count"),
            gmv=("Total", "sum"),
            refunds=("Financial Status", lambda x: x.isin(_REFUND_STATUSES).sum()),
            month_label=("month_str", "first"),
        )
        .reset_index()
    )

    col1, col2 = st.columns(2)

    # Monthly Order Count
    with col1:
        st.markdown("### Monthly Order Count")
        fig = go.Figure(go.Bar(
            x=monthly["month_label"],
            y=monthly["orders"],
            marker_color="#00d4ff",
            text=monthly["orders"],
            textposition="outside",
            textfont=dict(color="#e0e0e0", size=11),
        ))
        fig.update_layout(**_ly(xaxis_title="Month", yaxis_title="Orders"))
        fig.update_layout(margin=dict(l=10, r=20, t=30, b=40))
        st.plotly_chart(fig, use_container_width=True, key="sf1_monthly_orders")

    # Monthly GMV
    with col2:
        st.markdown("### Monthly GMV (VNĐ)")
        fig = go.Figure(go.Bar(
            x=monthly["month_label"],
            y=monthly["gmv"],
            marker_color="#00ff88",
            text=[fmt_vnd(v) for v in monthly["gmv"]],
            textposition="outside",
            textfont=dict(color="#e0e0e0", size=10),
        ))
        fig.update_layout(**_ly(xaxis_title="Month", yaxis_title="GMV (VNĐ)"))
        fig.update_layout(margin=dict(l=10, r=20, t=30, b=40))
        st.plotly_chart(fig, use_container_width=True, key="sf1_monthly_gmv")

    st.markdown("---")

    # ── Financial & Fulfillment status breakdown ───────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### Financial Status")
        fin_counts = df["Financial Status"].value_counts().reset_index()
        fin_counts.columns = ["Status", "Count"]
        fin_colors = {
            "paid": "#00ff88",
            "refunded": "#ff4444",
            "partially_refunded": "#ffd700",
        }
        colors = [fin_colors.get(s, "#8b9bb4") for s in fin_counts["Status"]]
        fig = go.Figure(go.Pie(
            labels=fin_counts["Status"],
            values=fin_counts["Count"],
            hole=0.5,
            marker=dict(colors=colors, line=dict(color="#1e2235", width=2)),
            textfont=dict(color="#e0e0e0", size=11),
        ))
        fig.update_layout(
            paper_bgcolor="#1e2235", plot_bgcolor="#1e2235",
            font=dict(color="#e0e0e0"),
            height=300, margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0")),
        )
        st.plotly_chart(fig, use_container_width=True, key="sf1_fin_status")

    with col4:
        st.markdown("### Fulfillment Status")
        ful_counts = df["Fulfillment Status"].value_counts().reset_index()
        ful_counts.columns = ["Status", "Count"]
        ful_colors = {
            "fulfilled": "#00ff88",
            "unfulfilled": "#ff4444",
            "partial": "#ffd700",
        }
        colors = [ful_colors.get(s, "#8b9bb4") for s in ful_counts["Status"]]
        fig = go.Figure(go.Pie(
            labels=ful_counts["Status"],
            values=ful_counts["Count"],
            hole=0.5,
            marker=dict(colors=colors, line=dict(color="#1e2235", width=2)),
            textfont=dict(color="#e0e0e0", size=11),
        ))
        fig.update_layout(
            paper_bgcolor="#1e2235", plot_bgcolor="#1e2235",
            font=dict(color="#e0e0e0"),
            height=300, margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0")),
        )
        st.plotly_chart(fig, use_container_width=True, key="sf1_ful_status")

    # ── Quick Insight ──────────────────────────────────────────────────────────
    best_month = monthly.loc[monthly["gmv"].idxmax(), "month_label"]
    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>GMV gross: <b style="color:#00d4ff">{fmt_vnd(gmv)}</b> | Net (excl. refunds): <b style="color:#00ff88">{fmt_vnd(net_revenue)}</b></li>
            <li>AOV trung bình: <b style="color:#00d4ff">{fmt_vnd(aov)}</b> | {total_orders} orders</li>
            <li>Refund rate: <b style="color:{"#ff4444" if refund_rate > 10 else "#ffd700" if refund_rate > 5 else "#00ff88"}">{refund_rate:.1f}%</b>
                ({refund_count} orders) — {"cần kiểm tra" if refund_rate > 10 else "ổn"}</li>
            <li>Fulfillment rate: <b style="color:{"#00ff88" if fulfillment_rate >= 90 else "#ffd700"}">{fulfillment_rate:.1f}%</b></li>
            <li>Tháng GMV cao nhất: <b style="color:#00ff88">{best_month}</b></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
