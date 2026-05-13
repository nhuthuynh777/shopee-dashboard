import streamlit as st
import plotly.graph_objects as go
from utils import fmt_vnd, fmt_num, _ly, _hbar, ROAS_TIERS


def render(df, df_camp):
    st.markdown("## 🏥 Business Health — Shopee Ads")

    total_spend = df["Expense_VND"].sum()
    total_gmv   = df["GMV_VND"].sum()
    overall_roas = total_gmv / total_spend if total_spend > 0 else 0
    total_impressions = df["Impression"].sum()
    total_clicks = df["Clicks"].sum()
    avg_ctr = total_clicks / total_impressions * 100 if total_impressions > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Spend",    fmt_vnd(total_spend))
    c2.metric("Total GMV",      fmt_vnd(total_gmv))
    c3.metric("Overall ROAS",   f"{overall_roas:.2f}x")
    c4.metric("Avg CTR",        f"{avg_ctr:.2f}%", f"{fmt_num(total_clicks)} clicks")
    c5.metric("Impressions",    fmt_num(total_impressions))

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### GMV by Campaign (VNĐ)")
        camp_gmv = df_camp[df_camp["GMV_VND"] > 0].sort_values("GMV_VND", ascending=True)
        if not camp_gmv.empty:
            fig = _hbar(
                y=camp_gmv["Campaign"], x=camp_gmv["GMV_VND"],
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
                y=camp_roas["Campaign"], x=camp_roas["ROAS"],
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

    st.markdown("### Spend vs GMV by Campaign")
    valid = df_camp[df_camp["Expense_VND"] > 0]
    if not valid.empty:
        tier_colors = {t[0]: t[1] for t in ROAS_TIERS}
        max_imp = max(valid["Impressions"].max(), 1)
        fig = go.Figure()
        for tier, color in tier_colors.items():
            sub = valid[valid["ROAS_Tier"] == tier]
            if not sub.empty:
                sz = (sub["Impressions"] / max_imp * 35 + 8).clip(8, 40)
                fig.add_trace(go.Scatter(
                    x=sub["Expense_VND"], y=sub["GMV_VND"],
                    mode="markers", name=tier,
                    marker=dict(size=sz.tolist(), color=color, opacity=0.85,
                                line=dict(color="#1e2235", width=0.5)),
                    text=sub["Campaign"].str[:30],
                    hovertemplate="<b>%{text}</b><br>Spend: %{x:,.0f} ₫<br>GMV: %{y:,.0f} ₫<extra></extra>",
                ))
        from utils import _ly
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
