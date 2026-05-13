import plotly.graph_objects as go

THB_TO_VND = 830
CHART_H = 350

ROAS_TIERS = [
    ("🔴 Losing",    "#ff4444", 0,   1.0),
    ("🟡 Below avg", "#ffd700", 1.0, 3.0),
    ("🟢 Good",      "#00ff88", 3.0, 5.0),
    ("⭐ Excellent",  "#00d4ff", 5.0, 999),
]

def get_roas_tier(roas):
    for label, color, lo, hi in ROAS_TIERS:
        if lo <= roas < hi:
            return label, color
    return "⭐ Excellent", "#00d4ff"

def fmt_vnd(val):
    if val >= 1_000_000_000:
        return f"{val/1_000_000_000:.1f}B ₫"
    elif val >= 1_000_000:
        return f"{val/1_000_000:.1f}M ₫"
    elif val >= 1_000:
        return f"{val/1_000:.1f}K ₫"
    return f"{val:,.0f} ₫"

def fmt_num(val):
    if val >= 1_000_000:
        return f"{val/1_000_000:.1f}M"
    elif val >= 1_000:
        return f"{val/1_000:.1f}K"
    return f"{val:,.0f}"

def _ly(**kw):
    base = dict(
        paper_bgcolor="#1e2235", plot_bgcolor="#1e2235",
        font=dict(color="#c0c8d8", size=11),
        height=CHART_H,
        margin=dict(l=10, r=120, t=30, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#2d3149", borderwidth=1,
                    font=dict(color="#e0e0e0")),
        xaxis=dict(gridcolor="#2d3149", linecolor="#2d3149", zerolinecolor="#2d3149",
                   tickfont=dict(color="#c0c8d8")),
        yaxis=dict(gridcolor="#2d3149", linecolor="#2d3149", tickfont=dict(color="#c0c8d8")),
    )
    base.update(kw)
    return base

def _ly_pie(**kw):
    base = dict(
        paper_bgcolor="#1e2235", plot_bgcolor="#1e2235",
        font=dict(color="#e0e0e0", size=10),
        height=CHART_H,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e0e0e0")),
        showlegend=True,
    )
    base.update(kw)
    return base

def _hbar(y, x, colors, texts, xaxis_title=""):
    if isinstance(colors, str):
        colors = [colors] * len(x)
    mx = max(x) if len(x) > 0 else 1
    fig = go.Figure(go.Bar(
        x=list(x), y=list(y), orientation="h",
        marker_color=colors, text=texts,
        textposition="outside",
        textfont=dict(color="#e0e0e0", size=9),
        cliponaxis=False,
        hovertemplate="%{y}<br>" + xaxis_title + ": %{text}<extra></extra>",
    ))
    fig.update_layout(**_ly(xaxis_title=xaxis_title))
    fig.update_xaxes(range=[0, mx * 1.40])
    return fig

def styled_table(df):
    header = "".join(
        f'<th style="background:#1a2744;color:#00d4ff;padding:10px 16px;'
        f'text-align:left;font-size:12px;font-weight:700;'
        f'border-bottom:2px solid #2d4a6b;white-space:nowrap;">{col}</th>'
        for col in df.columns
    )
    body = ""
    for i, (_, row) in enumerate(df.iterrows()):
        bg = "#1e2235" if i % 2 == 0 else "#252a3d"
        cells = "".join(
            f'<td style="padding:9px 16px;font-size:13px;color:#e0e0e0;'
            f'border-bottom:1px solid #2d3149;">{val}</td>'
            for val in row
        )
        body += f'<tr style="background:{bg};">{cells}</tr>'
    return (
        '<div style="overflow-x:auto;border-radius:8px;border:1px solid #2d3149;margin-bottom:16px;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr>{header}</tr></thead>'
        f'<tbody>{body}</tbody>'
        '</table></div>'
    )
