import streamlit as st
from shopify.data import load_meta_ads, clean_meta_ads, get_meta_campaign_summary


def render(meta_files):
    st.markdown("## 📌 Summary Insight")
    st.caption("Auto-generated issues, data quality score")

    data_checks = {
        "Meta Ads: file đã upload":       bool(meta_files),
        "Meta Ads: Campaign data hợp lệ": False,
        "Shopify Orders: đã upload":       False,
        "GA4 Traffic: đã upload":          False,
        "GA4 Revenue by channel":          False,
    }

    if meta_files:
        try:
            dc = get_meta_campaign_summary(clean_meta_ads(load_meta_ads(meta_files)))
            data_checks["Meta Ads: Campaign data hợp lệ"] = not dc.empty
        except Exception:
            pass

    score = sum(data_checks.values())
    total = len(data_checks)
    pct   = score / total * 100
    color = "#00ff88" if pct >= 80 else "#ffd700" if pct >= 50 else "#ff4444"
    label = "Tốt" if pct >= 80 else "Trung bình" if pct >= 50 else "Thiếu nhiều"

    st.markdown(f"""
    <div style="background:#1e2235;border:1px solid #2d3149;border-radius:12px;
    padding:24px;text-align:center;margin-bottom:16px;">
        <div style="color:#8b9bb4;font-size:13px;margin-bottom:8px;">Data Completeness Score</div>
        <div style="color:{color};font-size:48px;font-weight:700;">{score}/{total}</div>
        <div style="color:{color};font-size:16px;">{pct:.0f}% — {label}</div>
    </div>""", unsafe_allow_html=True)

    for chk, ok in data_checks.items():
        st.markdown(f"{'✅' if ok else '❌'} {chk}")

    st.markdown("---")
    st.markdown("""
    <div style='background:#1e2235;border:1px solid #2d3149;border-radius:12px;
    padding:48px;text-align:center;margin-top:24px;'>
        <div style='font-size:40px;margin-bottom:12px;'>🚧</div>
        <div style='font-size:18px;color:#e0e0e0;margin-bottom:8px;'>Auto-generated Issues</div>
        <div style='color:#8b9bb4;font-size:13px;'>Sẽ hiển thị sau khi có đầy đủ Shopify + GA4 + Meta Ads data.</div>
    </div>""", unsafe_allow_html=True)
