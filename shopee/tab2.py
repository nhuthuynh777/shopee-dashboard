import streamlit as st
from utils import fmt_vnd, fmt_num, _hbar, styled_table


def render(df):
    st.markdown("## 🏷️ Product Traffic — Impressions & CTR")

    prod_df = df[df["Ad / Product Name"] != df["Campaign"]].copy()
    prod_df = prod_df[prod_df["Impression"] > 0]

    if prod_df.empty:
        st.info("Không có dữ liệu product-level trong file đã upload.")
        return

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

    st.markdown("### 🎯 Cơ hội: Impression cao nhưng CTR thấp")
    st.caption("Sản phẩm có impressions > median nhưng CTR < median — cần cải thiện thumbnail/giá")
    med_imp = prod_df["Impression"].median()
    opps = prod_df[
        (prod_df["Impression"] > med_imp) & (prod_df["CTR_pct"] < med_ctr)
    ].sort_values("Impression", ascending=False)[
        ["Ad / Product Name", "Impression", "CTR_pct", "Clicks"]
    ].head(10)
    opps.columns = ["Product", "Impressions", "CTR (%)", "Clicks"]
    st.markdown(styled_table(opps), unsafe_allow_html=True)

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

    st.markdown("### 📋 Full Product Performance Table")
    tbl = prod_df[prod_df["GMV_VND"] > 0].sort_values("GMV_VND", ascending=False)[
        ["Ad / Product Name", "GMV_VND", "Items Sold", "Impression", "CTR_pct", "Expense_VND", "ROAS"]
    ].copy()
    tbl.columns = ["Product", "GMV (VNĐ)", "Units Sold", "Impressions", "CTR (%)", "Spend (VNĐ)", "ROAS"]
    tbl["GMV (VNĐ)"]   = tbl["GMV (VNĐ)"].apply(fmt_vnd)
    tbl["Spend (VNĐ)"] = tbl["Spend (VNĐ)"].apply(fmt_vnd)
    tbl["ROAS"]        = tbl["ROAS"].apply(lambda x: f"{x:.2f}x")
    tbl["CTR (%)"]     = tbl["CTR (%)"].apply(lambda x: f"{x:.2f}%")
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
