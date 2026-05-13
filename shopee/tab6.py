import streamlit as st
from utils import fmt_vnd


def render(df_camp, overall_roas):
    st.markdown("## 🚀 Action Plan — Shopee Ads")
    st.markdown(
        f"**Overall ROAS hiện tại: <span style='color:#00d4ff;font-weight:700;font-size:18px;'>"
        f"{overall_roas:.2f}x</span>**",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🚀 Scale ngay")
        scale_camps = df_camp[df_camp["ROAS"] >= 5.0]
        if not scale_camps.empty:
            for _, r in scale_camps.iterrows():
                st.markdown(f"""
                <div class="issue-card" style="border-left:3px solid #00d4ff;">
                    <div class="issue-title" style="color:#00d4ff;">{r['Campaign']}</div>
                    <div class="issue-detail">
                        ROAS: <b style="color:#00ff88">{r['ROAS']:.2f}x</b> | Spend: {fmt_vnd(r['Expense_VND'])}<br>
                        GMV: {fmt_vnd(r['GMV_VND'])} | 👉 Tăng budget 30-50%
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            good_camps = df_camp[df_camp["ROAS"] >= 3.0]
            if not good_camps.empty:
                for _, r in good_camps.iterrows():
                    st.markdown(f"""
                    <div class="issue-card" style="border-left:3px solid #00ff88;">
                        <div class="issue-title" style="color:#00ff88;">{r['Campaign']}</div>
                        <div class="issue-detail">
                            ROAS: <b style="color:#00ff88">{r['ROAS']:.2f}x</b> | Spend: {fmt_vnd(r['Expense_VND'])}<br>
                            GMV: {fmt_vnd(r['GMV_VND'])} | 👉 Maintain hoặc tăng nhẹ 10-20%
                        </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("Chưa có campaign nào đạt ROAS ≥ 3.0x để scale.")

    with col2:
        st.markdown("### 🛑 Cần tối ưu / Pause")
        pause_camps = df_camp[df_camp["ROAS"] < 1.0]
        if not pause_camps.empty:
            for _, r in pause_camps.iterrows():
                st.markdown(f"""
                <div class="issue-card" style="border-left:3px solid #ff4444;">
                    <div class="issue-title" style="color:#ff4444;">{r['Campaign']}</div>
                    <div class="issue-detail">
                        ROAS: <b style="color:#ff4444">{r['ROAS']:.2f}x</b> | Spend: {fmt_vnd(r['Expense_VND'])}<br>
                        GMV: {fmt_vnd(r['GMV_VND'])} | ⛔ Review targeting & bid trước khi tiếp tục
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="issue-card" style="border-left:3px solid #00ff88;background:#0d2e1a;">
                <div style="color:#00ff88;font-weight:700;">✅ Tất cả campaigns active đều có ROAS > 1.0x</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Checklist Hành Động — Shopee Ads")

    st.markdown("#### Budget & Bidding")
    st.checkbox("Scale campaigns ROAS > 5x: tăng daily budget +30%")
    st.checkbox("Pause campaigns ROAS < 1.0x đang Ongoing")
    st.checkbox('Chuyển campaigns "GMV Max Auto" → "GMV Max Custom ROAS" với target ROAS = 3.0')
    st.checkbox("Review campaigns Paused có GMV tốt → reactivate với budget nhỏ hơn")

    st.markdown("#### Campaign Structure")
    st.checkbox("Tách riêng campaigns cho từng brand: CAOSTU, HIGHCHIC, FNOS, IAMSAIGON, PARADOX")
    st.checkbox("Tạo Clearance Sale campaign riêng cho sản phẩm tồn kho")
    st.checkbox("Thêm shop voucher vào campaigns có CTR cao để tăng conversion")

    st.markdown("#### Creative & Targeting")
    st.checkbox("Update creative cho campaigns CTR thấp nhất (so sánh trong dữ liệu thực tế)")
    st.checkbox("Test giá thầu cao hơn vào giờ peak (18:00–22:00 +7)")
    st.checkbox("Activate Discovery placement cho campaigns có Product CTR tốt")

    st.markdown("#### Measurement")
    st.checkbox("Export weekly performance report từ Shopee Seller Center")
    st.checkbox("So sánh Direct ROAS vs Total ROAS để đánh giá assisted conversions")
    st.checkbox("Monitor ACOS weekly — target ACOS < 30%")
