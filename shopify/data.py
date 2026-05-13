import io
import pandas as pd
import streamlit as st
from utils import get_roas_tier


@st.cache_data(show_spinner=False)
def read_csv_upload(data: bytes, **kwargs) -> pd.DataFrame:
    """Read CSV from uploaded file bytes (cache-safe)."""
    return pd.read_csv(io.BytesIO(data), **kwargs)


@st.cache_data(show_spinner=False)
def read_csv_path(path: str, **kwargs) -> pd.DataFrame:
    """Read CSV from local path (cache-safe)."""
    return pd.read_csv(path, **kwargs)


def load_csv(uploaded_file, fallback_path: str, **kwargs) -> tuple:
    """
    Return (df, source_label).
    Uses uploaded_file if provided, else fallback_path sample CSV.
    """
    if uploaded_file is not None:
        df = read_csv_upload(uploaded_file.getvalue(), **kwargs)
        return df, f"📤 {uploaded_file.name}"
    if fallback_path:
        import os
        if os.path.exists(fallback_path):
            df = read_csv_path(fallback_path, **kwargs)
            return df, "📊 Sample data"
    return pd.DataFrame(), "❌ Không có data"


def load_meta_ads(files):
    frames = []
    for f in files:
        try:
            df = pd.read_excel(f)
            df["_source_file"] = f.name
            frames.append(df)
        except Exception as e:
            st.sidebar.warning(f"Lỗi đọc file {f.name}: {e}")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# Columns that contain "spend" but are NOT the actual spend metric
_SPEND_EXCLUDE = {"spending limit", "spend limit", "budget", "daily budget"}


def _map_columns(df):
    """Return rename dict and a mapping_log for diagnostics."""
    rename = {}
    log = {}  # target → original col name

    # Pass 1: strict "amount spent" match (highest priority for Spend)
    for col in df.columns:
        cl = col.lower().strip()
        if "amount spent" in cl and "Spend" not in rename.values():
            rename[col] = "Spend"
            log["Spend"] = col

    for col in df.columns:
        cl = col.lower().strip()
        if col in rename:
            continue
        if "campaign name" in cl and "Campaign" not in rename.values():
            rename[col] = "Campaign";         log["Campaign"] = col
        elif ("ad name" in cl or "ad set name" in cl) and "Ad Name" not in rename.values():
            rename[col] = "Ad Name";          log["Ad Name"] = col
        # Spend fallback: only if no "amount spent" col found AND not a limit/budget col
        elif ("spend" in cl and "roas" not in cl
              and "Spend" not in rename.values()
              and not any(x in cl for x in _SPEND_EXCLUDE)):
            rename[col] = "Spend";            log["Spend"] = col
        elif "impression" in cl and "Impressions" not in rename.values():
            rename[col] = "Impressions";      log["Impressions"] = col
        elif "click" in cl and "ctr" not in cl and "Clicks" not in rename.values():
            rename[col] = "Clicks";           log["Clicks"] = col
        elif (cl == "ctr" or cl.startswith("ctr")) and "CTR" not in rename.values():
            rename[col] = "CTR";              log["CTR"] = col
        elif ("purchase roas" in cl or ("roas" in cl and "purchase" in cl)) and "ROAS" not in rename.values():
            rename[col] = "ROAS";             log["ROAS"] = col
        elif ("purchases conversion value" in cl or "purchase conversion value" in cl) and "Revenue" not in rename.values():
            rename[col] = "Revenue";          log["Revenue"] = col
        elif ("purchases" in cl and "roas" not in cl
              and "value" not in cl and "cart" not in cl
              and "Purchases" not in rename.values()):
            rename[col] = "Purchases";        log["Purchases"] = col
        elif "add" in cl and "cart" in cl and "Adds to Cart" not in rename.values():
            rename[col] = "Adds to Cart";     log["Adds to Cart"] = col

    return rename, log


def clean_meta_ads(df):
    if df.empty:
        return df

    rename, mapping_log = _map_columns(df)
    df = df.rename(columns=rename)

    # Remove any remaining duplicate column names (shouldn't happen now, but safety net)
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    # Parse numeric columns
    for col in ["Spend", "Impressions", "Clicks", "ROAS", "Revenue", "Purchases", "Adds to Cart"]:
        if col in df.columns:
            s = df[col]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            df[col] = pd.to_numeric(
                s.astype(str).str.replace(",", "").str.strip(), errors="coerce"
            ).fillna(0)

    if "CTR" in df.columns:
        s = df["CTR"]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        df["CTR"] = pd.to_numeric(
            s.astype(str).str.replace("%", "").str.replace(",", "").str.strip(),
            errors="coerce",
        ).fillna(0)

    # Fallback: compute ROAS where missing/zero
    if "Revenue" in df.columns and "Spend" in df.columns:
        mask = df.get("ROAS", pd.Series(0, index=df.index)) == 0
        df.loc[mask, "ROAS"] = df.loc[mask].apply(
            lambda r: r["Revenue"] / r["Spend"] if r["Spend"] > 0 else 0, axis=1
        )

    # Fallback: compute CTR where missing/zero
    if "Clicks" in df.columns and "Impressions" in df.columns:
        if "CTR" not in df.columns or df["CTR"].sum() == 0:
            df["CTR"] = df.apply(
                lambda r: r["Clicks"] / r["Impressions"] * 100 if r["Impressions"] > 0 else 0,
                axis=1,
            )

    # Drop total/summary rows and blank Campaign rows
    if "Campaign" in df.columns:
        df = df.dropna(subset=["Campaign"])
        df = df[~df["Campaign"].astype(str).str.lower().str.contains(
            r"total|grand|^\s*$", na=True, regex=True
        )]

    if "ROAS" not in df.columns:
        df["ROAS"] = 0
    df["ROAS_Tier"]  = df["ROAS"].apply(lambda x: get_roas_tier(x)[0])
    df["ROAS_Color"] = df["ROAS"].apply(lambda x: get_roas_tier(x)[1])

    # Attach mapping log for diagnostics
    df.attrs["mapping_log"] = mapping_log
    return df


def get_meta_campaign_summary(df):
    if df.empty or "Campaign" not in df.columns:
        return pd.DataFrame()
    sum_cols = {
        c: "sum"
        for c in ["Spend", "Impressions", "Clicks", "Revenue", "Purchases", "Adds to Cart"]
        if c in df.columns
    }
    agg = df.groupby("Campaign", as_index=False).agg(sum_cols)

    if "Revenue" in agg.columns and "Spend" in agg.columns:
        agg["ROAS"] = agg.apply(
            lambda r: r["Revenue"] / r["Spend"] if r["Spend"] > 0 else 0, axis=1
        )
    else:
        agg["ROAS"] = 0

    if "Clicks" in agg.columns and "Impressions" in agg.columns:
        agg["CTR"] = agg.apply(
            lambda r: r["Clicks"] / r["Impressions"] * 100 if r["Impressions"] > 0 else 0, axis=1
        )
    else:
        agg["CTR"] = 0

    agg["ROAS_Tier"]  = agg["ROAS"].apply(lambda x: get_roas_tier(x)[0])
    agg["ROAS_Color"] = agg["ROAS"].apply(lambda x: get_roas_tier(x)[1])
    return agg
