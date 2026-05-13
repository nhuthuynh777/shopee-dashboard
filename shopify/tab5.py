import streamlit as st
import plotly.graph_objects as go
from utils import fmt_vnd, fmt_num, _ly, _hbar, styled_table, ROAS_TIERS
from shopify.data import load_meta_ads, clean_meta_ads, get_meta_campaign_summary


def render(meta_files):
    st.markdown("## 📢 Paid Campaign Performance — Meta Ads")

    if not meta_files:
        st.markdown("""
        <div style='background:#1e2235;border:1px solid #2d3149;border-radius:12px;
        padding:48px;text-align:center;margin-top:24px;'>
            <div style='font-size:40px;margin-bottom:12px;'>📂</div>
            <div style='font-size:20px;color:#e0e0e0;margin-bottom:8px;'>Chưa có data Meta Ads</div>
            <div style='color:#8b9bb4;font-size:14px;'>Upload file Meta Ads export (.xlsx) ở sidebar bên trái để bắt đầu</div>
            <div style='color:#6b7a99;font-size:13px;margin-top:12px;'>
                Cần có các cột: Campaign name · Ad name · Amount spent VND · Impressions · Clicks · CTR ·
                Purchases · Purchase ROAS · Purchases conversion value · Adds to cart
            </div>
        </div>""", unsafe_allow_html=True)
        return

    with st.spinner("Đang đọc Meta Ads data..."):
        df_raw = load_meta_ads(meta_files)
        df     = clean_meta_ads(df_raw.copy())
        df_mc  = get_meta_campaign_summary(df)

    if df.empty or "Campaign" not in df.columns:
        st.error("Không đọc được dữ liệu hợp lệ từ file. Kiểm tra lại tên cột.")
        return

    mapping_log = df.attrs.get("mapping_log", {})

    st.markdown(
        f'<div class="info-banner">📁 {len(meta_files)} file | {len(df_mc)} campaigns | '
        f'{len(df_raw)} rows raw → {len(df)} rows sau filter | Currency: VNĐ</div>',
        unsafe_allow_html=True,
    )

    # ── Diagnostic expander ──────────────────────────────────────────────────
    with st.expander("🔍 Data Diagnostic — so sánh với Excel gốc", expanded=False):
        st.markdown("#### Column Mapping")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Cột được map từ file gốc:**")
            for target, source in mapping_log.items():
                st.markdown(f"- `{target}` ← **{source}**")
            unmapped = [c for c in df_raw.columns if c not in mapping_log.values()]
            if unmapped:
                st.markdown(f"**Cột không được map ({len(unmapped)}):**")
                st.caption(" · ".join(unmapped))
        with col_b:
            st.markdown("**Raw totals (trực tiếp từ file, trước filter):**")
            if "Spend" in mapping_log:
                raw_spend_col = mapping_log["Spend"]
                if raw_spend_col in df_raw.columns:
                    import pandas as _pd
                    raw_s = _pd.to_numeric(
                        df_raw[raw_spend_col].astype(str).str.replace(",", "").str.strip(),
                        errors="coerce"
                    ).fillna(0)
                    st.markdown(f"- **Amount Spent** (raw sum): `{raw_s.sum():,.0f}`")
                    st.markdown(f"- **Amount Spent** (sau filter): `{df['Spend'].sum():,.0f}`")
                    st.markdown(f"- **Amount Spent** (sau groupby): `{df_mc['Spend'].sum() if 'Spend' in df_mc.columns else 0:,.0f}`")
            if "Revenue" in mapping_log:
                raw_rev_col = mapping_log["Revenue"]
                if raw_rev_col in df_raw.columns:
                    import pandas as _pd
                    raw_r = _pd.to_numeric(
                        df_raw[raw_rev_col].astype(str).str.replace(",", "").str.strip(),
                        errors="coerce"
                    ).fillna(0)
                    st.markdown(f"- **Conv. Value** (raw sum): `{raw_r.sum():,.0f}`")
                    st.markdown(f"- **Conv. Value** (sau groupby): `{df_mc['Revenue'].sum() if 'Revenue' in df_mc.columns else 0:,.0f}`")

        st.markdown("#### Row Count")
        st.markdown(f"- Raw rows (kể cả total/header): **{len(df_raw)}**")
        st.markdown(f"- Sau khi drop 'Total' rows & blank Campaign: **{len(df)}**")
        st.markdown(f"- Campaigns unique (sau groupby): **{len(df_mc)}**")

        if len(df) > 0 and "Campaign" in df.columns:
            rows_per_camp = df.groupby("Campaign").size()
            if rows_per_camp.max() > 1:
                st.warning(
                    f"⚠️ Có campaign với **nhiều hơn 1 row** (max = {rows_per_camp.max()} rows). "
                    f"File có thể export ở ad-level hoặc ad set-level — SUM theo campaign là đúng. "
                    f"Nếu file có cả campaign-level lẫn ad-level thì bị double-count.",
                    icon="⚠️",
                )
                st.dataframe(
                    rows_per_camp.reset_index().rename(columns={0: "# rows"}),
                    hide_index=True,
                )

    # KPI row
    total_spend  = df_mc["Spend"].sum()      if "Spend"      in df_mc.columns else 0
    total_rev    = df_mc["Revenue"].sum()    if "Revenue"    in df_mc.columns else 0
    total_pur    = df_mc["Purchases"].sum()  if "Purchases"  in df_mc.columns else 0
    total_imp    = df_mc["Impressions"].sum() if "Impressions" in df_mc.columns else 0
    overall_roas = total_rev / total_spend   if total_spend > 0 else 0
    avg_ctr      = df_mc["Clicks"].sum() / total_imp * 100 if total_imp > 0 and "Clicks" in df_mc.columns else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Spend",           fmt_vnd(total_spend))
    m2.metric("Revenue (Conv. Value)", fmt_vnd(total_rev))
    m3.metric("Overall ROAS",          f"{overall_roas:.2f}x")
    m4.metric("Purchases",             fmt_num(total_pur))
    m5.metric("Avg CTR",               f"{avg_ctr:.2f}%")

    st.markdown("---")

    # Campaign table
    st.markdown("### Campaign Performance Table")
    tbl_cols = [c for c in ["Campaign", "Spend", "Impressions", "Clicks", "CTR",
                              "Purchases", "Revenue", "ROAS", "Adds to Cart", "ROAS_Tier"]
                if c in df_mc.columns]
    tbl = df_mc[tbl_cols].copy().sort_values("ROAS", ascending=False)
    if "Spend"        in tbl.columns: tbl["Spend"]        = tbl["Spend"].apply(fmt_vnd)
    if "Revenue"      in tbl.columns: tbl["Revenue"]      = tbl["Revenue"].apply(fmt_vnd)
    if "ROAS"         in tbl.columns: tbl["ROAS"]         = tbl["ROAS"].apply(lambda x: f"{x:.2f}x")
    if "CTR"          in tbl.columns: tbl["CTR"]          = tbl["CTR"].apply(lambda x: f"{x:.2f}%")
    if "Impressions"  in tbl.columns: tbl["Impressions"]  = tbl["Impressions"].apply(fmt_num)
    if "Clicks"       in tbl.columns: tbl["Clicks"]       = tbl["Clicks"].apply(fmt_num)
    if "Purchases"    in tbl.columns: tbl["Purchases"]    = tbl["Purchases"].apply(fmt_num)
    if "Adds to Cart" in tbl.columns: tbl["Adds to Cart"] = tbl["Adds to Cart"].apply(fmt_num)
    if "Revenue"      in tbl.columns: tbl = tbl.rename(columns={"Revenue": "Revenue (Meta)"})
    st.markdown(styled_table(tbl), unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    # ROAS chart
    with col1:
        st.markdown("### ROAS by Campaign")
        roas_sorted = df_mc[df_mc["ROAS"] > 0].sort_values("ROAS", ascending=True)
        if not roas_sorted.empty:
            fig = _hbar(
                y=roas_sorted["Campaign"], x=roas_sorted["ROAS"],
                colors=roas_sorted["ROAS_Color"].tolist(),
                texts=[f"{v:.2f}x" for v in roas_sorted["ROAS"]],
                xaxis_title="ROAS",
            )
            fig.add_vline(x=3.0, line_dash="dash", line_color="#00ff88",
                          annotation_text="3.0x", annotation_font_color="#00ff88",
                          annotation_position="top right")
            fig.add_vline(x=1.0, line_dash="dash", line_color="#ff4444",
                          annotation_text="1.0x", annotation_font_color="#ff4444",
                          annotation_position="top right")
            st.plotly_chart(fig, use_container_width=True, key="sf5_roas")

    # CTR chart
    with col2:
        st.markdown("### CTR by Campaign")
        ctr_sorted = df_mc[df_mc["CTR"] > 0].sort_values("CTR", ascending=True)
        if not ctr_sorted.empty:
            med_ctr = ctr_sorted["CTR"].median()
            ctr_colors = ["#ff4444" if v < med_ctr else "#00d4ff" for v in ctr_sorted["CTR"]]
            fig = _hbar(
                y=ctr_sorted["Campaign"], x=ctr_sorted["CTR"],
                colors=ctr_colors,
                texts=[f"{v:.2f}%" for v in ctr_sorted["CTR"]],
                xaxis_title="CTR (%)",
            )
            fig.add_vline(x=med_ctr, line_dash="dash", line_color="#ffd700",
                          annotation_text=f"Median {med_ctr:.2f}%",
                          annotation_font_color="#ffd700", annotation_position="top right")
            st.plotly_chart(fig, use_container_width=True, key="sf5_ctr")

    # Bubble chart
    st.markdown("### Spend vs Revenue — bubble size = ROAS")
    bubble = df_mc[df_mc.get("Spend", 0) > 0] if "Spend" in df_mc.columns else df_mc.head(0)
    if not bubble.empty and "Revenue" in bubble.columns:
        max_roas   = max(bubble["ROAS"].max(), 1)
        tier_colors = {t[0]: t[1] for t in ROAS_TIERS}
        fig = go.Figure()
        for tier, color in tier_colors.items():
            sub = bubble[bubble["ROAS_Tier"] == tier]
            if not sub.empty:
                sz = (sub["ROAS"] / max_roas * 35 + 8).clip(8, 45)
                fig.add_trace(go.Scatter(
                    x=sub["Spend"], y=sub["Revenue"],
                    mode="markers", name=tier,
                    marker=dict(size=sz.tolist(), color=color, opacity=0.85,
                                line=dict(color="#1e2235", width=0.5)),
                    text=sub["Campaign"].str[:35],
                    hovertemplate="<b>%{text}</b><br>Spend: %{x:,.0f} ₫<br>Revenue: %{y:,.0f} ₫<extra></extra>",
                ))
        fig.update_layout(**_ly(xaxis_title="Spend (VNĐ)", yaxis_title="Revenue (VNĐ)"))
        st.plotly_chart(fig, use_container_width=True, key="sf5_bubble")

    # Daily trend placeholder
    st.markdown("### Daily Trend")
    st.markdown("""
    <div class="info-banner">
        ℹ️ Daily trend cần file export theo ngày từ Meta Ads Manager.
        Upload thêm file breakdown by day để hiển thị chart này.
    </div>""", unsafe_allow_html=True)

    # Quick insight
    losing  = df_mc[df_mc["ROAS"] < 1.0] if "ROAS" in df_mc.columns else df_mc.head(0)
    best    = df_mc.loc[df_mc["ROAS"].idxmax()] if not df_mc.empty else None
    st.markdown(f"""
    <div class="quick-insight">
        <div class="quick-insight-title">⚡ QUICK INSIGHT</div>
        <ul style="color:#b0c4de;font-size:13px;margin:0;padding-left:20px;">
            <li>Overall ROAS: <b style="color:#00d4ff">{overall_roas:.2f}x</b> |
                Total Spend: <b>{fmt_vnd(total_spend)}</b> |
                Revenue: <b>{fmt_vnd(total_rev)}</b></li>
            {"<li>Campaign ROAS cao nhất: <b style='color:#00ff88'>" + str(best['Campaign']) + f"</b> — {best['ROAS']:.2f}x</li>" if best is not None else ""}
            <li>Campaigns ROAS &lt; 1.0: <b style="color:#ff4444">{len(losing)}</b> — cần review hoặc pause</li>
        </ul>
    </div>""", unsafe_allow_html=True)
