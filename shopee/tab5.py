import re
import os
import streamlit as st
from utils import fmt_vnd, fmt_num
from shopee.ai import generate_ai_insight


_AI_SECTION_CONFIGS = {
    "Vấn đề cần xử lý ngay": {"color": "#ff4444", "icon": "🔴", "bg": "#2a1a1a"},
    "Cơ hội tăng trưởng":    {"color": "#00ff88", "icon": "📈", "bg": "#0d2e1a"},
    "Khuyến nghị hành động": {"color": "#00d4ff", "icon": "🎯", "bg": "#0d1a2e"},
}


def render(df, df_camp, df_kw_raw, overall_roas, total_spend, total_gmv):
    st.markdown("## 📌 Summary Insight — Shopee")
    st.caption("Phân tích tự động dựa trên data hiện có. Cập nhật mỗi lần load.")

    # AI Insight
    st.markdown("## 🤖 AI Insight — Phân tích bởi Claude AI")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning("Chưa cấu hình ANTHROPIC_API_KEY. Thêm vào environment variable để bật tính năng AI Insight.", icon="⚠️")
    else:
        with st.spinner("Claude AI đang phân tích campaign data..."):
            try:
                ai_text = generate_ai_insight(df_camp, overall_roas, total_spend, total_gmv)
                for section_title, cfg in _AI_SECTION_CONFIGS.items():
                    pattern = re.compile(
                        rf"###\s*{re.escape(section_title)}\s*\n(.*?)(?=###|\Z)", re.DOTALL
                    )
                    match = pattern.search(ai_text)
                    content = match.group(1).strip() if match else ""
                    st.markdown(
                        f'<div style="background:{cfg["bg"]};border:1px solid {cfg["color"]};'
                        f'border-left:4px solid {cfg["color"]};border-radius:10px;'
                        f'padding:14px 18px 2px 18px;margin-top:14px;">'
                        f'<span style="color:{cfg["color"]};font-size:15px;font-weight:700;">'
                        f'{cfg["icon"]} {section_title}</span></div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div style="background:{cfg["bg"]};border:1px solid {cfg["color"]};'
                        f'border-left:4px solid {cfg["color"]};border-top:none;border-radius:0 0 10px 10px;'
                        f'padding:4px 18px 14px 18px;margin-bottom:4px;">'
                        f'<div style="color:#c8d8e8;font-size:13.5px;line-height:1.7;">'
                        + content.replace("\n", "<br>") + "</div></div>",
                        unsafe_allow_html=True,
                    )
            except Exception as e:
                st.error(f"Lỗi khi gọi Claude API: {e}")

    st.markdown("---")
    st.markdown("## 🔴 Vấn đề đang tồn tại")

    issues = []

    losing = df_camp[df_camp["ROAS"] < 1.0]
    if not losing.empty:
        issues.append({
            "severity": "🔴",
            "title": f"Lưu ý — {len(losing)} campaign(s) có ROAS < 1.0x — đang lỗ tiền quảng cáo",
            "detail": f"💸 Tổng spend đang lỗ: {fmt_vnd(losing['Expense_VND'].sum())} | Không có GMV hoặc ROAS âm",
            "reason": "💡 Nguyên nhân có thể: Targeting quá rộng, sản phẩm hết hàng, hoặc giá thầu quá cao",
            "color": "#ff4444",
        })

    shop_ads = df_camp[df_camp["Ad_Type"] == "Shop Ad"]
    if not shop_ads.empty and shop_ads["ROAS"].mean() < 2.0:
        issues.append({
            "severity": "🟡",
            "title": f"Cần chú ý — Shop Ads có ROAS trung bình {shop_ads['ROAS'].mean():.2f}x — kém hiệu quả so với Product Ads",
            "detail": f"💸 {len(shop_ads)} Shop Ad campaign(s) | Avg ROAS: {shop_ads['ROAS'].mean():.2f}x",
            "reason": "💡 Nguyên nhân có thể: Shop Ads targeting quá rộng, không đủ intent so với Product Ads",
            "color": "#ffd700",
        })

    acos_high = df_camp[df_camp["ACOS"] > 40]
    if not acos_high.empty:
        issues.append({
            "severity": "🟡",
            "title": f"Cần chú ý — {len(acos_high)} campaign(s) có ACOS > 40% — chi phí quảng cáo cao",
            "detail": f"💸 {', '.join(acos_high['Campaign'].tolist()[:3])}",
            "reason": "💡 Nguyên nhân có thể: Giá thầu cao, conversion rate thấp",
            "color": "#ffd700",
        })

    excellent = df_camp[df_camp["ROAS"] >= 5.0]
    if not excellent.empty:
        issues.append({
            "severity": "🟢",
            "title": f"Cơ hội — {len(excellent)} campaign(s) có ROAS ≥ 5.0x — đang under-invest",
            "detail": f"💰 {', '.join(excellent['Campaign'].tolist()[:3])} | ROAS xuất sắc nhưng budget chưa được tăng",
            "reason": "💡 Action: Tăng budget 30-50% để capture thêm GMV",
            "color": "#00ff88",
        })

    prod_df_check = df[df["Ad / Product Name"] != df["Campaign"]]
    low_ctr_prods = prod_df_check[
        (prod_df_check["Impression"] > prod_df_check["Impression"].median()) &
        (prod_df_check["CTR_pct"]   < prod_df_check["CTR_pct"].median())
    ]
    if not low_ctr_prods.empty:
        issues.append({
            "severity": "🟡",
            "title": f"Lưu ý — {len(low_ctr_prods)} sản phẩm có Impression cao nhưng CTR thấp",
            "detail": "💸 Đang waste impression budget — cần cải thiện thumbnail hoặc giá",
            "reason": "💡 Action: Update thumbnail/tiêu đề, test giá, hoặc dùng voucher để kéo CTR",
            "color": "#ffd700",
        })

    if not issues:
        st.markdown("""
        <div class="issue-card" style="border-left:3px solid #00ff88;background:#0d2e1a;">
            <div style="color:#00ff88;font-weight:700;">✅ Không phát hiện vấn đề nghiêm trọng trong kỳ này</div>
        </div>""", unsafe_allow_html=True)
    else:
        for issue in issues:
            st.markdown(f"""
            <div class="issue-card" style="border-left:4px solid {issue['color']};">
                <div class="issue-title" style="color:{issue['color']};">{issue['severity']} {issue['title']}</div>
                <div class="issue-detail">{issue['detail']}</div>
                <div class="issue-reason">{issue['reason']}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 📊 Data Quality Score — Kỳ này")

    checks = {
        "Shopee Ads: All Campaigns loaded":  not df_camp.empty,
        "Shopee Ads: ROAS column present":   "ROAS" in df.columns,
        "Shopee Ads: Product-level data":    len(df[df["Ad / Product Name"] != df["Campaign"]]) > 0,
        "Shopee Ads: Keyword data":          not df_kw_raw.empty,
        "Shopee Ads: CTR data available":    "CTR_pct" in df.columns,
        "Shopee Ads: GMV data available":    df["GMV_VND"].sum() > 0,
        "Shopee Insights: Daily GMV":        False,
        "Shopee Insights: Traffic Overview": False,
        "Shopee Insights: Orders data":      False,
        "Cross-channel: Shopify comparison": False,
    }

    score = sum(checks.values())
    total = len(checks)
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

    col1, col2 = st.columns(2)
    items = list(checks.items())
    half  = len(items) // 2
    for i, (check_name, passed) in enumerate(items):
        (col1 if i < half else col2).markdown(f"{'✅' if passed else '❌'} {check_name}")

    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>Data completeness: {score}/{total} ({pct:.0f}%)</li>
            <li>{len(issues)} vấn đề cần xử lý ({len([i for i in issues if '🔴' in i['severity']])} nghiêm trọng)</li>
            <li>Overall ROAS kỳ này: <b style="color:#00d4ff">{overall_roas:.2f}x</b></li>
        </ul>
    </div>""", unsafe_allow_html=True)
