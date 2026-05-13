import re
import streamlit as st
from utils import styled_table
from shopify.data import load_meta_ads, clean_meta_ads, get_meta_campaign_summary


def render(meta_files):
    st.markdown("## 🔍 Campaign Setup Audit")
    st.caption("Naming convention, active/inactive spend, GA4 cross-reference, performance issues")

    if not meta_files:
        st.markdown("""
        <div style='background:#1e2235;border:1px solid #2d3149;border-radius:12px;
        padding:48px;text-align:center;margin-top:24px;'>
            <div style='font-size:40px;margin-bottom:12px;'>🚧</div>
            <div style='font-size:18px;color:#e0e0e0;margin-bottom:8px;'>Campaign Setup Audit</div>
            <div style='color:#8b9bb4;font-size:13px;'>Upload Meta Ads data để kiểm tra naming convention và performance issues.</div>
        </div>""", unsafe_allow_html=True)
        return

    with st.spinner("Đang phân tích..."):
        df_mc = get_meta_campaign_summary(clean_meta_ads(load_meta_ads(meta_files)))

    if df_mc.empty:
        st.error("Không đọc được dữ liệu Meta Ads hợp lệ.")
        return

    # Naming Convention
    st.markdown("### Naming Convention Check")

    def _check_naming(name):
        issues = []
        if not re.search(r'\d{4}|\d{2}[-_]\d{2}', str(name)):
            issues.append("⚠️ Thiếu ngày/tháng")
        kws = ["retargeting", "prospecting", "brand", "dpa", "collection", "sale"]
        if not any(k in str(name).lower() for k in kws):
            issues.append("⚠️ Không rõ objective")
        return "✅ OK" if not issues else " | ".join(issues)

    naming_df = df_mc[["Campaign", "ROAS_Tier"]].copy()
    naming_df["Naming Issues"] = naming_df["Campaign"].apply(_check_naming)
    st.markdown(styled_table(naming_df), unsafe_allow_html=True)

    st.markdown("---")

    # Performance Issues
    st.markdown("### Performance Issues")
    losing = df_mc[df_mc["ROAS"] < 1.0]
    if not losing.empty:
        for _, r in losing.iterrows():
            st.markdown(f"""
            <div class="issue-card" style="border-left:3px solid #ff4444;">
                <div class="issue-title" style="color:#ff4444;">🔴 {r['Campaign']}</div>
                <div class="issue-detail">ROAS: {r['ROAS']:.2f}x — chi nhiều hơn doanh thu</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="issue-card" style="border-left:3px solid #00ff88;background:#0d2e1a;">
            <div style="color:#00ff88;font-weight:700;">✅ Tất cả campaigns đang có ROAS > 1.0x</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # GA4 Cross-reference (placeholder)
    st.markdown("### GA4 Cross-reference")
    st.markdown("""
    <div class="info-banner">
        ℹ️ GA4 cross-reference cần GA4 export (Sessions / Revenue by source).
        Upload GA4 data để so sánh với Meta Ads data.
    </div>""", unsafe_allow_html=True)
