import pandas as pd
import streamlit as st
from utils import THB_TO_VND, get_roas_tier


def load_files(uploaded_files):
    all_campaigns, all_keywords = [], []
    for f in uploaded_files:
        try:
            xl = pd.ExcelFile(f)
            if "All Campaigns" in xl.sheet_names:
                df = pd.read_excel(f, sheet_name="All Campaigns")
                df["_source_file"] = f.name
                all_campaigns.append(df)
            if "Shop Ad - Keywords" in xl.sheet_names:
                dfk = pd.read_excel(f, sheet_name="Shop Ad - Keywords")
                dfk["_source_file"] = f.name
                all_keywords.append(dfk)
        except Exception as e:
            st.sidebar.warning(f"Lỗi đọc file {f.name}: {e}")
    df_camp = pd.concat(all_campaigns, ignore_index=True) if all_campaigns else pd.DataFrame()
    df_kw   = pd.concat(all_keywords,  ignore_index=True) if all_keywords  else pd.DataFrame()
    return df_camp, df_kw


def clean_campaigns(df):
    if df.empty:
        return df
    num_cols = ["Impression", "Clicks", "Expense", "GMV", "ROAS", "ACOS",
                "Items Sold", "Conversions", "Direct GMV", "Direct ROAS",
                "Direct ACOS", "Direct Items Sold"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in ["Expense", "GMV", "Direct GMV"]:
        if col in df.columns:
            df[f"{col}_VND"] = df[col] * THB_TO_VND
    if "CTR" in df.columns:
        df["CTR_pct"] = pd.to_numeric(
            df["CTR"].astype(str).str.replace("%", "").str.strip(), errors="coerce"
        ).fillna(0)
    if "ACOS" in df.columns:
        df["ACOS_pct"] = pd.to_numeric(
            df["ACOS"].astype(str).str.replace("%", "").str.strip(), errors="coerce"
        ).fillna(0)
    if "Campaign" in df.columns:
        df["Ad_Type"] = df["Campaign"].apply(
            lambda x: "Shop Ad" if "Shop Ad" in str(x) else "Product Ad"
        )
    if "ROAS" in df.columns:
        df["ROAS_Tier"]  = df["ROAS"].apply(lambda x: get_roas_tier(x)[0])
        df["ROAS_Color"] = df["ROAS"].apply(lambda x: get_roas_tier(x)[1])
    return df


def get_campaign_summary(df):
    if df.empty:
        return df
    agg = df.groupby("Campaign", as_index=False).agg(
        Ad_Type=("Ad_Type", "first"),
        Ad_Status=("Ad Status", "first"),
        Impressions=("Impression", "sum"),
        Clicks=("Clicks", "sum"),
        Expense_VND=("Expense_VND", "sum"),
        GMV_VND=("GMV_VND", "sum"),
        Items_Sold=("Items Sold", "sum"),
    )
    agg["ROAS"] = agg.apply(
        lambda r: r["GMV_VND"] / r["Expense_VND"] if r["Expense_VND"] > 0 else 0, axis=1
    )
    agg["CTR"] = agg.apply(
        lambda r: r["Clicks"] / r["Impressions"] * 100 if r["Impressions"] > 0 else 0, axis=1
    )
    agg["ACOS"] = agg.apply(
        lambda r: r["Expense_VND"] / r["GMV_VND"] * 100 if r["GMV_VND"] > 0 else 0, axis=1
    )
    agg["ROAS_Tier"]  = agg["ROAS"].apply(lambda x: get_roas_tier(x)[0])
    agg["ROAS_Color"] = agg["ROAS"].apply(lambda x: get_roas_tier(x)[1])
    return agg
