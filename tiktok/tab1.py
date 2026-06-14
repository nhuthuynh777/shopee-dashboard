import streamlit as st
import plotly.graph_objects as go
from utils import fmt_vnd, fmt_num, _ly, _hbar, ROAS_TIERS, get_roas_tier, THB_TO_VND


def render(df, df_camp):
    st.markdown("## 📊 Business Health — TikTok Ads")

    if df.empty:
        st.warning("Chưa có data. Upload file TikTok Ads Performance (.xlsx) ở sidebar.")
        return

    total_spend    = df['Cost_VND'].sum()
    total_gmv      = df['GMV_VND'].sum()
    overall_roas   = total_gmv / total_spend if total_spend > 0 else 0
    total_impr     = df['Impressions'].sum()
    total_reach    = df['Reach'].sum()
    total_clicks   = df['Clicks'].sum()
    total_purchases= df['Purchases'].sum()
    avg_ctr        = total_clicks / total_impr * 100 if total_impr > 0 else 0

    st.markdown(
        f'<div class="info-banner">💱 Cost & GMV đã quy đổi: 1 THB = {THB_TO_VND:,} VNĐ</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Spend",    fmt_vnd(total_spend))
    c2.metric("Total GMV",      fmt_vnd(total_gmv))
    c3.metric("ROAS",           f"{overall_roas:.2f}x")
    c4.metric("Impressions",    fmt_num(total_impr))
    c5.metric("Purchases",      fmt_num(total_purchases))

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### GMV by Campaign")
        camp_gmv = (df_camp[df_camp['GMV_VND'] > 0]
                    .sort_values('GMV_VND', ascending=True).tail(15))
        if not camp_gmv.empty:
            fig = _hbar(
                y=camp_gmv['Campaign'].str[:35],
                x=camp_gmv['GMV_VND'],
                colors='#00d4ff',
                texts=[fmt_vnd(v) for v in camp_gmv['GMV_VND']],
                xaxis_title='GMV (VNĐ)',
            )
            st.plotly_chart(fig, use_container_width=True, key='tt1_gmv')

    with col2:
        st.markdown("### ROAS by Campaign")
        camp_roas = (df_camp[df_camp['ROAS'] > 0]
                     .sort_values('ROAS', ascending=True).tail(15))
        if not camp_roas.empty:
            fig = _hbar(
                y=camp_roas['Campaign'].str[:35],
                x=camp_roas['ROAS'],
                colors=camp_roas['ROAS_Color'].tolist(),
                texts=[f"{v:.2f}x" for v in camp_roas['ROAS']],
                xaxis_title='ROAS',
            )
            fig.add_vline(x=1.0, line_dash="dash", line_color="#ff4444",
                          annotation_text="1.0x", annotation_font_color="#ff4444",
                          annotation_position="top right")
            fig.add_vline(x=3.0, line_dash="dash", line_color="#00ff88",
                          annotation_text="3.0x", annotation_font_color="#00ff88",
                          annotation_position="top right")
            st.plotly_chart(fig, use_container_width=True, key='tt1_roas')

    # Trend by day (only if date data available)
    if df['Date'].notna().any():
        st.markdown("### Spend vs GMV Trend")
        daily = (df.groupby(df['Date'].dt.date)
                 .agg(Cost_VND=('Cost_VND', 'sum'), GMV_VND=('GMV_VND', 'sum'))
                 .reset_index()
                 .sort_values('Date'))
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily['Date'], y=daily['GMV_VND'], name='GMV',
            line=dict(color='#00d4ff', width=2),
            hovertemplate='%{x}<br>GMV: %{y:,.0f} ₫<extra></extra>',
        ))
        fig.add_trace(go.Scatter(
            x=daily['Date'], y=daily['Cost_VND'], name='Spend',
            line=dict(color='#ff6b6b', width=2),
            hovertemplate='%{x}<br>Spend: %{y:,.0f} ₫<extra></extra>',
        ))
        fig.update_layout(**_ly(xaxis_title='Date', yaxis_title='VNĐ'))
        st.plotly_chart(fig, use_container_width=True, key='tt1_trend')

    top_camp = df_camp.loc[df_camp['GMV_VND'].idxmax(), 'Campaign'] if not df_camp.empty else '-'
    losing   = df_camp[df_camp['ROAS'] < 1.0]
    roas_tier, _ = get_roas_tier(overall_roas)

    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>Tổng chi: <b style="color:#ff6b6b">{fmt_vnd(total_spend)}</b> | GMV: <b style="color:#00d4ff">{fmt_vnd(total_gmv)}</b> | ROAS: <b style="color:#00d4ff">{overall_roas:.2f}x</b> ({roas_tier})</li>
            <li>Campaign GMV cao nhất: <b style="color:#00ff88">{top_camp}</b></li>
            <li>Impressions: <b style="color:#00d4ff">{fmt_num(total_impr)}</b> | Reach: <b style="color:#00d4ff">{fmt_num(total_reach)}</b> | CTR: <b style="color:#00d4ff">{avg_ctr:.2f}%</b></li>
            <li>Campaigns ROAS &lt; 1.0: <b style="color:#ff4444">{len(losing)} campaigns</b></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
