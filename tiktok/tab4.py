import streamlit as st
from utils import fmt_vnd, fmt_num, _hbar, styled_table, THB_TO_VND


def render(df_gmvmax):
    st.markdown("## 📦 GMV Max — TikTok Shop Sales")

    if df_gmvmax.empty:
        st.markdown("""
        <div style='background:#1e2235;border:1px solid #2d3149;border-radius:12px;
        padding:48px;text-align:center;margin-top:24px;'>
            <div style='font-size:40px;margin-bottom:12px;'>📦</div>
            <div style='font-size:16px;color:#e0e0e0;margin-bottom:8px;'>Chưa có GMV Max data</div>
            <div style='color:#8b9bb4;font-size:13px;'>Upload file TikTok Shop Sales (.xlsx) ở sidebar để xem báo cáo</div>
        </div>""", unsafe_allow_html=True)
        return

    st.markdown(
        f'<div class="info-banner">💱 GMV & AOV đã quy đổi: 1 THB = {THB_TO_VND:,} VNĐ</div>',
        unsafe_allow_html=True,
    )

    total_gmv      = df_gmvmax['GMV_VND'].sum()
    total_purchases= df_gmvmax['Purchases'].sum()
    total_items    = df_gmvmax['Items'].sum()
    aov            = total_gmv / total_purchases if total_purchases > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total GMV",    fmt_vnd(total_gmv))
    c2.metric("Purchases",    fmt_num(total_purchases))
    c3.metric("Items Sold",   fmt_num(total_items))
    c4.metric("AOV",          fmt_vnd(aov))

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Top products by GMV
    with col1:
        st.markdown("### 🏆 Top Products by GMV")
        top_gmv = (df_gmvmax.groupby('Product', as_index=False)
                   .agg(GMV_VND=('GMV_VND', 'sum'), Purchases=('Purchases', 'sum'))
                   .sort_values('GMV_VND', ascending=True).tail(15))
        if not top_gmv.empty:
            fig = _hbar(
                y=top_gmv['Product'].str[:45],
                x=top_gmv['GMV_VND'],
                colors='#00d4ff',
                texts=[fmt_vnd(v) for v in top_gmv['GMV_VND']],
                xaxis_title='GMV (VNĐ)',
            )
            st.plotly_chart(fig, use_container_width=True, key='tt4_top_gmv')

    # Top products by purchases
    with col2:
        st.markdown("### 📦 Top Products by Purchases")
        top_purch = (df_gmvmax.groupby('Product', as_index=False)
                     .agg(Purchases=('Purchases', 'sum'), GMV_VND=('GMV_VND', 'sum'))
                     .sort_values('Purchases', ascending=True).tail(15))
        if not top_purch.empty:
            fig = _hbar(
                y=top_purch['Product'].str[:45],
                x=top_purch['Purchases'],
                colors='#00ff88',
                texts=[fmt_num(v) for v in top_purch['Purchases']],
                xaxis_title='Purchases',
            )
            st.plotly_chart(fig, use_container_width=True, key='tt4_top_purch')

    # By Brand
    brands = df_gmvmax[df_gmvmax['Brand'].str.strip() != '']['Brand'].unique()
    if len(brands) > 1:
        st.markdown("### 🏷️ GMV by Brand")
        by_brand = (df_gmvmax.groupby('Brand', as_index=False)
                    .agg(GMV_VND=('GMV_VND', 'sum'), Purchases=('Purchases', 'sum'))
                    .sort_values('GMV_VND', ascending=True))
        fig = _hbar(
            y=by_brand['Brand'],
            x=by_brand['GMV_VND'],
            colors='#ffd700',
            texts=[fmt_vnd(v) for v in by_brand['GMV_VND']],
            xaxis_title='GMV (VNĐ)',
        )
        st.plotly_chart(fig, use_container_width=True, key='tt4_brand_gmv')

    # Table by campaign
    st.markdown("### 📊 Performance by Campaign")
    by_camp = (df_gmvmax.groupby('Campaign', as_index=False)
               .agg(GMV_VND=('GMV_VND', 'sum'),
                    Purchases=('Purchases', 'sum'),
                    AOV_VND=('AOV_VND', 'mean'))
               .sort_values('GMV_VND', ascending=False))
    if not by_camp.empty:
        tbl = by_camp.copy()
        tbl['GMV']       = tbl['GMV_VND'].apply(fmt_vnd)
        tbl['Purchases'] = tbl['Purchases'].apply(lambda x: fmt_num(x))
        tbl['AOV']       = tbl['AOV_VND'].apply(fmt_vnd)
        st.markdown(
            styled_table(tbl[['Campaign', 'GMV', 'Purchases', 'AOV']]),
            unsafe_allow_html=True,
        )
