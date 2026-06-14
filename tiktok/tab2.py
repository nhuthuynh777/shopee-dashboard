import streamlit as st
import plotly.graph_objects as go
from utils import fmt_num, _ly, _hbar


def render(df, df_camp):
    st.markdown("## 🎬 Video Performance — TikTok Ads")

    if df.empty:
        st.warning("Chưa có data. Upload file TikTok Ads Performance (.xlsx) ở sidebar.")
        return

    total_impr    = df['Impressions'].sum()
    total_reach   = df['Reach'].sum()
    total_6s      = df['Video_6s'].sum()
    total_25      = df['Video_25'].sum()
    total_50      = df['Video_50'].sum()
    total_75      = df['Video_75'].sum()
    total_100     = df['Video_100'].sum()
    avg_play_raw  = df['AvgPlayTime'].replace(0, float('nan')).mean()
    avg_play      = avg_play_raw if avg_play_raw == avg_play_raw else None  # NaN check

    view_rate_6s  = total_6s / total_impr * 100 if total_impr > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Impressions",      fmt_num(total_impr))
    c2.metric("Reach",            fmt_num(total_reach))
    c3.metric("6-sec Views",      fmt_num(total_6s))
    c4.metric("6-sec View Rate",  f"{view_rate_6s:.1f}%")
    c5.metric("Avg Play Time",    f"{avg_play:.2f}s" if avg_play is not None else "N/A")

    st.markdown("---")

    col1, col2 = st.columns(2)

    # Video view funnel
    with col1:
        st.markdown("### 📉 Video View Funnel")
        stages, vals = [], []
        for label, total in [
            ("Impressions",  total_impr),
            ("6-sec Views",  total_6s),
            ("25% Views",    total_25),
            ("50% Views",    total_50),
            ("75% Views",    total_75),
            ("100% Views",   total_100),
        ]:
            if total > 0:
                stages.append(label)
                vals.append(total)

        if len(stages) > 1:
            colors = ['#00d4ff', '#00b4d8', '#008fb8', '#006e90', '#004e68', '#003040']
            fig = go.Figure(go.Funnel(
                y=stages, x=vals,
                textinfo="value+percent initial",
                textfont=dict(color='#e0e0e0', size=11),
                marker=dict(color=colors[:len(stages)]),
            ))
            fig.update_layout(
                paper_bgcolor='#1e2235', plot_bgcolor='#1e2235',
                font=dict(color='#c0c8d8'),
                height=350, margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(fig, use_container_width=True, key='tt2_funnel')

    # View rate breakdown
    with col2:
        st.markdown("### 📊 View Rate vs Impressions")
        base = total_impr if total_impr > 0 else 1
        rate_items = [
            ("6-sec view rate",  total_6s,  '#00d4ff'),
            ("25% view rate",    total_25,  '#00b4d8'),
            ("50% view rate",    total_50,  '#008fb8'),
            ("75% view rate",    total_75,  '#ffd700'),
            ("100% view rate",   total_100, '#00ff88'),
        ]
        for label, val, color in rate_items:
            if val > 0:
                rate = val / base * 100
                st.markdown(f"""
                <div class="kpi-card" style="margin-bottom:6px;padding:10px 16px;">
                    <div class="kpi-label">{label}</div>
                    <div style="display:flex;align-items:baseline;gap:12px;">
                        <div class="kpi-value" style="font-size:20px;color:{color}">{rate:.2f}%</div>
                        <div class="kpi-sub">{fmt_num(val)} views</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Video 6s by campaign
    st.markdown("### 🎯 6-sec Views by Campaign")
    camp_v = (df_camp[df_camp['Video_6s'] > 0]
              .sort_values('Video_6s', ascending=True).tail(15))
    if not camp_v.empty:
        # Compute view rate per campaign
        camp_v = camp_v.copy()
        camp_v['ViewRate'] = camp_v.apply(
            lambda r: r['Video_6s'] / r['Impressions'] * 100 if r['Impressions'] > 0 else 0, axis=1)
        col1, col2 = st.columns(2)
        with col1:
            fig = _hbar(
                y=camp_v['Campaign'].str[:35],
                x=camp_v['Video_6s'],
                colors='#00b4d8',
                texts=[fmt_num(v) for v in camp_v['Video_6s']],
                xaxis_title='6-sec Views',
            )
            st.plotly_chart(fig, use_container_width=True, key='tt2_6s_camp')
        with col2:
            fig = _hbar(
                y=camp_v['Campaign'].str[:35],
                x=camp_v['ViewRate'],
                colors='#00d4ff',
                texts=[f"{v:.1f}%" for v in camp_v['ViewRate']],
                xaxis_title='6-sec View Rate (%)',
            )
            st.plotly_chart(fig, use_container_width=True, key='tt2_viewrate_camp')

    # Engagement
    total_likes    = df['Paid_Likes'].sum()
    total_comments = df['Paid_Comments'].sum()
    total_shares   = df['Paid_Shares'].sum()
    total_follows  = df['Paid_Follows'].sum()
    total_profile  = df['Paid_Profile'].sum()

    if total_likes + total_comments + total_shares + total_follows > 0:
        st.markdown("### 💬 Paid Engagement")
        e1, e2, e3, e4, e5 = st.columns(5)
        e1.metric("Likes",          fmt_num(total_likes))
        e2.metric("Comments",       fmt_num(total_comments))
        e3.metric("Shares",         fmt_num(total_shares))
        e4.metric("Follows",        fmt_num(total_follows))
        e5.metric("Profile Visits", fmt_num(total_profile))

    # Quick insight
    best_camp = ''
    if not df_camp.empty and df_camp['Video_6s'].sum() > 0:
        best_camp = df_camp.loc[df_camp['Video_6s'].idxmax(), 'Campaign']

    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>6-sec view rate: <b style="color:#00d4ff">{view_rate_6s:.1f}%</b> trên tổng <b>{fmt_num(total_impr)}</b> impressions</li>
            <li>Video hoàn thành 50%: <b style="color:#ffd700">{fmt_num(total_50)}</b> ({total_50/base*100:.1f}%)</li>
            <li>Video hoàn thành 100%: <b style="color:#00ff88">{fmt_num(total_100)}</b> ({total_100/base*100:.1f}%)</li>
            {f'<li>Campaign views cao nhất: <b style="color:#00ff88">{best_camp}</b></li>' if best_camp else ''}
        </ul>
    </div>
    """, unsafe_allow_html=True)
