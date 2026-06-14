import streamlit as st
from utils import THB_TO_VND

st.set_page_config(
    page_title="VSTu Analytics Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0e1117; }
[data-testid="stSidebar"] { background-color: #1a1d27; border-right: 1px solid #2d3149; }
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
h1, h2, h3, h4, p, li, label { color: #e0e0e0 !important; }
[data-testid="metric-container"] {
    background-color: #1e2235; border: 1px solid #2d3149;
    border-radius: 8px; padding: 16px !important;
}
[data-testid="stMetricValue"] { color: #00d4ff !important; font-size: 28px !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #8b9bb4 !important; font-size: 13px !important; }
[data-testid="stMetricDelta"] { font-size: 13px !important; }
[data-testid="stTabs"] button {
    background-color: #1e2235 !important; color: #8b9bb4 !important;
    border-radius: 6px 6px 0 0 !important; font-size: 13px !important; padding: 8px 16px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    background-color: #00d4ff !important; color: #0e1117 !important; font-weight: 700 !important;
}
[data-testid="stDataFrame"] { border: 1px solid #2d3149; border-radius: 8px; }
.info-banner {
    background-color: #1a2744; border-left: 4px solid #00d4ff;
    padding: 10px 16px; border-radius: 0 6px 6px 0;
    margin-bottom: 16px; font-size: 13px; color: #b0c4de !important;
}
.kpi-card { background-color: #1e2235; border: 1px solid #2d3149; border-radius: 8px; padding: 16px 20px; margin-bottom: 8px; }
.kpi-label { color: #8b9bb4; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-value { color: #00d4ff; font-size: 26px; font-weight: 700; margin: 4px 0; }
.kpi-sub { color: #6b7a99; font-size: 12px; }
.issue-card { background-color: #1e2235; border: 1px solid #2d3149; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; }
.issue-title { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.issue-detail { color: #8b9bb4; font-size: 13px; }
.issue-reason { color: #6b7a99; font-size: 12px; font-style: italic; margin-top: 4px; }
.quick-insight { background-color: #1a2235; border: 1px solid #2d4a6b; border-radius: 8px; padding: 12px 16px; margin-top: 16px; }
.quick-insight-title { color: #00d4ff; font-size: 13px; font-weight: 700; margin-bottom: 8px; }
.section-header { font-size: 20px; font-weight: 700; color: #e0e0e0; margin: 24px 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #2d3149; }
[data-testid="stFileUploader"] { background-color: #1e2235; border: 1px dashed #3d4a6b; border-radius: 8px; padding: 8px; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #1e2235; }
::-webkit-scrollbar-thumb { background: #3d4a6b; border-radius: 3px; }
.stCheckbox label { color: #e0e0e0 !important; }
[data-testid="stSelectbox"] select { background-color: #1e2235; color: #e0e0e0; }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
uploaded_files         = []
meta_files             = []
tiktok_perf_files      = []
tiktok_gmvmax_files    = []
shopify_orders_file    = None
shopify_lineitems_file = None
shopify_customers_file = None

with st.sidebar:
    st.markdown("## 🛍️ VSTu Analytics")
    st.markdown("Digital Marketing Dashboard")
    st.markdown("---")
    platform = st.radio(
        "Nền tảng",
        ["🛍️ Shopee Report", "🛒 Shopify Report", "📱 TikTok Report"],
        label_visibility="collapsed",
    )
    st.markdown("---")

    if "Shopee" in platform:
        st.markdown("### 📂 Upload Shopee Ads Data")
        uploaded_files = st.file_uploader(
            "Shopee Ads Export (.xlsx)", type=["xlsx"], accept_multiple_files=True,
            help="Upload file export từ Shopee Ads. Có thể upload nhiều file cùng lúc (nhiều tháng).",
        )
        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} file đã tải:**")
            for f in uploaded_files:
                st.markdown(f"• {f.name}")
        st.markdown("---")
        st.markdown(f"**💱 Tỷ giá:** 1 THB = {THB_TO_VND:,} VNĐ")
        st.caption("Nguồn: Google")
    elif "TikTok" in platform:
        st.markdown("### 📊 Branding — TikTok Ads")
        tiktok_perf_files = st.file_uploader(
            "Raw TikTok Performance (.xlsx)", type=["xlsx"], accept_multiple_files=True,
            help="Export từ TikTok Ads Manager → Report. Cần: Campaign name, Cost, Impressions, Video views, Purchases (Shop), Gross revenue (Shop). Đơn vị THB — tự động × 830.",
            key="tt_perf",
        )
        if tiktok_perf_files:
            st.markdown(f"**{len(tiktok_perf_files)} file đã tải:**")
            for f in tiktok_perf_files:
                st.markdown(f"• {f.name}")

        st.markdown("---")
        st.markdown("### 📦 GMV Max")
        tiktok_gmvmax_files = st.file_uploader(
            "Raw Data GMV Max (.xlsx)", type=["xlsx"], accept_multiple_files=True,
            help="Export TikTok Shop Sales (SPU level). Cần: SPU name, Campaign name, Purchases (Shop), Gross revenue (Shop). Đơn vị THB — tự động × 830.",
            key="tt_gmvmax",
        )
        if tiktok_gmvmax_files:
            st.markdown(f"**{len(tiktok_gmvmax_files)} file đã tải:**")
            for f in tiktok_gmvmax_files:
                st.markdown(f"• {f.name}")

        st.markdown("---")
        st.markdown(f"**💱 Tỷ giá:** 1 THB = {THB_TO_VND:,} VNĐ")
        st.caption("Tất cả giá trị TikTok đều THB → tự động quy đổi VNĐ")
    else:
        st.markdown("### 📂 Shopify Data")

        shopify_orders_file    = st.file_uploader(
            "Orders (.csv)",
            type=["csv"],
            help="Shopify Admin → Orders → Export. Cần cột: Name, Created at, Financial Status, Fulfillment Status, Total, Subtotal, Email.",
            key="sf_orders",
        )
        shopify_lineitems_file = st.file_uploader(
            "Line Items / Products (.csv)",
            type=["csv"],
            help="Shopify export có line items. Cần cột: Order Name, Created at, Financial Status, Brand, Product, SKU, Quantity, Unit Price, Discount, Line Total.",
            key="sf_lineitems",
        )
        shopify_customers_file = st.file_uploader(
            "Customers (.csv)",
            type=["csv"],
            help="Shopify Admin → Customers → Export. Cần cột: Order Name, Created at, Email, Customer Name, Province, District, Total, Financial Status, Is New Customer.",
            key="sf_customers",
        )

        uploaded_shopify = [f for f in [shopify_orders_file, shopify_lineitems_file, shopify_customers_file] if f]
        if uploaded_shopify:
            st.caption(f"✅ {len(uploaded_shopify)}/3 file đã tải")
        else:
            st.caption("Chưa upload — đang dùng sample data")

        st.markdown("---")
        st.markdown("### 📂 Meta Ads")
        meta_files = st.file_uploader(
            "Meta Ads Export (.xlsx)", type=["xlsx"], accept_multiple_files=True,
            help="Cần các cột: Campaign name, Ad name, Amount spent VND, Impressions, Clicks, CTR, Purchases, Purchase ROAS, Purchases conversion value, Adds to cart.",
        )
        if meta_files:
            st.markdown(f"**{len(meta_files)} file đã tải:**")
            for f in meta_files:
                st.markdown(f"• {f.name}")
        st.markdown("---")
        st.markdown("**💱 Currency:** VNĐ")
        st.caption("Shopify + Meta Ads Analytics")


# ─── SHOPIFY REPORT ───────────────────────────────────────────────────────────
if "Shopify" in platform:
    import shopify.tab1 as sf_tab1
    import shopify.tab2 as sf_tab2
    import shopify.tab3 as sf_tab3
    import shopify.tab5 as sf_tab5
    import shopify.tab6 as sf_tab6
    import shopify.tab7 as sf_tab7

    st.markdown("# 🛒 Report — Shopify Analytics")
    st.markdown("**VSTu Digital Marketing Analytics** | Shopify Store Performance")

    def _placeholder(label, note):
        st.markdown(f"""
        <div style='background:#1e2235;border:1px solid #2d3149;border-radius:12px;
        padding:48px;text-align:center;margin-top:24px;'>
            <div style='font-size:40px;margin-bottom:12px;'>🚧</div>
            <div style='font-size:18px;color:#e0e0e0;margin-bottom:8px;'>{label}</div>
            <div style='color:#8b9bb4;font-size:13px;'>{note}</div>
        </div>""", unsafe_allow_html=True)

    sf1, sf2, sf3, sf4, sf5, sf6, sf7 = st.tabs([
        "🏥 Business Health", "🏷️ Brand & Product", "🌍 Customer & Geography",
        "📡 Traffic Overview", "📢 Paid Campaign", "🔍 Campaign Audit", "📌 Summary Insight",
    ])
    with sf1:
        sf_tab1.render(shopify_orders_file)
    with sf2:
        sf_tab2.render(shopify_lineitems_file)
    with sf3:
        sf_tab3.render(shopify_customers_file)
    with sf4:
        st.markdown("## 📡 Traffic Overview")
        st.caption("Sessions, paid vs organic, source/medium breakdown, revenue by channel")
        _placeholder("Traffic Overview", "Cần kết nối GA4 export")
    with sf5:
        sf_tab5.render(meta_files)
    with sf6:
        sf_tab6.render(meta_files)
    with sf7:
        sf_tab7.render(meta_files)

    st.stop()


# ─── TIKTOK REPORT ────────────────────────────────────────────────────────────
if "TikTok" in platform:
    import pandas as pd
    import tiktok.tab1 as tt_tab1
    import tiktok.tab2 as tt_tab2
    import tiktok.tab3 as tt_tab3
    import tiktok.tab4 as tt_tab4
    from tiktok.data import load_perf_files, get_camp_summary, load_gmvmax_files

    st.markdown("# 📱 Report — TikTok Ads Analytics")
    st.markdown("**VSTu Digital Marketing Analytics** | TikTok Ads Performance")

    if not tiktok_perf_files and not tiktok_gmvmax_files:
        st.markdown("""
        <div style='background:#1e2235;border:1px solid #2d3149;border-radius:12px;padding:48px;text-align:center;margin-top:32px;'>
            <div style='font-size:48px;margin-bottom:16px;'>📱</div>
            <div style='font-size:20px;color:#e0e0e0;margin-bottom:8px;'>Chưa có data</div>
            <div style='color:#8b9bb4;font-size:14px;'>Upload file TikTok Ads Performance (Branding) hoặc GMV Max ở sidebar bên trái</div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    with st.spinner("Đang đọc data..."):
        df_tt      = load_perf_files(tiktok_perf_files) if tiktok_perf_files else pd.DataFrame()
        df_tt_camp = get_camp_summary(df_tt)
        df_gmvmax  = load_gmvmax_files(tiktok_gmvmax_files) if tiktok_gmvmax_files else pd.DataFrame()

    file_info = []
    if tiktok_perf_files:
        file_info.append(f"{len(tiktok_perf_files)} file Branding")
    if tiktok_gmvmax_files:
        file_info.append(f"{len(tiktok_gmvmax_files)} file GMV Max")
    st.markdown(
        f'<div class="info-banner">💱 1 THB = {THB_TO_VND:,} VNĐ &nbsp;|&nbsp; '
        f'Tất cả giá trị TikTok đã quy đổi THB → VNĐ &nbsp;|&nbsp; '
        f'{" | ".join(file_info)}</div>',
        unsafe_allow_html=True,
    )

    # 2 subtab chính: Branding và GMV Max
    tt_branding, tt_gmvmax = st.tabs(["📊 Branding", "📦 GMV Max"])

    with tt_branding:
        if df_tt.empty:
            st.markdown("""
            <div style='background:#1e2235;border:1px solid #2d3149;border-radius:12px;
            padding:40px;text-align:center;margin-top:16px;'>
                <div style='font-size:36px;margin-bottom:10px;'>📊</div>
                <div style='font-size:16px;color:#e0e0e0;'>Upload file TikTok Ads Performance ở sidebar để xem Branding report</div>
            </div>""", unsafe_allow_html=True)
        else:
            b1, b2, b3 = st.tabs([
                "🏥 Business Health", "🎬 Video Performance", "🛒 Shop Performance"
            ])
            with b1: tt_tab1.render(df_tt, df_tt_camp)
            with b2: tt_tab2.render(df_tt, df_tt_camp)
            with b3: tt_tab3.render(df_tt, df_tt_camp)

    with tt_gmvmax:
        tt_tab4.render(df_gmvmax)

    st.stop()


# ─── SHOPEE REPORT ────────────────────────────────────────────────────────────
import shopee.tab1 as s_tab1
import shopee.tab2 as s_tab2
import shopee.tab3 as s_tab3
import shopee.tab4 as s_tab4
import shopee.tab5 as s_tab5
import shopee.tab6 as s_tab6
from shopee.data import load_files, clean_campaigns, get_campaign_summary

st.markdown("# 🛍️ Report — Shopee Analytics")
st.markdown("**VSTu Digital Marketing Analytics** | Shopee Ads Performance")

if not uploaded_files:
    st.markdown("""
    <div style='background:#1e2235;border:1px solid #2d3149;border-radius:12px;padding:48px;text-align:center;margin-top:32px;'>
        <div style='font-size:48px;margin-bottom:16px;'>📂</div>
        <div style='font-size:20px;color:#e0e0e0;margin-bottom:8px;'>Chưa có data</div>
        <div style='color:#8b9bb4;font-size:14px;'>Upload file Shopee Ads export (.xlsx) ở sidebar bên trái để bắt đầu</div>
        <div style='color:#6b7a99;font-size:13px;margin-top:12px;'>Có thể upload nhiều file cùng lúc để xem dữ liệu tổng hợp nhiều tháng</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

with st.spinner("Đang đọc data..."):
    df_raw, df_kw_raw = load_files(uploaded_files)
    df      = clean_campaigns(df_raw.copy())
    df_camp = get_campaign_summary(df)

total_spend  = df["Expense_VND"].sum()
total_gmv    = df["GMV_VND"].sum()
overall_roas = total_gmv / total_spend if total_spend > 0 else 0

st.markdown(
    f'<div class="info-banner">💱 Tỷ giá quy đổi: 1 THB = {THB_TO_VND:,} VNĐ &nbsp;|&nbsp; '
    f'Shopee Ads Expense/GMV: THB → VNĐ &nbsp;|&nbsp; {len(uploaded_files)} file đã tải</div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏥 Business Health", "🏷️ Brand & Product", "📊 Onsite Ads Performance",
    "🔍 Campaign Setup Audit", "📌 Summary Insight", "🚀 Action Plan",
])

with tab1: s_tab1.render(df, df_camp)
with tab2: s_tab2.render(df)
with tab3: s_tab3.render(df, df_camp)
with tab4: s_tab4.render(df_camp)
with tab5: s_tab5.render(df, df_camp, df_kw_raw, overall_roas, total_spend, total_gmv)
with tab6: s_tab6.render(df_camp, overall_roas)
