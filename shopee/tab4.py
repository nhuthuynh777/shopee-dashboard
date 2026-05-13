import re
import streamlit as st
import plotly.graph_objects as go
from utils import fmt_vnd, _ly_pie, _hbar, styled_table, ROAS_TIERS
import pandas as pd


def render(df_camp):
    st.markdown("## 🔍 Campaign Setup Audit")

    # 1. ROAS Classification
    st.markdown("### 1. ROAS Classification")
    tier_table = pd.DataFrame([
        {"Tier": "🔴 Losing",    "ROAS": "< 1.0x",    "Đánh giá": "Chi nhiều hơn doanh thu"},
        {"Tier": "🟡 Below avg", "ROAS": "1.0 – 3.0x", "Đánh giá": "Cần optimize"},
        {"Tier": "🟢 Good",      "ROAS": "3.0 – 5.0x", "Đánh giá": "Hiệu quả tốt"},
        {"Tier": "⭐ Excellent",  "ROAS": "> 5.0x",     "Đánh giá": "Scale aggressively"},
    ])
    st.markdown(styled_table(tier_table), unsafe_allow_html=True)

    roas_tbl = df_camp[["Campaign", "Ad_Status", "Expense_VND", "ROAS", "ROAS_Tier", "ACOS", "CTR"]].copy()
    roas_tbl = roas_tbl.rename(columns={
        "Ad_Status": "Status", "Expense_VND": "Spend (VNĐ)", "ROAS_Tier": "ROAS Tier"
    })
    roas_tbl["Spend (VNĐ)"] = roas_tbl["Spend (VNĐ)"].apply(fmt_vnd)
    roas_tbl["ROAS"]        = roas_tbl["ROAS"].apply(lambda x: f"{x:.2f}x")
    roas_tbl["CTR"]         = roas_tbl["CTR"].apply(lambda x: f"{x:.2f}%")
    roas_tbl["ACOS"]        = roas_tbl["ACOS"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(roas_tbl, hide_index=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        tier_counts = df_camp["ROAS_Tier"].value_counts().reset_index()
        tier_counts.columns = ["Tier", "Count"]
        tier_color_map = {t[0]: t[1] for t in ROAS_TIERS}
        donut_colors = [tier_color_map.get(t, "#888") for t in tier_counts["Tier"]]
        fig = go.Figure(go.Pie(
            values=tier_counts["Count"], labels=tier_counts["Tier"], hole=0.5,
            marker=dict(colors=donut_colors, line=dict(color="#1e2235", width=2)),
            textfont=dict(color="#e0e0e0", size=10),
        ))
        fig.update_layout(**_ly_pie(title=dict(text="# Campaigns by ROAS Tier",
                                               font=dict(color="#e0e0e0", size=12))))
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
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="issue-card" style="border-left:3px solid #00ff88;background:#0d2e1a;">
                <div style="color:#00ff88;font-weight:700;">✅ Tất cả campaigns đang có ROAS > 1.0x</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # 2. ACOS Analysis
    st.markdown("### 2. ACOS Analysis (Advertising Cost of Sales)")
    st.caption("ACOS = Spend / GMV × 100% — thấp hơn là tốt hơn")
    acos_sorted = df_camp[df_camp["ACOS"] > 0].sort_values("ACOS", ascending=True)
    if not acos_sorted.empty:
        colors_acos = ["#00ff88" if v < 30 else "#ffd700" if v < 50 else "#ff4444"
                       for v in acos_sorted["ACOS"]]
        fig = _hbar(
            y=acos_sorted["Campaign"], x=acos_sorted["ACOS"],
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
            values=status_count["Count"], labels=status_count["Status"], hole=0.5,
            marker=dict(colors=status_colors, line=dict(color="#1e2235", width=2)),
            textfont=dict(color="#e0e0e0", size=10),
        ))
        fig.update_layout(**_ly_pie(title=dict(text="# Campaigns by Status",
                                               font=dict(color="#e0e0e0", size=12))))
        st.plotly_chart(fig, use_container_width=True, key="t4_status_pie")

    with col2:
        status_spend = df_camp.groupby("Ad_Status")["Expense_VND"].sum().reset_index()
        bar_colors_status = ["#00d4ff", "#ffd700", "#ff8c00"][:len(status_spend)]
        fig = _hbar(
            y=status_spend["Ad_Status"], x=status_spend["Expense_VND"],
            colors=bar_colors_status,
            texts=[fmt_vnd(v) for v in status_spend["Expense_VND"]],
            xaxis_title="Total Spend (VNĐ)",
        )
        fig.update_layout(title=dict(text="Spend by Status (VNĐ)", font=dict(color="#e0e0e0", size=12)))
        st.plotly_chart(fig, use_container_width=True, key="t4_status_spend_bar")

    st.markdown("---")

    # 4. Naming Convention
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
