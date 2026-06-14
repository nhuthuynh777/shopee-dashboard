"""
Run: python3 debug_meta.py <path-to-meta-ads.xlsx>
"""
import sys
import pandas as pd

path = sys.argv[1] if len(sys.argv) > 1 else None
if not path:
    print("Usage: python3 debug_meta.py <path-to-file.xlsx>")
    sys.exit(1)

df = pd.read_excel(path)

print(f"\n{'='*60}")
print(f"FILE: {path}")
print(f"{'='*60}")
print(f"Rows (bao gồm cả header nếu có):  {len(df)}")
print(f"Columns ({len(df.columns)}):")
for i, col in enumerate(df.columns):
    print(f"  [{i:02d}] '{col}'")

print(f"\n{'='*60}")
print("RAW SUMS (không lọc, không rename)")
print(f"{'='*60}")

# Tìm cột amount spent
for col in df.columns:
    cl = col.lower().strip()
    if "amount spent" in cl or ("spend" in cl and "roas" not in cl):
        raw = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
        print(f"Amount Spent  → '{col}'")
        print(f"  sum (raw)   = {raw.sum():,.0f}")
        print(f"  non-null    = {raw.notna().sum()} / {len(df)} rows")
        print(f"  sample (5)  = {raw.dropna().head(5).tolist()}")

print()

# Tìm cột purchases conversion value
for col in df.columns:
    cl = col.lower().strip()
    if "purchases conversion value" in cl or ("conversion value" in cl):
        raw = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
        print(f"Conv. Value   → '{col}'")
        print(f"  sum (raw)   = {raw.sum():,.0f}")
        print(f"  non-null    = {raw.notna().sum()} / {len(df)} rows")
        print(f"  sample (5)  = {raw.dropna().head(5).tolist()}")

print()

# Tìm cột purchases
for col in df.columns:
    cl = col.lower().strip()
    if "purchases" in cl and "roas" not in cl and "value" not in cl and "cart" not in cl:
        raw = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
        print(f"Purchases     → '{col}'")
        print(f"  sum (raw)   = {raw.sum():,.0f}")
        print(f"  non-null    = {raw.notna().sum()} / {len(df)} rows")

print()

# Tìm cột Purchase ROAS
for col in df.columns:
    cl = col.lower().strip()
    if "purchase roas" in cl or ("roas" in cl and "purchase" in cl):
        raw = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
        print(f"Purchase ROAS → '{col}'")
        print(f"  mean (raw)  = {raw.mean():.2f}")
        print(f"  sample (5)  = {raw.dropna().head(5).tolist()}")

print()

# Tìm cột campaign
for col in df.columns:
    if "campaign name" in col.lower():
        print(f"Campaign      → '{col}'")
        print(f"  unique vals = {df[col].nunique()}")
        totals = df[col].astype(str).str.lower().str.contains(r"total|grand|^\s*$", regex=True)
        print(f"  'total' rows bị drop = {totals.sum()}")
        print(f"  sample (5)  = {df[col].dropna().head(5).tolist()}")

print(f"\n{'='*60}")
print("SIMULATION: sau khi app aggregate by Campaign")
print(f"{'='*60}")

# Simulate the rename + aggregate the app does
rename = {}
for col in df.columns:
    cl = col.lower().strip()
    if "campaign name" in cl:
        rename[col] = "Campaign"
    elif "amount spent" in cl or ("spend" in cl and "roas" not in cl):
        rename[col] = "Spend"
    elif "purchases conversion value" in cl or "conversion value" in cl:
        rename[col] = "Revenue"
    elif "purchases" in cl and "roas" not in cl and "value" not in cl and "cart" not in cl:
        rename[col] = "Purchases"

df2 = df.rename(columns=rename)
df2 = df2.loc[:, ~df2.columns.duplicated(keep="first")]

for col in ["Spend", "Revenue", "Purchases"]:
    if col in df2.columns:
        df2[col] = pd.to_numeric(
            df2[col].astype(str).str.replace(",", ""), errors="coerce"
        ).fillna(0)

if "Campaign" in df2.columns:
    df2 = df2.dropna(subset=["Campaign"])
    df2 = df2[~df2["Campaign"].astype(str).str.lower().str.contains(
        r"total|grand|^\s*$", na=True, regex=True
    )]
    agg = df2.groupby("Campaign")[
        [c for c in ["Spend", "Revenue", "Purchases"] if c in df2.columns]
    ].sum()
    print(agg.to_string())
    print(f"\nAgg totals:")
    for col in ["Spend", "Revenue", "Purchases"]:
        if col in agg.columns:
            print(f"  {col}: {agg[col].sum():,.0f}")
