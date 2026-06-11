import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import fmt_vnd, fmt_num, _ly, _hbar, styled_table
from shopify.data import load_csv

_SAMPLE_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_shopify_line_items.csv")

BRAND_COLORS = {
    "CAOSTU":    "#00d4ff",
    "HIGHCHIC":  "#ff6b9d",
    "FNOS":      "#ffd700",
    "IAMSAIGON": "#00ff88",
    "PARADOX":   "#9d4edd",
}
_REFUND_STATUSES = {"refunded", "partially_refunded"}


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df["Financial Status"] = df["Financial Status"].str.lower().str.strip()
    for col in ["Line Total", "Unit Price", "Discount", "Quantity", "Discount Pct"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Created at"]  = pd.to_datetime(df["Created at"])
    df["month_key"]   = df["Created at"].dt.strftime("%Y-%m")
    df["month_label"] = df["Created at"].dt.strftime("%b %Y")
    return df


def render(uploaded_file=None):
    st.markdown("## 🏷️ Brand & Product")

    df_raw, source = load_csv(uploaded_file, _SAMPLE_CSV, parse_dates=["Created at"])
    if df_raw.empty:
        st.warning("Chưa có data. Upload file Line Items (.csv) ở sidebar hoặc thêm sample data.")
        return
    df_all = _clean(df_raw.copy())
    # Exclude refunded orders from revenue metrics
    df = df_all[~df_all["Financial Status"].isin(_REFUND_STATUSES)].copy()

    brands  = sorted(df["Brand"].unique())
    colors  = [BRAND_COLORS.get(b, "#8b9bb4") for b in brands]

    st.markdown(
        f'<div class="info-banner">'
        f'📦 {len(df_all)} line items · {df_all["Order Name"].nunique()} orders · '
        f'{len(brands)} brands · {source}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Section 1: Brand summary ───────────────────────────────────────────────
    st.markdown("### Net Sales & Units by Brand")
    brand_sum = (
        df.groupby("Brand", sort=False)
        .agg(net_sales=("Line Total", "sum"), units=("Quantity", "sum"),
             orders=("Order Name", "nunique"), discount=("Discount", "sum"))
        .reset_index()
        .sort_values("net_sales", ascending=False)
    )
    brand_sum["aov"] = brand_sum["net_sales"] / brand_sum["orders"]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Net Sales by Brand (VNĐ)")
        bsorted = brand_sum.sort_values("net_sales", ascending=True)
        fig = _hbar(
            y=bsorted["Brand"],
            x=bsorted["net_sales"],
            colors=[BRAND_COLORS.get(b, "#8b9bb4") for b in bsorted["Brand"]],
            texts=[fmt_vnd(v) for v in bsorted["net_sales"]],
            xaxis_title="Net Sales (VNĐ)",
        )
        st.plotly_chart(fig, use_container_width=True, key="sf2_brand_sales")

    with col2:
        st.markdown("#### Units Sold by Brand")
        bsorted2 = brand_sum.sort_values("units", ascending=True)
        fig = _hbar(
            y=bsorted2["Brand"],
            x=bsorted2["units"],
            colors=[BRAND_COLORS.get(b, "#8b9bb4") for b in bsorted2["Brand"]],
            texts=[fmt_num(v) for v in bsorted2["units"]],
            xaxis_title="Units Sold",
        )
        st.plotly_chart(fig, use_container_width=True, key="sf2_brand_units")

    # Brand summary table
    tbl_brand = brand_sum[["Brand", "net_sales", "units", "orders", "aov", "discount"]].copy()
    tbl_brand.columns = ["Brand", "Net Sales", "Units", "Orders", "AOV", "Total Discount"]
    tbl_brand["Net Sales"]      = tbl_brand["Net Sales"].apply(fmt_vnd)
    tbl_brand["AOV"]            = tbl_brand["AOV"].apply(fmt_vnd)
    tbl_brand["Total Discount"] = tbl_brand["Total Discount"].apply(fmt_vnd)
    tbl_brand["Units"]          = tbl_brand["Units"].apply(fmt_num)
    st.markdown(styled_table(tbl_brand), unsafe_allow_html=True)

    st.markdown("---")

    # ── Section 2: Monthly Revenue Stacked by Brand ────────────────────────────
    st.markdown("### Monthly Revenue by Brand (Stacked)")
    monthly_brand = (
        df.groupby(["month_key", "month_label", "Brand"], sort=True)["Line Total"]
        .sum()
        .reset_index()
    )
    months_ordered = monthly_brand.drop_duplicates("month_key").sort_values("month_key")["month_label"].tolist()

    fig = go.Figure()
    for brand in brands:
        sub = monthly_brand[monthly_brand["Brand"] == brand]
        sub = sub[["month_label", "Line Total"]].set_index("month_label").reindex(months_ordered, fill_value=0).reset_index()
        fig.add_trace(go.Bar(
            name=brand,
            x=sub["month_label"],
            y=sub["Line Total"],
            marker_color=BRAND_COLORS.get(brand, "#8b9bb4"),
            text=[fmt_vnd(v) if v > 0 else "" for v in sub["Line Total"]],
            textposition="inside",
            textfont=dict(color="#0e1117", size=9),
            hovertemplate=f"<b>{brand}</b><br>%{{x}}: %{{y:,.0f}} ₫<extra></extra>",
        ))
    fig.update_layout(
        **_ly(xaxis_title="Month", yaxis_title="Revenue (VNĐ)", height=380),
        barmode="stack",
    )
    st.plotly_chart(fig, use_container_width=True, key="sf2_monthly_stacked")

    st.markdown("---")

    # ── Section 3: Top Products ────────────────────────────────────────────────
    st.markdown("### Top Products by Net Sales")
    top_prod = (
        df.groupby(["Brand", "Product", "SKU"], sort=False)
        .agg(net_sales=("Line Total", "sum"), units=("Quantity", "sum"),
             orders=("Order Name", "nunique"), avg_price=("Unit Price", "mean"))
        .reset_index()
        .sort_values("net_sales", ascending=False)
        .head(20)
    )

    col3, col4 = st.columns([3, 2])

    with col3:
        tbl_prod = top_prod[["Brand", "Product", "SKU", "net_sales", "units", "orders", "avg_price"]].copy()
        tbl_prod.columns = ["Brand", "Product", "SKU", "Net Sales", "Units", "Orders", "Avg Price"]
        tbl_prod["Net Sales"]  = tbl_prod["Net Sales"].apply(fmt_vnd)
        tbl_prod["Avg Price"]  = tbl_prod["Avg Price"].apply(fmt_vnd)
        tbl_prod["Units"]      = tbl_prod["Units"].apply(fmt_num)
        st.markdown(styled_table(tbl_prod), unsafe_allow_html=True)

    with col4:
        st.markdown("#### Top 10 by Net Sales")
        top10 = top_prod.head(10).sort_values("net_sales", ascending=True)
        fig = _hbar(
            y=top10["Product"].str[:35],
            x=top10["net_sales"],
            colors=[BRAND_COLORS.get(b, "#8b9bb4") for b in top10["Brand"]],
            texts=[fmt_vnd(v) for v in top10["net_sales"]],
            xaxis_title="Net Sales (VNĐ)",
        )
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True, key="sf2_top10_prod")

    st.markdown("---")

    # ── Section 4: Discount Analysis ──────────────────────────────────────────
    st.markdown("### Discount Analysis by Brand")
    disc_brand = (
        df_all.groupby("Brand")
        .agg(
            total_discount=("Discount", "sum"),
            gross_revenue=("Line Total", "sum"),
            avg_disc_pct=("Discount Pct", "mean"),
            disc_orders=("Order Name", lambda x: (df_all.loc[x.index, "Discount"] > 0).sum()),
        )
        .reset_index()
    )
    disc_brand["disc_rate"] = disc_brand["total_discount"] / (
        disc_brand["gross_revenue"] + disc_brand["total_discount"]
    ) * 100

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("#### Total Discount by Brand (VNĐ)")
        ds = disc_brand.sort_values("total_discount", ascending=True)
        fig = _hbar(
            y=ds["Brand"],
            x=ds["total_discount"],
            colors=[BRAND_COLORS.get(b, "#8b9bb4") for b in ds["Brand"]],
            texts=[fmt_vnd(v) for v in ds["total_discount"]],
            xaxis_title="Discount (VNĐ)",
        )
        st.plotly_chart(fig, use_container_width=True, key="sf2_disc_total")

    with col6:
        st.markdown("#### Avg Discount Rate by Brand (%)")
        ds2 = disc_brand.sort_values("disc_rate", ascending=True)
        bar_colors = ["#ffd700" if v > 8 else "#00d4ff" for v in ds2["disc_rate"]]
        fig = _hbar(
            y=ds2["Brand"],
            x=ds2["disc_rate"],
            colors=bar_colors,
            texts=[f"{v:.1f}%" for v in ds2["disc_rate"]],
            xaxis_title="Discount Rate (%)",
        )
        fig.add_vline(x=10, line_dash="dash", line_color="#ff4444",
                      annotation_text="10% threshold", annotation_font_color="#ff4444",
                      annotation_position="top right")
        st.plotly_chart(fig, use_container_width=True, key="sf2_disc_rate")

    # ── Quick Insight ──────────────────────────────────────────────────────────
    top_brand    = brand_sum.iloc[0]["Brand"]
    top_brand_rev = brand_sum.iloc[0]["net_sales"]
    top_product  = top_prod.iloc[0]["Product"]
    total_disc   = df_all["Discount"].sum()
    total_rev    = df["Line Total"].sum()
    disc_pct_all = total_disc / (total_rev + total_disc) * 100 if (total_rev + total_disc) > 0 else 0

    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>Brand doanh thu cao nhất: <b style="color:#00d4ff">{top_brand}</b>
                — {fmt_vnd(top_brand_rev)}</li>
            <li>Sản phẩm bán chạy nhất: <b style="color:#00ff88">{top_product}</b></li>
            <li>Tổng discount đã tặng: <b style="color:#ffd700">{fmt_vnd(total_disc)}</b>
                ({disc_pct_all:.1f}% of gross revenue)</li>
            <li>Brands: {" · ".join(
                "<b style='color:" + BRAND_COLORS.get(b, "#8b9bb4") + "'>" + b + "</b>"
                for b in brand_sum["Brand"].tolist()
            )}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
