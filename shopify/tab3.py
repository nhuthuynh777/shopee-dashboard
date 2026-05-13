import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import fmt_vnd, fmt_num, _ly, _hbar, styled_table
from shopify.data import load_csv

_SAMPLE_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_shopify_customers.csv")

_REFUND = {"refunded", "partially_refunded"}


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df["Financial Status"] = df["Financial Status"].str.lower().str.strip()
    df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)
    df["Created at"] = pd.to_datetime(df["Created at"])
    if "Is New Customer" in df.columns:
        df["Is New Customer"] = df["Is New Customer"].astype(str).str.lower().isin(
            ["true", "1", "yes"]
        )
    else:
        df["Is New Customer"] = True
    df["Hour"]        = df["Created at"].dt.hour
    df["month_label"] = df["Created at"].dt.strftime("%b %Y")
    return df


def render(uploaded_file=None):
    st.markdown("## 🌍 Customer & Geography")

    df_raw, source = load_csv(uploaded_file, _SAMPLE_CSV, parse_dates=["Created at"])
    if df_raw.empty:
        st.warning("Chưa có data. Upload file Customers (.csv) ở sidebar hoặc thêm sample data.")
        return
    df_all = _clean(df_raw.copy())
    df = df_all[~df_all["Financial Status"].isin(_REFUND)].copy()

    n_orders      = len(df_all)
    n_customers   = df_all["Email"].nunique()
    repeat_orders = (~df_all["Is New Customer"]).sum()
    repeat_rate   = repeat_orders / n_orders * 100 if n_orders else 0

    st.markdown(
        f'<div class="info-banner">'
        f'👥 {n_customers} khách hàng · {n_orders} orders · '
        f'Repeat rate: <b>{repeat_rate:.1f}%</b> · {source}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Section 1: Geography ──────────────────────────────────────────────────
    st.markdown("### Orders & Revenue by Province")

    prov = (
        df.groupby("Province", sort=False)
        .agg(orders=("Order Name", "count"), revenue=("Total", "sum"))
        .reset_index()
    )
    prov_all = (
        df_all.groupby("Province", sort=False)["Order Name"]
        .count().reset_index().rename(columns={"Order Name": "orders_gross"})
    )
    prov = prov.merge(prov_all, on="Province", how="left")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Orders by Province")
        ps = prov.sort_values("orders", ascending=True)
        fig = _hbar(
            y=ps["Province"], x=ps["orders"],
            colors="#00d4ff",
            texts=[fmt_num(v) for v in ps["orders"]],
            xaxis_title="Orders",
        )
        st.plotly_chart(fig, use_container_width=True, key="sf3_prov_orders")

    with col2:
        st.markdown("#### Revenue by Province (VNĐ)")
        ps2 = prov.sort_values("revenue", ascending=True)
        fig = _hbar(
            y=ps2["Province"], x=ps2["revenue"],
            colors="#00ff88",
            texts=[fmt_vnd(v) for v in ps2["revenue"]],
            xaxis_title="Revenue (VNĐ)",
        )
        st.plotly_chart(fig, use_container_width=True, key="sf3_prov_revenue")

    # Province table
    prov_tbl = prov.sort_values("revenue", ascending=False).copy()
    prov_tbl["aov"] = prov_tbl["revenue"] / prov_tbl["orders"]
    prov_tbl["pct"] = prov_tbl["revenue"] / prov_tbl["revenue"].sum() * 100
    disp = prov_tbl[["Province", "orders", "revenue", "aov", "pct"]].copy()
    disp.columns = ["Province", "Orders", "Revenue (VNĐ)", "AOV", "% Revenue"]
    disp["Revenue (VNĐ)"] = disp["Revenue (VNĐ)"].apply(fmt_vnd)
    disp["AOV"]           = disp["AOV"].apply(fmt_vnd)
    disp["% Revenue"]     = disp["% Revenue"].apply(lambda x: f"{x:.1f}%")
    st.markdown(styled_table(disp), unsafe_allow_html=True)

    st.markdown("---")

    # ── Section 2: New vs Repeat ───────────────────────────────────────────────
    st.markdown("### New vs Repeat Buyers")

    new_count    = df_all["Is New Customer"].sum()
    repeat_count = (~df_all["Is New Customer"]).sum()
    new_rev      = df[df["Is New Customer"]]["Total"].sum()
    repeat_rev   = df[~df["Is New Customer"]]["Total"].sum()

    col3, col4 = st.columns(2)

    with col3:
        # Donut — order count
        fig = go.Figure(go.Pie(
            labels=["New Buyers", "Repeat Buyers"],
            values=[new_count, repeat_count],
            hole=0.55,
            marker=dict(colors=["#00d4ff", "#00ff88"],
                        line=dict(color="#1e2235", width=2)),
            textfont=dict(color="#e0e0e0", size=12),
        ))
        fig.update_layout(
            paper_bgcolor="#1e2235", font=dict(color="#e0e0e0"),
            height=300, margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0")),
            title=dict(text="Order Count", font=dict(color="#e0e0e0", size=13)),
        )
        st.plotly_chart(fig, use_container_width=True, key="sf3_new_repeat_count")

    with col4:
        # Donut — revenue
        fig = go.Figure(go.Pie(
            labels=["New Buyers", "Repeat Buyers"],
            values=[new_rev, repeat_rev],
            hole=0.55,
            marker=dict(colors=["#00d4ff", "#00ff88"],
                        line=dict(color="#1e2235", width=2)),
            textfont=dict(color="#e0e0e0", size=12),
        ))
        fig.update_layout(
            paper_bgcolor="#1e2235", font=dict(color="#e0e0e0"),
            height=300, margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0")),
            title=dict(text="Revenue (VNĐ)", font=dict(color="#e0e0e0", size=13)),
        )
        st.plotly_chart(fig, use_container_width=True, key="sf3_new_repeat_rev")

    # New vs Repeat metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("New Buyers",    fmt_num(new_count),    f"{new_count/n_orders*100:.0f}% of orders")
    m2.metric("Repeat Buyers", fmt_num(repeat_count), f"{repeat_count/n_orders*100:.0f}% of orders")
    m3.metric("New Revenue",   fmt_vnd(new_rev))
    m4.metric("Repeat Revenue",fmt_vnd(repeat_rev))

    st.markdown("---")

    # ── Section 3: Peak Hours ─────────────────────────────────────────────────
    st.markdown("### Peak Hours — Orders per Hour")

    hour_counts = (
        df_all.groupby("Hour")["Order Name"].count()
        .reindex(range(24), fill_value=0)
        .reset_index()
    )
    hour_counts.columns = ["Hour", "Orders"]
    peak_hour = int(hour_counts.loc[hour_counts["Orders"].idxmax(), "Hour"])

    bar_colors = [
        "#ff6b35" if h in (12, 13, 20, 21, 22) else "#00d4ff"
        for h in hour_counts["Hour"]
    ]
    fig = go.Figure(go.Bar(
        x=[f"{h:02d}:00" for h in hour_counts["Hour"]],
        y=hour_counts["Orders"],
        marker_color=bar_colors,
        text=hour_counts["Orders"],
        textposition="outside",
        textfont=dict(color="#e0e0e0", size=9),
    ))
    fig.update_layout(**_ly(xaxis_title="Hour", yaxis_title="Orders", height=320))
    st.plotly_chart(fig, use_container_width=True, key="sf3_peak_hours")

    st.markdown("---")

    # ── Section 4: Top Customers ──────────────────────────────────────────────
    st.markdown("### Top 15 Customers by Revenue")

    top_cust = (
        df.groupby(["Email", "Customer Name", "Province"], sort=False)
        .agg(
            orders=("Order Name", "count"),
            revenue=("Total", "sum"),
            avg_order=("Total", "mean"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(15)
    )

    col5, col6 = st.columns([3, 2])

    with col5:
        tbl = top_cust[["Customer Name", "Province", "orders", "revenue", "avg_order"]].copy()
        tbl.columns = ["Customer", "Province", "Orders", "Total Revenue", "Avg Order"]
        tbl["Total Revenue"] = tbl["Total Revenue"].apply(fmt_vnd)
        tbl["Avg Order"]     = tbl["Avg Order"].apply(fmt_vnd)
        st.markdown(styled_table(tbl), unsafe_allow_html=True)

    with col6:
        st.markdown("#### Revenue Distribution")
        tc = top_cust.sort_values("revenue", ascending=True).tail(10)
        fig = _hbar(
            y=tc["Customer Name"],
            x=tc["revenue"],
            colors="#ffd700",
            texts=[fmt_vnd(v) for v in tc["revenue"]],
            xaxis_title="Revenue (VNĐ)",
        )
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True, key="sf3_top_cust")

    # ── Quick Insight ─────────────────────────────────────────────────────────
    top_prov     = prov.loc[prov["revenue"].idxmax(), "Province"]
    top_prov_rev = prov["revenue"].max()
    top_cust_name = top_cust.iloc[0]["Customer Name"]
    top_cust_rev  = top_cust.iloc[0]["revenue"]

    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>Tỉnh/TP doanh thu cao nhất: <b style="color:#00d4ff">{top_prov}</b>
                — {fmt_vnd(top_prov_rev)}</li>
            <li>Repeat buyer rate: <b style="color:{"#00ff88" if repeat_rate >= 40 else "#ffd700"}">{repeat_rate:.1f}%</b>
                ({repeat_count} orders từ khách quay lại)</li>
            <li>Giờ cao điểm: <b style="color:#ff6b35">{peak_hour:02d}:00</b>
                ({int(hour_counts.loc[hour_counts["Hour"]==peak_hour,"Orders"].iloc[0])} orders)</li>
            <li>Khách hàng VIP: <b style="color:#ffd700">{top_cust_name}</b>
                — {fmt_vnd(top_cust_rev)}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
