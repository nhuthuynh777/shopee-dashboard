import streamlit as st
import plotly.graph_objects as go
from utils import fmt_vnd, fmt_num, _ly, _hbar, get_roas_tier


def render(df, df_camp):
    st.markdown("## 🛒 Shop Performance — TikTok Shop")

    if df.empty:
        st.warning("Chưa có data. Upload file TikTok Ads Performance (.xlsx) ở sidebar.")
        return

    total_spend    = df['Cost_VND'].sum()
    total_gmv      = df['GMV_VND'].sum()
    total_purchases= df['Purchases'].sum()
    total_atc      = df['ATC'].sum()
    total_checkouts= df['Checkouts'].sum()
    total_clicks   = df['Clicks'].sum()
    total_prod_views = df['Product_Views'].sum()
    overall_roas   = total_gmv / total_spend if total_spend > 0 else 0
    aov            = total_gmv / total_purchases if total_purchases > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Purchases",  fmt_num(total_purchases))
    c2.metric("Total GMV",  fmt_vnd(total_gmv))
    c3.metric("ROAS",       f"{overall_roas:.2f}x")
    c4.metric("AOV",        fmt_vnd(aov))
    c5.metric("Add to Cart",fmt_num(total_atc))

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Conversion funnel
    with col1:
        st.markdown("### 🔽 Conversion Funnel")
        funnel_labels, funnel_vals = [], []
        for label, val in [
            ("Clicks",         total_clicks),
            ("Product Views",  total_prod_views),
            ("Add to Cart",    total_atc),
            ("Checkouts",      total_checkouts),
            ("Purchases",      total_purchases),
        ]:
            if val > 0:
                funnel_labels.append(label)
                funnel_vals.append(val)

        if len(funnel_labels) > 1:
            fig = go.Figure(go.Funnel(
                y=funnel_labels, x=funnel_vals,
                textinfo="value+percent initial",
                textfont=dict(color='#e0e0e0', size=11),
                marker=dict(color=['#00d4ff', '#00b4d8', '#0090a0', '#006e80', '#00d464'][:len(funnel_labels)]),
            ))
            fig.update_layout(
                paper_bgcolor='#1e2235', plot_bgcolor='#1e2235',
                font=dict(color='#c0c8d8'),
                height=350, margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(fig, use_container_width=True, key='tt3_funnel')

    # GMV by campaign
    with col2:
        st.markdown("### GMV by Campaign")
        camp_gmv = (df_camp[df_camp['GMV_VND'] > 0]
                    .sort_values('GMV_VND', ascending=True).tail(12))
        if not camp_gmv.empty:
            fig = _hbar(
                y=camp_gmv['Campaign'].str[:30],
                x=camp_gmv['GMV_VND'],
                colors='#00d464',
                texts=[fmt_vnd(v) for v in camp_gmv['GMV_VND']],
                xaxis_title='GMV (VNĐ)',
            )
            st.plotly_chart(fig, use_container_width=True, key='tt3_gmv_camp')

    # GMV trend by day
    if df['Date'].notna().any():
        st.markdown("### GMV & Spend Trend by Day")
        daily = (df.groupby(df['Date'].dt.date)
                 .agg(GMV_VND=('GMV_VND', 'sum'),
                      Cost_VND=('Cost_VND', 'sum'),
                      Purchases=('Purchases', 'sum'))
                 .reset_index()
                 .sort_values('Date'))

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=daily['Date'], y=daily['GMV_VND'], name='GMV',
            marker_color='rgba(0,212,100,0.7)',
            hovertemplate='%{x}<br>GMV: %{y:,.0f} ₫<extra></extra>',
        ))
        fig.add_trace(go.Scatter(
            x=daily['Date'], y=daily['Cost_VND'], name='Spend',
            line=dict(color='#ff6b6b', width=2),
            hovertemplate='%{x}<br>Spend: %{y:,.0f} ₫<extra></extra>',
        ))
        fig.update_layout(**_ly(xaxis_title='Date', yaxis_title='VNĐ'))
        st.plotly_chart(fig, use_container_width=True, key='tt3_trend')

    # Purchases trend
    if df['Date'].notna().any():
        st.markdown("### Purchases by Day")
        daily2 = (df.groupby(df['Date'].dt.date)
                  .agg(Purchases=('Purchases', 'sum'))
                  .reset_index()
                  .sort_values('Date'))
        fig2 = go.Figure(go.Bar(
            x=daily2['Date'], y=daily2['Purchases'],
            marker_color='#00d4ff',
            hovertemplate='%{x}<br>Purchases: %{y:,}<extra></extra>',
        ))
        fig2.update_layout(**_ly(xaxis_title='Date', yaxis_title='Purchases'))
        st.plotly_chart(fig2, use_container_width=True, key='tt3_purchases_trend')

    atc_rate = total_atc / total_clicks * 100 if total_clicks > 0 else 0
    cr       = total_purchases / total_clicks * 100 if total_clicks > 0 else 0
    roas_tier, _ = get_roas_tier(overall_roas)

    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>Purchases: <b style="color:#00d4ff">{fmt_num(total_purchases)}</b> | GMV: <b style="color:#00d4ff">{fmt_vnd(total_gmv)}</b> | AOV: <b style="color:#00d4ff">{fmt_vnd(aov)}</b></li>
            <li>ROAS: <b style="color:#00d4ff">{overall_roas:.2f}x</b> ({roas_tier}) | ATC: <b style="color:#00ff88">{fmt_num(total_atc)}</b> | ATC Rate: <b style="color:#00ff88">{atc_rate:.2f}%</b></li>
            <li>Purchase CR: <b style="color:#ffd700">{cr:.2f}%</b> | Checkouts: <b style="color:#ffd700">{fmt_num(total_checkouts)}</b></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
