import pandas as pd
from utils import THB_TO_VND


def _get(df, aliases, default=0):
    for c in aliases:
        if c in df.columns:
            return pd.to_numeric(df[c], errors='coerce').fillna(default)
    return pd.Series(default, index=df.index)


def _detect_currency(df):
    if 'Currency' not in df.columns:
        return False
    return df['Currency'].astype(str).str.upper().eq('THB').any()


_BAD_SHEETS = {'pivot table', 'overall', 'natufres overal', 'natufres overall', 'sheet5'}


def _best_sheet(xl):
    for s in xl.sheet_names:
        if s.lower() not in _BAD_SHEETS and 'pivot' not in s.lower():
            return s
    return xl.sheet_names[0]


# ── Performance report (campaign/adgroup level with video metrics) ─────────────

def load_perf_files(files):
    frames = []
    for f in files:
        try:
            xl = pd.ExcelFile(f)
            df = pd.read_excel(f, sheet_name=_best_sheet(xl))
            if 'Campaign name' in df.columns or 'Cost' in df.columns:
                frames.append(df)
        except Exception:
            pass
    if not frames:
        return pd.DataFrame()
    return clean_perf(pd.concat(frames, ignore_index=True))


def clean_perf(raw):
    is_thb = _detect_currency(raw)
    rate = THB_TO_VND if is_thb else 1

    # Drop TikTok-generated summary rows (e.g. "Total of N results")
    if 'Campaign name' in raw.columns:
        raw = raw[~raw['Campaign name'].astype(str).str.match(r'^Total of \d+')]

    df = pd.DataFrame()
    df['Campaign']     = raw['Campaign name'].fillna('').astype(str) if 'Campaign name' in raw.columns else pd.Series('', index=raw.index)
    df['Adgroup']      = raw['Ad group name'].fillna('').astype(str) if 'Ad group name' in raw.columns else pd.Series('', index=raw.index)
    df['Currency_raw'] = raw['Currency'].astype(str) if 'Currency' in raw.columns else pd.Series('VND', index=raw.index)

    if 'By Day' in raw.columns:
        df['Date'] = pd.to_datetime(raw['By Day'], errors='coerce')
    else:
        df['Date'] = pd.NaT

    # Spend
    df['Cost_VND']   = _get(raw, ['Cost']) * rate

    # Audience
    df['Impressions'] = _get(raw, ['Impressions'])
    df['Reach']       = _get(raw, ['Reach'])
    df['Clicks']      = _get(raw, ['Clicks (destination)', 'Clicks (all)'])

    # Video funnel
    df['Video_6s']    = _get(raw, ['6-second video views', '6-second focused views'])
    df['Video_25']    = _get(raw, ['Video views at 25%'])
    df['Video_50']    = _get(raw, ['Video views at 50%'])
    df['Video_75']    = _get(raw, ['Video views at 75%'])
    df['Video_100']   = _get(raw, ['Video views at 100%'])
    df['AvgPlayTime'] = _get(raw, ['Average play time per video view'])

    # Engagement
    df['Paid_Follows']  = _get(raw, ['Paid follows'])
    df['Paid_Likes']    = _get(raw, ['Paid likes'])
    df['Paid_Comments'] = _get(raw, ['Paid comments'])
    df['Paid_Shares']   = _get(raw, ['Paid shares'])
    df['Paid_Profile']  = _get(raw, ['Paid profile visits'])

    # Shop
    df['Purchases']        = _get(raw, ['Purchases (Shop)'])
    df['ATC']              = _get(raw, ['Adds to cart (Shop)'])
    df['ATC_Val_VND']      = _get(raw, ['Add to cart value (Shop)']) * rate
    df['GMV_VND']          = _get(raw, ['Gross revenue (Shop)']) * rate
    df['Checkouts']        = _get(raw, ['Checkouts initiated (Shop)'])
    df['Checkout_Val_VND'] = _get(raw, ['Checkout initiation value (Shop)']) * rate
    df['Product_Views']    = _get(raw, ['Product page views (Shop)'])

    # Derived
    df['ROAS'] = df.apply(
        lambda r: r['GMV_VND'] / r['Cost_VND'] if r['Cost_VND'] > 0 else 0, axis=1)
    df['CTR'] = df.apply(
        lambda r: r['Clicks'] / r['Impressions'] * 100 if r['Impressions'] > 0 else 0, axis=1)

    return df


def get_camp_summary(df):
    if df.empty:
        return pd.DataFrame()
    g = df.groupby('Campaign', as_index=False).agg(
        Cost_VND=('Cost_VND', 'sum'),
        GMV_VND=('GMV_VND', 'sum'),
        Impressions=('Impressions', 'sum'),
        Reach=('Reach', 'sum'),
        Clicks=('Clicks', 'sum'),
        Video_6s=('Video_6s', 'sum'),
        Video_25=('Video_25', 'sum'),
        Video_50=('Video_50', 'sum'),
        Video_75=('Video_75', 'sum'),
        Video_100=('Video_100', 'sum'),
        AvgPlayTime=('AvgPlayTime', 'mean'),
        Purchases=('Purchases', 'sum'),
        ATC=('ATC', 'sum'),
        Checkouts=('Checkouts', 'sum'),
        Paid_Likes=('Paid_Likes', 'sum'),
        Paid_Comments=('Paid_Comments', 'sum'),
        Paid_Shares=('Paid_Shares', 'sum'),
        Paid_Follows=('Paid_Follows', 'sum'),
    )
    g['ROAS'] = g.apply(
        lambda r: r['GMV_VND'] / r['Cost_VND'] if r['Cost_VND'] > 0 else 0, axis=1)
    g['CTR'] = g.apply(
        lambda r: r['Clicks'] / r['Impressions'] * 100 if r['Impressions'] > 0 else 0, axis=1)

    from utils import get_roas_tier
    tier_info = g['ROAS'].apply(get_roas_tier)
    g['ROAS_Tier']  = tier_info.apply(lambda x: x[0])
    g['ROAS_Color'] = tier_info.apply(lambda x: x[1])
    return g


# ── GMV Max / TikTok Shop Sales report ────────────────────────────────────────

def load_gmvmax_files(files):
    frames = []
    for f in files:
        try:
            xl = pd.ExcelFile(f)
            df = pd.read_excel(f, sheet_name=xl.sheet_names[0])
            if 'Gross revenue (Shop)' in df.columns or 'SPU name' in df.columns:
                frames.append(df)
        except Exception:
            pass
    if not frames:
        return pd.DataFrame()
    return clean_gmvmax(pd.concat(frames, ignore_index=True))


def clean_gmvmax(raw):
    is_thb = _detect_currency(raw)
    rate = THB_TO_VND if is_thb else 1

    df = pd.DataFrame()
    df['Account']   = raw['Account name'].fillna('').astype(str) if 'Account name' in raw.columns else pd.Series('', index=raw.index)
    df['Campaign']  = raw['Campaign name'].fillna('').astype(str) if 'Campaign name' in raw.columns else pd.Series('', index=raw.index)
    df['Brand']     = (raw.get('brand', raw.get('Brand', pd.Series('', index=raw.index)))).fillna('').astype(str)
    df['Product']   = raw['SPU name'].fillna('Unknown').astype(str) if 'SPU name' in raw.columns else pd.Series('Unknown', index=raw.index)
    df['Purchases'] = _get(raw, ['Purchases (Shop)'])
    df['GMV_VND']   = _get(raw, ['Gross revenue (Shop)']) * rate
    df['AOV_VND']   = _get(raw, ['Average order value (Shop)']) * rate
    df['Items']     = _get(raw, ['Items purchased (Shop)', 'Items purchased (TikTok Shop)'])
    df['Currency_raw'] = raw['Currency'].astype(str) if 'Currency' in raw.columns else pd.Series('VND', index=raw.index)
    return df
