import streamlit as st
import plotly.graph_objects as go
from utils import fmt_vnd, fmt_num, _ly, _hbar, styled_table, ROAS_TIERS


def render(df, df_camp):
    st.markdown("## 📊 Onsite Ads Performance")

    total_spend  = df["Expense_VND"].sum()
    total_gmv    = df["GMV_VND"].sum()
    overall_roas = total_gmv / total_spend if total_spend > 0 else 0
    total_imp    = df["Impression"].sum()
    total_clicks = df["Clicks"].sum()
    avg_ctr      = total_clicks / total_imp * 100 if total_imp > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Spend",  fmt_vnd(total_spend))
    c2.metric("Total GMV",    fmt_vnd(total_gmv))
    c3.metric("Overall ROAS", f"{overall_roas:.2f}x")
    c4.metric("Avg CTR",      f"{avg_ctr:.2f}%", f"{fmt_num(total_clicks)} clicks")
    c5.metric("Impressions",  fmt_num(total_imp))

    st.markdown("---")

    st.markdown("### Campaign Performance (All CPC)")
    tbl2 = df_camp[["Campaign", "Ad_Type", "Ad_Status", "Expense_VND", "GMV_VND",
                     "ROAS", "CTR", "ACOS", "Items_Sold"]].copy()
    tbl2 = tbl2.rename(columns={
        "Ad_Type": "Ad Type", "Ad_Status": "Status",
        "Expense_VND": "Spend (VNĐ)", "GMV_VND": "GMV (VNĐ)",
        "CTR": "CTR (%)", "ACOS": "ACOS (%)", "Items_Sold": "Items Sold",
    })
    tbl2["Spend (VNĐ)"] = tbl2["Spend (VNĐ)"].apply(fmt_vnd)
    tbl2["GMV (VNĐ)"]   = tbl2["GMV (VNĐ)"].apply(fmt_vnd)
    tbl2["ROAS"]        = tbl2["ROAS"].apply(lambda x: f"{x:.2f}x")
    tbl2["CTR (%)"]     = tbl2["CTR (%)"].apply(lambda x: f"{x:.2f}%")
    tbl2["ACOS (%)"]    = tbl2["ACOS (%)"].apply(lambda x: f"{x:.1f}%")
    st.markdown(styled_table(tbl2), unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### GMV by Campaign (VNĐ)")
        camp_sorted = df_camp[df_camp["GMV_VND"] > 0].sort_values("GMV_VND", ascending=True)
        if not camp_sorted.empty:
            fig = _hbar(
                y=camp_sorted["Campaign"], x=camp_sorted["GMV_VND"],
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
                y=roas_sorted["Campaign"], x=roas_sorted["ROAS"],
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

    st.markdown("### CTR vs ROAS — bubble size = Spend")
    bubble_df = df_camp[df_camp["Expense_VND"] > 0]
    if not bubble_df.empty:
        tier_colors = {t[0]: t[1] for t in ROAS_TIERS}
        max_spend = max(bubble_df["Expense_VND"].max(), 1)
        fig = go.Figure()
        for tier, color in tier_colors.items():
            sub = bubble_df[bubble_df["ROAS_Tier"] == tier]
            if not sub.empty:
                sz = (sub["Expense_VND"] / max_spend * 35 + 8).clip(8, 40)
                fig.add_trace(go.Scatter(
                    x=sub["CTR"], y=sub["ROAS"],
                    mode="markers", name=tier,
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
