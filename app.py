import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Shopee Analytics Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── THEME / CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Dark background */
[data-testid="stAppViewContainer"] { background-color: #0e1117; }
[data-testid="stSidebar"] { background-color: #1a1d27; border-right: 1px solid #2d3149; }
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }

/* Main text */
h1, h2, h3, h4, p, li, label { color: #e0e0e0 !important; }

/* Metric cards */
[data-testid="metric-container"] {
    background-color: #1e2235;
    border: 1px solid #2d3149;
    border-radius: 8px;
    padding: 16px !important;
}
[data-testid="stMetricValue"] { color: #00d4ff !important; font-size: 28px !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #8b9bb4 !important; font-size: 13px !important; }
[data-testid="stMetricDelta"] { font-size: 13px !important; }

/* Tabs */
[data-testid="stTabs"] button {
    background-color: #1e2235 !important;
    color: #8b9bb4 !important;
    border-radius: 6px 6px 0 0 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    background-color: #00d4ff !important;
    color: #0e1117 !important;
    font-weight: 700 !important;
}

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid #2d3149; border-radius: 8px; }

/* Info box */
.info-banner {
    background-color: #1a2744;
    border-left: 4px solid #00d4ff;
    padding: 10px 16px;
    border-radius: 0 6px 6px 0;
    margin-bottom: 16px;
    font-size: 13px;
    color: #b0c4de !important;
}

/* KPI card custom */
.kpi-card {
    background-color: #1e2235;
    border: 1px solid #2d3149;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.kpi-label { color: #8b9bb4; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-value { color: #00d4ff; font-size: 26px; font-weight: 700; margin: 4px 0; }
.kpi-sub { color: #6b7a99; font-size: 12px; }

/* Issue cards */
.issue-card {
    background-color: #1e2235;
    border: 1px solid #2d3149;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.issue-title { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.issue-detail { color: #8b9bb4; font-size: 13px; }
.issue-reason { color: #6b7a99; font-size: 12px; font-style: italic; margin-top: 4px; }

/* Quick insight box */
.quick-insight {
    background-color: #1a2235;
    border: 1px solid #2d4a6b;
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 16px;
}
.quick-insight-title { color: #00d4ff; font-size: 13px; font-weight: 700; margin-bottom: 8px; }

/* Section header */
.section-header {
    font-size: 20px;
    font-weight: 700;
    color: #e0e0e0;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #2d3149;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background-color: #1e2235;
    border: 1px dashed #3d4a6b;
    border-radius: 8px;
    padding: 8px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #1e2235; }
::-webkit-scrollbar-thumb { background: #3d4a6b; border-radius: 3px; }

/* Checkbox */
.stCheckbox label { color: #e0e0e0 !important; }

/* selectbox */
[data-testid="stSelectbox"] select { background-color: #1e2235; color: #e0e0e0; }
</style>
""", unsafe_allow_html=True)

THB_TO_VND = 830

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def fmt_vnd(val):
    if val >= 1_000_000_000:
        return f"{val/1_000_000_000:.1f}B ₫"
    elif val >= 1_000_000:
        return f"{val/1_000_000:.1f}M ₫"
    elif val >= 1_000:
        return f"{val/1_000:.1f}K ₫"
    return f"{val:,.0f} ₫"

def fmt_num(val):
    if val >= 1_000_000:
        return f"{val/1_000_000:.1f}M"
    elif val >= 1_000:
        return f"{val/1_000:.1f}K"
    return f"{val:,.0f}"

# ─── PLOTLY CHART HELPERS ─────────────────────────────────────────────────────
CHART_H = 350

def _ly(**kw):
    """Base dark layout for all plotly bar/scatter charts."""
    base = dict(
        paper_bgcolor="#1e2235",
        plot_bgcolor="#1e2235",
        font=dict(color="#c0c8d8", size=11),
        height=CHART_H,
        margin=dict(l=10, r=120, t=30, b=40),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="#2d3149",
            borderwidth=1,
            font=dict(color="#e0e0e0"),
        ),
        xaxis=dict(
            gridcolor="#2d3149",
            linecolor="#2d3149",
            zerolinecolor="#2d3149",
            tickfont=dict(color="#c0c8d8"),
        ),
        yaxis=dict(
            gridcolor="#2d3149",
            linecolor="#2d3149",
            tickfont=dict(color="#c0c8d8"),
        ),
    )
    base.update(kw)
    return base

def _ly_pie(**kw):
    """Dark layout for pie/donut charts."""
    base = dict(
        paper_bgcolor="#1e2235",
        plot_bgcolor="#1e2235",
        font=dict(color="#e0e0e0", size=10),
        height=CHART_H,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0")),
        showlegend=True,
    )
    base.update(kw)
    return base

def _hbar(y, x, colors, texts, xaxis_title="", vlines=None):
    """Horizontal bar chart with outside text labels."""
    if isinstance(colors, str):
        colors = [colors] * len(x)
    mx = max(x) if len(x) > 0 else 1
    fig = go.Figure(go.Bar(
        x=list(x), y=list(y),
        orientation="h",
        marker_color=colors,
        text=texts,
        textposition="outside",
        textfont=dict(color="#e0e0e0", size=9),
        cliponaxis=False,
        hovertemplate="%{y}<br>" + xaxis_title + ": %{text}<extra></extra>",
    ))
    fig.update_layout(**_ly(xaxis_title=xaxis_title))
    fig.update_xaxes(range=[0, mx * 1.40])
    return fig

def styled_table(df):
    """Render a DataFrame as a dark-themed HTML table."""
    header = "".join(
        f'<th style="background:#1a2744;color:#00d4ff;padding:10px 16px;'
        f'text-align:left;font-size:12px;font-weight:700;'
        f'border-bottom:2px solid #2d4a6b;white-space:nowrap;">{col}</th>'
        for col in df.columns
    )
    body = ""
    for i, (_, row) in enumerate(df.iterrows()):
        bg = "#1e2235" if i % 2 == 0 else "#252a3d"
        cells = "".join(
            f'<td style="padding:9px 16px;font-size:13px;color:#e0e0e0;'
            f'border-bottom:1px solid #2d3149;">{val}</td>'
            for val in row
        )
        body += f'<tr style="background:{bg};">{cells}</tr>'
    return (
        '<div style="overflow-x:auto;border-radius:8px;border:1px solid #2d3149;margin-bottom:16px;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr>{header}</tr></thead>'
        f'<tbody>{body}</tbody>'
        '</table></div>'
    )


ROAS_TIERS = [
    ("🔴 Losing", "#ff4444", 0, 1.0),
    ("🟡 Below avg", "#ffd700", 1.0, 3.0),
    ("🟢 Good", "#00ff88", 3.0, 5.0),
    ("⭐ Excellent", "#00d4ff", 5.0, 999),
]

def get_roas_tier(roas):
    for label, color, lo, hi in ROAS_TIERS:
        if lo <= roas < hi:
            return label, color
    return "⭐ Excellent", "#00d4ff"

def load_files(uploaded_files):
    all_campaigns = []
    all_keywords = []
    for f in uploaded_files:
        try:
            xl = pd.ExcelFile(f)
            if "All Campaigns" in xl.sheet_names:
                df = pd.read_excel(f, sheet_name="All Campaigns")
                df["_source_file"] = f.name
                all_campaigns.append(df)
            if "Shop Ad - Keywords" in xl.sheet_names:
                dfk = pd.read_excel(f, sheet_name="Shop Ad - Keywords")
                dfk["_source_file"] = f.name
                all_keywords.append(dfk)
        except Exception as e:
            st.sidebar.warning(f"Lỗi đọc file {f.name}: {e}")
    df_camp = pd.concat(all_campaigns, ignore_index=True) if all_campaigns else pd.DataFrame()
    df_kw = pd.concat(all_keywords, ignore_index=True) if all_keywords else pd.DataFrame()
    return df_camp, df_kw

def clean_campaigns(df):
    if df.empty:
        return df
    num_cols = ["Impression", "Clicks", "Expense", "GMV", "ROAS", "ACOS",
                "Items Sold", "Conversions", "Direct GMV", "Direct ROAS",
                "Direct ACOS", "Direct Items Sold"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in ["Expense", "GMV", "Direct GMV"]:
        if col in df.columns:
            df[f"{col}_VND"] = df[col] * THB_TO_VND
    if "CTR" in df.columns:
        df["CTR_pct"] = df["CTR"].astype(str).str.replace("%", "").str.strip()
        df["CTR_pct"] = pd.to_numeric(df["CTR_pct"], errors="coerce").fillna(0)
    if "ACOS" in df.columns:
        df["ACOS_pct"] = df["ACOS"].astype(str).str.replace("%", "").str.strip()
        df["ACOS_pct"] = pd.to_numeric(df["ACOS_pct"], errors="coerce").fillna(0)
    if "Campaign" in df.columns:
        df["Ad_Type"] = df["Campaign"].apply(
            lambda x: "Shop Ad" if "Shop Ad" in str(x) else "Product Ad"
        )
    if "ROAS" in df.columns:
        df["ROAS_Tier"] = df["ROAS"].apply(lambda x: get_roas_tier(x)[0])
        df["ROAS_Color"] = df["ROAS"].apply(lambda x: get_roas_tier(x)[1])
    return df

def get_campaign_summary(df):
    if df.empty:
        return df
    agg = df.groupby("Campaign", as_index=False).agg(
        Ad_Type=("Ad_Type", "first"),
        Ad_Status=("Ad Status", "first"),
        Impressions=("Impression", "sum"),
        Clicks=("Clicks", "sum"),
        Expense_VND=("Expense_VND", "sum"),
        GMV_VND=("GMV_VND", "sum"),
        Items_Sold=("Items Sold", "sum"),
    )
    agg["ROAS"] = agg.apply(
        lambda r: r["GMV_VND"] / r["Expense_VND"] if r["Expense_VND"] > 0 else 0, axis=1
    )
    agg["CTR"] = agg.apply(
        lambda r: r["Clicks"] / r["Impressions"] * 100 if r["Impressions"] > 0 else 0, axis=1
    )
    agg["ACOS"] = agg.apply(
        lambda r: r["Expense_VND"] / r["GMV_VND"] * 100 if r["GMV_VND"] > 0 else 0, axis=1
    )
    agg["ROAS_Tier"] = agg["ROAS"].apply(lambda x: get_roas_tier(x)[0])
    agg["ROAS_Color"] = agg["ROAS"].apply(lambda x: get_roas_tier(x)[1])
    return agg


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛍️ VSTu Analytics")
    st.markdown("Digital Marketing Dashboard")
    st.markdown("---")
    st.markdown("### 📂 Upload Raw Data")
    uploaded_files = st.file_uploader(
        "Shopee Ads Export (.xlsx)",
        type=["xlsx"],
        accept_multiple_files=True,
        help="Upload file export từ Shopee Ads. Có thể upload nhiều file cùng lúc (nhiều tháng)."
    )
    st.markdown("---")
    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file đã tải:**")
        for f in uploaded_files:
            st.markdown(f"• {f.name}")
    st.markdown("---")
    st.markdown(f"**💱 Tỷ giá:** 1 THB = {THB_TO_VND:,} VNĐ")
    st.caption("Nguồn: Google")

# ─── MAIN CONTENT ─────────────────────────────────────────────────────────────
st.markdown("# 🛍️ Report — Shopee Analytics")
st.markdown("**VSTu Digital Marketing Analytics** | Shopee Ads Performance")

if not uploaded_files:
    st.markdown("""
    <div style='background:#1e2235;border:1px solid #2d3149;border-radius:12px;padding:48px;text-align:center;margin-top:32px;'>
        <div style='font-size:48px;margin-bottom:16px;'>📂</div>
        <div style='font-size:20px;color:#e0e0e0;margin-bottom:8px;'>Chưa có data</div>
        <div style='color:#8b9bb4;font-size:14px;'>Upload file Shopee Ads export (.xlsx) ở sidebar bên trái để bắt đầu</div>
        <div style='color:#6b7a99;font-size:13px;margin-top:12px;'>Có thể upload nhiều file cùng lúc để xem dữ liệu tổng hợp nhiều tháng</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

with st.spinner("Đang đọc data..."):
    df_raw, df_kw_raw = load_files(uploaded_files)
    df = clean_campaigns(df_raw.copy())
    df_camp = get_campaign_summary(df)

st.markdown(
    f'<div class="info-banner">💱 Tỷ giá quy đổi: 1 THB = {THB_TO_VND:,} VNĐ &nbsp;|&nbsp; Shopee Ads Expense/GMV: THB → VNĐ &nbsp;|&nbsp; {len(uploaded_files)} file đã tải</div>',
    unsafe_allow_html=True
)

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏥 Business Health",
    "🏷️ Brand & Product",
    "📊 Onsite Ads Performance",
    "🔍 Campaign Setup Audit",
    "📌 Summary Insight",
    "🚀 Action Plan",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BUSINESS HEALTH
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## 🏥 Business Health — Shopee Ads")

    total_spend = df["Expense_VND"].sum()
    total_gmv = df["GMV_VND"].sum()
    overall_roas = total_gmv / total_spend if total_spend > 0 else 0
    total_impressions = df["Impression"].sum()
    total_clicks = df["Clicks"].sum()
    avg_ctr = total_clicks / total_impressions * 100 if total_impressions > 0 else 0
    total_items = df["Items Sold"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Spend", fmt_vnd(total_spend))
    c2.metric("Total GMV", fmt_vnd(total_gmv))
    c3.metric("Overall ROAS", f"{overall_roas:.2f}x")
    c4.metric("Avg CTR", f"{avg_ctr:.2f}%", f"{fmt_num(total_clicks)} clicks")
    c5.metric("Impressions", fmt_num(total_impressions))

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### GMV by Campaign (VNĐ)")
        camp_gmv = df_camp[df_camp["GMV_VND"] > 0].sort_values("GMV_VND", ascending=True)
        if not camp_gmv.empty:
            fig = _hbar(
                y=camp_gmv["Campaign"],
                x=camp_gmv["GMV_VND"],
                colors="#00d4ff",
                texts=[fmt_vnd(v) for v in camp_gmv["GMV_VND"]],
                xaxis_title="GMV (VNĐ)",
            )
            st.plotly_chart(fig, use_container_width=True, key="t1_gmv_campaign")

    with col2:
        st.markdown("### ROAS by Campaign")
        camp_roas = df_camp[df_camp["ROAS"] > 0].sort_values("ROAS", ascending=True)
        if not camp_roas.empty:
            fig = _hbar(
                y=camp_roas["Campaign"],
                x=camp_roas["ROAS"],
                colors=camp_roas["ROAS_Color"].tolist(),
                texts=[f"{v:.2f}x" for v in camp_roas["ROAS"]],
                xaxis_title="ROAS",
            )
            fig.add_vline(x=3.0, line_dash="dash", line_color="#00ff88",
                          annotation_text="ROAS=3.0", annotation_font_color="#00ff88",
                          annotation_position="top right")
            fig.add_vline(x=1.0, line_dash="dash", line_color="#ff4444",
                          annotation_text="ROAS=1.0", annotation_font_color="#ff4444",
                          annotation_position="top right")
            st.plotly_chart(fig, use_container_width=True, key="t1_roas_campaign")

    # Spend vs GMV scatter
    st.markdown("### Spend vs GMV by Campaign")
    valid = df_camp[df_camp["Expense_VND"] > 0]
    if not valid.empty:
        tier_colors = {t[0]: t[1] for t in ROAS_TIERS}
        max_imp = valid["Impressions"].max() if valid["Impressions"].max() > 0 else 1
        fig = go.Figure()
        for tier, color in tier_colors.items():
            sub = valid[valid["ROAS_Tier"] == tier]
            if not sub.empty:
                sz = (sub["Impressions"] / max_imp * 35 + 8).clip(8, 40)
                fig.add_trace(go.Scatter(
                    x=sub["Expense_VND"], y=sub["GMV_VND"],
                    mode="markers",
                    name=tier,
                    marker=dict(size=sz.tolist(), color=color, opacity=0.85,
                                line=dict(color="#1e2235", width=0.5)),
                    text=sub["Campaign"].str[:30],
                    hovertemplate="<b>%{text}</b><br>Spend: %{x:,.0f} ₫<br>GMV: %{y:,.0f} ₫<extra></extra>",
                ))
        fig.update_layout(**_ly(xaxis_title="Spend (VNĐ)", yaxis_title="GMV (VNĐ)"))
        st.plotly_chart(fig, use_container_width=True, key="t1_spend_gmv_scatter")

    top_camp = df_camp.loc[df_camp["GMV_VND"].idxmax(), "Campaign"] if not df_camp.empty else "-"
    losing = df_camp[df_camp["ROAS"] < 1.0]
    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>ROAS tổng: <b style="color:#00d4ff">{overall_roas:.2f}x</b> | GMV tổng: <b style="color:#00d4ff">{fmt_vnd(total_gmv)}</b></li>
            <li>Campaign GMV cao nhất: <b style="color:#00ff88">{top_camp}</b></li>
            <li>Campaigns ROAS &lt; 1.0: <b style="color:#ff4444">{len(losing)} campaigns</b> — cần review hoặc pause</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BRAND & PRODUCT
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## 🏷️ Product Traffic — Impressions & CTR")

    prod_df = df[df["Ad / Product Name"] != df["Campaign"]].copy()
    prod_df = prod_df[prod_df["Impression"] > 0]

    if prod_df.empty:
        st.info("Không có dữ liệu product-level trong file đã upload.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Top 15 by Impressions")
            top_imp = prod_df.nlargest(15, "Impression").sort_values("Impression", ascending=True)
            fig = _hbar(
                y=top_imp["Ad / Product Name"].str[:50],
                x=top_imp["Impression"],
                colors="#00d4ff",
                texts=[fmt_num(v) for v in top_imp["Impression"]],
                xaxis_title="Impressions",
            )
            st.plotly_chart(fig, use_container_width=True, key="t2_top_impressions")

        with col2:
            st.markdown("#### CTR by Product (Top 15 by Impressions)")
            med_ctr = prod_df["CTR_pct"].median()
            top_imp2 = prod_df.nlargest(15, "Impression").sort_values("CTR_pct", ascending=True)
            colors_ctr = ["#ff4444" if v < med_ctr else "#00d4ff" for v in top_imp2["CTR_pct"]]
            fig = _hbar(
                y=top_imp2["Ad / Product Name"].str[:50],
                x=top_imp2["CTR_pct"],
                colors=colors_ctr,
                texts=[f"{v:.2f}%" for v in top_imp2["CTR_pct"]],
                xaxis_title="CTR (%)",
            )
            fig.add_vline(x=med_ctr, line_dash="dash", line_color="#ffd700",
                          annotation_text=f"Median {med_ctr:.2f}%", annotation_font_color="#ffd700",
                          annotation_position="top right")
            st.plotly_chart(fig, use_container_width=True, key="t2_ctr_product")

        # Opportunity table
        st.markdown("### 🎯 Cơ hội: Impression cao nhưng CTR thấp")
        st.caption("Sản phẩm có impressions > median nhưng CTR < median — cần cải thiện thumbnail/giá")
        med_imp = prod_df["Impression"].median()
        opps = prod_df[
            (prod_df["Impression"] > med_imp) &
            (prod_df["CTR_pct"] < med_ctr)
        ].sort_values("Impression", ascending=False)[
            ["Ad / Product Name", "Impression", "CTR_pct", "Clicks"]
        ].head(10)
        opps.columns = ["Product", "Impressions", "CTR (%)", "Clicks"]
        st.markdown(styled_table(opps), unsafe_allow_html=True)

        # Product performance — sales & revenue
        st.markdown("### 📦 Product Performance — Sales & Revenue")
        prod_rev = prod_df[prod_df["GMV_VND"] > 0].sort_values("GMV_VND", ascending=True).tail(15)
        fig = _hbar(
            y=prod_rev["Ad / Product Name"].str[:55],
            x=prod_rev["GMV_VND"],
            colors="#00ff88",
            texts=[fmt_vnd(v) for v in prod_rev["GMV_VND"]],
            xaxis_title="GMV (VNĐ)",
        )
        st.plotly_chart(fig, use_container_width=True, key="t2_product_sales")

        # Top 15 by units sold
        st.markdown("### 📦 Top 15 Products by Units Sold")
        top_units = prod_df[prod_df["Items Sold"] > 0].nlargest(15, "Items Sold").sort_values("Items Sold", ascending=True)
        fig = _hbar(
            y=top_units["Ad / Product Name"].str[:55],
            x=top_units["Items Sold"],
            colors="#ffd700",
            texts=[fmt_num(v) for v in top_units["Items Sold"]],
            xaxis_title="Units Sold",
        )
        st.plotly_chart(fig, use_container_width=True, key="t2_units_sold")

        # Full product table
        st.markdown("### 📋 Full Product Performance Table")
        tbl = prod_df[prod_df["GMV_VND"] > 0].sort_values("GMV_VND", ascending=False)[
            ["Ad / Product Name", "GMV_VND", "Items Sold", "Impression", "CTR_pct", "Expense_VND", "ROAS"]
        ].copy()
        tbl.columns = ["Product", "GMV (VNĐ)", "Units Sold", "Impressions", "CTR (%)", "Spend (VNĐ)", "ROAS"]
        tbl["GMV (VNĐ)"] = tbl["GMV (VNĐ)"].apply(fmt_vnd)
        tbl["Spend (VNĐ)"] = tbl["Spend (VNĐ)"].apply(fmt_vnd)
        tbl["ROAS"] = tbl["ROAS"].apply(lambda x: f"{x:.2f}x")
        tbl["CTR (%)"] = tbl["CTR (%)"].apply(lambda x: f"{x:.2f}%")
        st.markdown(styled_table(tbl), unsafe_allow_html=True)

        top_prod = prod_df.loc[prod_df["GMV_VND"].idxmax(), "Ad / Product Name"] if not prod_df.empty else "-"
        low_ctr_prods = len(prod_df[(prod_df["Impression"] > med_imp) & (prod_df["CTR_pct"] < med_ctr)])
        st.markdown(f"""
        <div class="quick-insight">
            <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
            <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
                <li>Sản phẩm GMV cao nhất: <b style="color:#00d4ff">{top_prod[:60]}</b></li>
                <li><b style="color:#ffd700">{low_ctr_prods} sản phẩm</b> có impressions cao nhưng CTR thấp → cần cải thiện thumbnail/giá</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ONSITE ADS PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## 📊 Onsite Ads Performance")

    total_spend = df["Expense_VND"].sum()
    total_gmv = df["GMV_VND"].sum()
    overall_roas = total_gmv / total_spend if total_spend > 0 else 0
    total_imp = df["Impression"].sum()
    total_clicks_all = df["Clicks"].sum()
    avg_ctr_all = total_clicks_all / total_imp * 100 if total_imp > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Spend", fmt_vnd(total_spend))
    c2.metric("Total GMV", fmt_vnd(total_gmv))
    c3.metric("Overall ROAS", f"{overall_roas:.2f}x")
    c4.metric("Avg CTR", f"{avg_ctr_all:.2f}%", f"{fmt_num(total_clicks_all)} clicks")
    c5.metric("Impressions", fmt_num(total_imp))

    st.markdown("---")

    # Campaign performance table
    st.markdown("### Campaign Performance (All CPC)")
    tbl2 = df_camp[["Campaign", "Ad_Type", "Ad_Status", "Expense_VND", "GMV_VND", "ROAS", "CTR", "ACOS", "Items_Sold"]].copy()
    tbl2 = tbl2.rename(columns={
        "Ad_Type": "Ad Type", "Ad_Status": "Status",
        "Expense_VND": "Spend (VNĐ)", "GMV_VND": "GMV (VNĐ)",
        "CTR": "CTR (%)", "ACOS": "ACOS (%)", "Items_Sold": "Items Sold"
    })
    tbl2["Spend (VNĐ)"] = tbl2["Spend (VNĐ)"].apply(fmt_vnd)
    tbl2["GMV (VNĐ)"] = tbl2["GMV (VNĐ)"].apply(fmt_vnd)
    tbl2["ROAS"] = tbl2["ROAS"].apply(lambda x: f"{x:.2f}x")
    tbl2["CTR (%)"] = tbl2["CTR (%)"].apply(lambda x: f"{x:.2f}%")
    tbl2["ACOS (%)"] = tbl2["ACOS (%)"].apply(lambda x: f"{x:.1f}%")
    st.markdown(styled_table(tbl2), unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### GMV by Campaign (VNĐ)")
        camp_sorted = df_camp[df_camp["GMV_VND"] > 0].sort_values("GMV_VND", ascending=True)
        if not camp_sorted.empty:
            fig = _hbar(
                y=camp_sorted["Campaign"],
                x=camp_sorted["GMV_VND"],
                colors="#00d4ff",
                texts=[fmt_vnd(v) for v in camp_sorted["GMV_VND"]],
                xaxis_title="GMV (VNĐ)",
            )
            st.plotly_chart(fig, use_container_width=True, key="t3_gmv_campaign")

    with col2:
        st.markdown("### ROAS by Campaign")
        roas_sorted = df_camp[df_camp["ROAS"] > 0].sort_values("ROAS", ascending=True)
        if not roas_sorted.empty:
            fig = _hbar(
                y=roas_sorted["Campaign"],
                x=roas_sorted["ROAS"],
                colors=roas_sorted["ROAS_Color"].tolist(),
                texts=[f"{v:.2f}x" for v in roas_sorted["ROAS"]],
                xaxis_title="ROAS",
            )
            fig.add_vline(x=3.0, line_dash="dash", line_color="#00ff88",
                          annotation_text="ROAS=3.0", annotation_font_color="#00ff88",
                          annotation_position="top right")
            fig.add_vline(x=1.0, line_dash="dash", line_color="#ff4444",
                          annotation_text="ROAS=1.0", annotation_font_color="#ff4444",
                          annotation_position="top right")
            st.plotly_chart(fig, use_container_width=True, key="t3_roas_campaign")

    # CTR vs ROAS bubble
    st.markdown("### CTR vs ROAS — bubble size = Spend")
    bubble_df = df_camp[df_camp["Expense_VND"] > 0]
    if not bubble_df.empty:
        tier_colors = {t[0]: t[1] for t in ROAS_TIERS}
        max_spend = bubble_df["Expense_VND"].max() if bubble_df["Expense_VND"].max() > 0 else 1
        fig = go.Figure()
        for tier, color in tier_colors.items():
            sub = bubble_df[bubble_df["ROAS_Tier"] == tier]
            if not sub.empty:
                sz = (sub["Expense_VND"] / max_spend * 35 + 8).clip(8, 40)
                fig.add_trace(go.Scatter(
                    x=sub["CTR"], y=sub["ROAS"],
                    mode="markers",
                    name=tier,
                    marker=dict(size=sz.tolist(), color=color, opacity=0.85,
                                line=dict(color="#1e2235", width=0.5)),
                    text=sub["Campaign"].str[:30],
                    hovertemplate="<b>%{text}</b><br>CTR: %{x:.2f}%<br>ROAS: %{y:.2f}x<extra></extra>",
                ))
        fig.add_hline(y=3.0, line_dash="dash", line_color="#00ff88",
                      annotation_text="ROAS=3.0", annotation_font_color="#00ff88")
        fig.add_hline(y=1.0, line_dash="dash", line_color="#ff4444",
                      annotation_text="ROAS=1.0", annotation_font_color="#ff4444")
        fig.update_layout(**_ly(xaxis_title="CTR (%)", yaxis_title="ROAS"))
        st.plotly_chart(fig, use_container_width=True, key="t3_ctr_roas_bubble")

    top_roas_camp = df_camp.loc[df_camp["ROAS"].idxmax()] if not df_camp.empty else None
    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>ROAS tổng: <b style="color:#00d4ff">{overall_roas:.2f}x</b> | Total Spend: <b>{fmt_vnd(total_spend)}</b></li>
            {"<li>Campaign ROAS cao nhất: <b style='color:#00ff88'>" + top_roas_camp['Campaign'] + f"</b> — ROAS {top_roas_camp['ROAS']:.2f}x</li>" if top_roas_camp is not None else ""}
            <li>Campaigns đang lỗ (ROAS &lt; 1.0): <b style="color:#ff4444">{len(df_camp[df_camp['ROAS'] < 1.0])}</b></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CAMPAIGN SETUP AUDIT
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## 🔍 Campaign Setup Audit")

    # 1. ROAS Classification
    st.markdown("### 1. ROAS Classification")
    tier_table = pd.DataFrame([
        {"Tier": "🔴 Losing", "ROAS": "< 1.0x", "Đánh giá": "Chi nhiều hơn doanh thu"},
        {"Tier": "🟡 Below avg", "ROAS": "1.0 – 3.0x", "Đánh giá": "Cần optimize"},
        {"Tier": "🟢 Good", "ROAS": "3.0 – 5.0x", "Đánh giá": "Hiệu quả tốt"},
        {"Tier": "⭐ Excellent", "ROAS": "> 5.0x", "Đánh giá": "Scale aggressively"},
    ])
    st.markdown(styled_table(tier_table), unsafe_allow_html=True)

    roas_tbl = df_camp[["Campaign", "Ad_Status", "Expense_VND", "ROAS", "ROAS_Tier", "ACOS", "CTR"]].copy()
    roas_tbl = roas_tbl.rename(columns={"Ad_Status": "Status", "Expense_VND": "Spend (VNĐ)",
                                         "ROAS_Tier": "ROAS Tier"})
    roas_tbl["Spend (VNĐ)"] = roas_tbl["Spend (VNĐ)"].apply(fmt_vnd)
    roas_tbl["ROAS"] = roas_tbl["ROAS"].apply(lambda x: f"{x:.2f}x")
    roas_tbl["CTR"] = roas_tbl["CTR"].apply(lambda x: f"{x:.2f}%")
    roas_tbl["ACOS"] = roas_tbl["ACOS"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(roas_tbl, hide_index=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        # ROAS tier donut
        tier_counts = df_camp["ROAS_Tier"].value_counts().reset_index()
        tier_counts.columns = ["Tier", "Count"]
        tier_color_map = {t[0]: t[1] for t in ROAS_TIERS}
        donut_colors = [tier_color_map.get(t, "#888") for t in tier_counts["Tier"]]
        fig = go.Figure(go.Pie(
            values=tier_counts["Count"],
            labels=tier_counts["Tier"],
            hole=0.5,
            marker=dict(colors=donut_colors, line=dict(color="#1e2235", width=2)),
            textfont=dict(color="#e0e0e0", size=10),
        ))
        fig.update_layout(**_ly_pie(title=dict(text="# Campaigns by ROAS Tier", font=dict(color="#e0e0e0", size=12))))
        st.plotly_chart(fig, use_container_width=True, key="t4_roas_tier_donut")

    with col2:
        losing = df_camp[df_camp["ROAS"] < 1.0]
        if not losing.empty:
            st.markdown("**❌ Campaigns đang lỗ (cần Pause/Review):**")
            for _, r in losing.iterrows():
                st.markdown(f"""
                <div class="issue-card" style="border-left:3px solid #ff4444;">
                    <div class="issue-title" style="color:#ff4444;">• {r['Campaign']}</div>
                    <div class="issue-detail">Status: {r['Ad_Status']} | Spend: {fmt_vnd(r['Expense_VND'])} | ROAS: {r['ROAS']:.2f}x</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="issue-card" style="border-left:3px solid #00ff88;background:#0d2e1a;">
                <div style="color:#00ff88;font-weight:700;">✅ Tất cả campaigns đang có ROAS > 1.0x</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 2. ACOS Analysis
    st.markdown("### 2. ACOS Analysis (Advertising Cost of Sales)")
    st.caption("ACOS = Spend / GMV × 100% — thấp hơn là tốt hơn")
    acos_sorted = df_camp[df_camp["ACOS"] > 0].sort_values("ACOS", ascending=True)
    if not acos_sorted.empty:
        colors_acos = ["#00ff88" if v < 30 else "#ffd700" if v < 50 else "#ff4444"
                       for v in acos_sorted["ACOS"]]
        fig = _hbar(
            y=acos_sorted["Campaign"],
            x=acos_sorted["ACOS"],
            colors=colors_acos,
            texts=[f"{v:.1f}%" for v in acos_sorted["ACOS"]],
            xaxis_title="ACOS (%)",
        )
        fig.add_vline(x=30, line_dash="dash", line_color="#ffd700",
                      annotation_text="30% threshold", annotation_font_color="#ffd700",
                      annotation_position="top right")
        st.plotly_chart(fig, use_container_width=True, key="t4_acos_analysis")

    st.markdown("---")

    # 3. Campaign Status Overview
    st.markdown("### 3. Campaign Status Overview")
    col1, col2 = st.columns(2)
    with col1:
        status_count = df_camp["Ad_Status"].value_counts().reset_index()
        status_count.columns = ["Status", "Count"]
        status_colors = ["#00d4ff", "#ffd700", "#ff8c00"][:len(status_count)]
        fig = go.Figure(go.Pie(
            values=status_count["Count"],
            labels=status_count["Status"],
            hole=0.5,
            marker=dict(colors=status_colors, line=dict(color="#1e2235", width=2)),
            textfont=dict(color="#e0e0e0", size=10),
        ))
        fig.update_layout(**_ly_pie(title=dict(text="# Campaigns by Status", font=dict(color="#e0e0e0", size=12))))
        st.plotly_chart(fig, use_container_width=True, key="t4_status_pie")

    with col2:
        status_spend = df_camp.groupby("Ad_Status")["Expense_VND"].sum().reset_index()
        bar_colors_status = ["#00d4ff", "#ffd700", "#ff8c00"][:len(status_spend)]
        fig = _hbar(
            y=status_spend["Ad_Status"],
            x=status_spend["Expense_VND"],
            colors=bar_colors_status,
            texts=[fmt_vnd(v) for v in status_spend["Expense_VND"]],
            xaxis_title="Total Spend (VNĐ)",
        )
        fig.update_layout(title=dict(text="Spend by Status (VNĐ)", font=dict(color="#e0e0e0", size=12)))
        st.plotly_chart(fig, use_container_width=True, key="t4_status_spend_bar")

    st.markdown("---")

    # 4. Campaign Naming Convention
    st.markdown("### 4. Campaign Naming Convention")
    st.caption("Quy tắc khuyến nghị: `[Type]_[Product/Brand]_[Date]`")

    def check_naming(name):
        issues = []
        if not re.search(r'\d{4}', str(name)):
            issues.append("⚠️ Thiếu năm/tháng")
        keywords = ["GMV", "CPC", "Shop", "Clearance", "Product"]
        if not any(k.lower() in str(name).lower() for k in keywords):
            issues.append("⚠️ Không rõ objective/type")
        return "✅ OK" if not issues else " | ".join(issues)

    naming_df = df_camp[["Campaign", "Ad_Status"]].copy()
    naming_df["Naming Issues"] = naming_df["Campaign"].apply(check_naming)
    st.markdown(styled_table(naming_df), unsafe_allow_html=True)

    acos_high = df_camp[df_camp["ACOS"] > 30]
    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>Campaigns ROAS &lt; 1.0: <b style="color:#ff4444">{len(df_camp[df_camp['ROAS'] < 1.0])}</b> — review bid/target trước khi reactivate</li>
            <li>Campaigns ROAS &gt; 5.0: <b style="color:#00d4ff">{len(df_camp[df_camp['ROAS'] >= 5.0])}</b> — tăng budget 30-50% để capture thêm GMV</li>
            <li>Campaigns ACOS &gt; 30%: <b style="color:#ffd700">{len(acos_high)}</b> — chi phí ads cao, có thể ảnh hưởng margin thực tế</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SUMMARY INSIGHT
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("## 📌 Summary Insight — Shopee")
    st.caption("Phân tích tự động dựa trên data hiện có. Cập nhật mỗi lần load.")

    st.markdown("## 🔴 Vấn đề đang tồn tại")

    issues = []

    losing = df_camp[df_camp["ROAS"] < 1.0]
    if not losing.empty:
        issues.append({
            "severity": "🔴",
            "title": f"Lưu ý — {len(losing)} campaign(s) có ROAS < 1.0x — đang lỗ tiền quảng cáo",
            "detail": f"💸 Tổng spend đang lỗ: {fmt_vnd(losing['Expense_VND'].sum())} | Không có GMV hoặc ROAS âm",
            "reason": "💡 Nguyên nhân có thể: Targeting quá rộng, sản phẩm hết hàng, hoặc giá thầu quá cao",
            "color": "#ff4444",
        })

    shop_ads = df_camp[df_camp["Ad_Type"] == "Shop Ad"]
    if not shop_ads.empty and shop_ads["ROAS"].mean() < 2.0:
        issues.append({
            "severity": "🟡",
            "title": f"Cần chú ý — Shop Ads có ROAS trung bình {shop_ads['ROAS'].mean():.2f}x — kém hiệu quả so với Product Ads",
            "detail": f"💸 {len(shop_ads)} Shop Ad campaign(s) | Avg ROAS: {shop_ads['ROAS'].mean():.2f}x",
            "reason": "💡 Nguyên nhân có thể: Shop Ads targeting quá rộng, không đủ intent so với Product Ads",
            "color": "#ffd700",
        })

    acos_high = df_camp[df_camp["ACOS"] > 40]
    if not acos_high.empty:
        issues.append({
            "severity": "🟡",
            "title": f"Cần chú ý — {len(acos_high)} campaign(s) có ACOS > 40% — chi phí quảng cáo cao",
            "detail": f"💸 {', '.join(acos_high['Campaign'].tolist()[:3])}",
            "reason": "💡 Nguyên nhân có thể: Giá thầu cao, conversion rate thấp",
            "color": "#ffd700",
        })

    excellent = df_camp[df_camp["ROAS"] >= 5.0]
    if not excellent.empty:
        issues.append({
            "severity": "🟢",
            "title": f"Cơ hội — {len(excellent)} campaign(s) có ROAS ≥ 5.0x — đang under-invest",
            "detail": f"💰 {', '.join(excellent['Campaign'].tolist()[:3])} | ROAS xuất sắc nhưng budget chưa được tăng",
            "reason": "💡 Action: Tăng budget 30-50% để capture thêm GMV",
            "color": "#00ff88",
        })

    prod_df_check = df[df["Ad / Product Name"] != df["Campaign"]]
    low_ctr_prods = prod_df_check[(prod_df_check["Impression"] > prod_df_check["Impression"].median()) &
                                   (prod_df_check["CTR_pct"] < prod_df_check["CTR_pct"].median())]
    if not low_ctr_prods.empty:
        issues.append({
            "severity": "🟡",
            "title": f"Lưu ý — {len(low_ctr_prods)} sản phẩm có Impression cao nhưng CTR thấp",
            "detail": f"💸 Đang waste impression budget — cần cải thiện thumbnail hoặc giá",
            "reason": "💡 Action: Update thumbnail/tiêu đề, test giá, hoặc dùng voucher để kéo CTR",
            "color": "#ffd700",
        })

    if not issues:
        st.markdown("""
        <div class="issue-card" style="border-left:3px solid #00ff88;background:#0d2e1a;">
            <div style="color:#00ff88;font-weight:700;">✅ Không phát hiện vấn đề nghiêm trọng trong kỳ này</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for issue in issues:
            st.markdown(f"""
            <div class="issue-card" style="border-left:4px solid {issue['color']};">
                <div class="issue-title" style="color:{issue['color']};">{issue['severity']} {issue['title']}</div>
                <div class="issue-detail">{issue['detail']}</div>
                <div class="issue-reason">{issue['reason']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("## 📊 Data Quality Score — Kỳ này")

    checks = {
        "Shopee Ads: All Campaigns loaded": not df_camp.empty,
        "Shopee Ads: ROAS column present": "ROAS" in df.columns,
        "Shopee Ads: Product-level data": len(df[df["Ad / Product Name"] != df["Campaign"]]) > 0,
        "Shopee Ads: Keyword data": not df_kw_raw.empty,
        "Shopee Ads: CTR data available": "CTR_pct" in df.columns,
        "Shopee Ads: GMV data available": df["GMV_VND"].sum() > 0,
        "Shopee Insights: Daily GMV": False,
        "Shopee Insights: Traffic Overview": False,
        "Shopee Insights: Orders data": False,
        "Cross-channel: Shopify comparison": False,
    }

    score = sum(checks.values())
    total = len(checks)
    pct = score / total * 100
    color = "#00ff88" if pct >= 80 else "#ffd700" if pct >= 50 else "#ff4444"
    label = "Tốt" if pct >= 80 else "Trung bình" if pct >= 50 else "Thiếu nhiều"

    st.markdown(f"""
    <div style="background:#1e2235;border:1px solid #2d3149;border-radius:12px;padding:24px;text-align:center;margin-bottom:16px;">
        <div style="color:#8b9bb4;font-size:13px;margin-bottom:8px;">Data Completeness Score</div>
        <div style="color:{color};font-size:48px;font-weight:700;">{score}/{total}</div>
        <div style="color:{color};font-size:16px;">{pct:.0f}% — {label}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    items = list(checks.items())
    half = len(items) // 2
    for i, (check_name, passed) in enumerate(items):
        col = col1 if i < half else col2
        col.markdown(f"{'✅' if passed else '❌'} {check_name}")

    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>Data completeness: {score}/{total} ({pct:.0f}%)</li>
            <li>{len(issues)} vấn đề cần xử lý ({len([i for i in issues if '🔴' in i['severity']])} nghiêm trọng)</li>
            <li>Overall ROAS kỳ này: <b style="color:#00d4ff">{overall_roas:.2f}x</b></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — ACTION PLAN
# ═══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("## 🚀 Action Plan — Shopee Ads")
    st.markdown(f"**Overall ROAS hiện tại: <span style='color:#00d4ff;font-weight:700;font-size:18px;'>{overall_roas:.2f}x</span>**", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🚀 Scale ngay")
        scale_camps = df_camp[df_camp["ROAS"] >= 5.0]
        if not scale_camps.empty:
            for _, r in scale_camps.iterrows():
                st.markdown(f"""
                <div class="issue-card" style="border-left:3px solid #00d4ff;">
                    <div class="issue-title" style="color:#00d4ff;">{r['Campaign']}</div>
                    <div class="issue-detail">
                        ROAS: <b style="color:#00ff88">{r['ROAS']:.2f}x</b> | Spend: {fmt_vnd(r['Expense_VND'])}<br>
                        GMV: {fmt_vnd(r['GMV_VND'])} | 👉 Tăng budget 30-50%
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            good_camps = df_camp[df_camp["ROAS"] >= 3.0]
            if not good_camps.empty:
                for _, r in good_camps.iterrows():
                    st.markdown(f"""
                    <div class="issue-card" style="border-left:3px solid #00ff88;">
                        <div class="issue-title" style="color:#00ff88;">{r['Campaign']}</div>
                        <div class="issue-detail">
                            ROAS: <b style="color:#00ff88">{r['ROAS']:.2f}x</b> | Spend: {fmt_vnd(r['Expense_VND'])}<br>
                            GMV: {fmt_vnd(r['GMV_VND'])} | 👉 Maintain hoặc tăng nhẹ 10-20%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Chưa có campaign nào đạt ROAS ≥ 3.0x để scale.")

    with col2:
        st.markdown("### 🛑 Cần tối ưu / Pause")
        pause_camps = df_camp[df_camp["ROAS"] < 1.0]
        if not pause_camps.empty:
            for _, r in pause_camps.iterrows():
                st.markdown(f"""
                <div class="issue-card" style="border-left:3px solid #ff4444;">
                    <div class="issue-title" style="color:#ff4444;">{r['Campaign']}</div>
                    <div class="issue-detail">
                        ROAS: <b style="color:#ff4444">{r['ROAS']:.2f}x</b> | Spend: {fmt_vnd(r['Expense_VND'])}<br>
                        GMV: {fmt_vnd(r['GMV_VND'])} | ⛔ Review targeting & bid trước khi tiếp tục
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="issue-card" style="border-left:3px solid #00ff88;background:#0d2e1a;">
                <div style="color:#00ff88;font-weight:700;">✅ Tất cả campaigns active đều có ROAS > 1.0x</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 📋 Checklist Hành Động — Shopee Ads")

    st.markdown("#### Budget & Bidding")
    st.checkbox("Scale campaigns ROAS > 5x: tăng daily budget +30%")
    st.checkbox("Pause campaigns ROAS < 1.0x đang Ongoing")
    st.checkbox('Chuyển campaigns "GMV Max Auto" → "GMV Max Custom ROAS" với target ROAS = 3.0')
    st.checkbox("Review campaigns Paused có GMV tốt → reactivate với budget nhỏ hơn")

    st.markdown("#### Campaign Structure")
    st.checkbox("Tách riêng campaigns cho từng brand: CAOSTU, HIGHCHIC, FNOS, IAMSAIGON, PARADOX")
    st.checkbox("Tạo Clearance Sale campaign riêng cho sản phẩm tồn kho")
    st.checkbox("Thêm shop voucher vào campaigns có CTR cao để tăng conversion")

    st.markdown("#### Creative & Targeting")
    st.checkbox("Update creative cho campaigns CTR thấp nhất (so sánh trong dữ liệu thực tế)")
    st.checkbox("Test giá thầu cao hơn vào giờ peak (18:00–22:00 +7)")
    st.checkbox("Activate Discovery placement cho campaigns có Product CTR tốt")

    st.markdown("#### Measurement")
    st.checkbox("Export weekly performance report từ Shopee Seller Center")
    st.checkbox("So sánh Direct ROAS vs Total ROAS để đánh giá assisted conversions")
    st.checkbox("Monitor ACOS weekly — target ACOS < 30%")
