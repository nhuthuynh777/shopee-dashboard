import os
import anthropic
import streamlit as st
from utils import fmt_vnd


@st.cache_data(show_spinner=False)
def generate_ai_insight(df_camp, overall_roas, total_spend, total_gmv):
    api_key = os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY chưa được cấu hình trong environment variables hoặc Streamlit secrets.")

    rows = [
        f"- {row['Campaign']}: ROAS={row['ROAS']:.2f}x, "
        f"Spend={fmt_vnd(row['Expense_VND'])}, "
        f"GMV={fmt_vnd(row['GMV_VND'])}, "
        f"CTR={row['CTR']:.2f}%, "
        f"ACOS={row['ACOS']:.1f}%"
        for _, row in df_camp.iterrows()
    ]

    prompt = f"""Bạn là chuyên gia phân tích quảng cáo Shopee. Hãy phân tích dữ liệu campaign sau và viết insight ngắn gọn, cụ thể bằng tiếng Việt.

Tổng quan kỳ này:
- Overall ROAS: {overall_roas:.2f}x
- Tổng Spend: {fmt_vnd(total_spend)}
- Tổng GMV: {fmt_vnd(total_gmv)}
- Số campaign: {len(df_camp)}

Chi tiết từng campaign:
{chr(10).join(rows)}

Viết phân tích theo đúng 3 section dưới đây, dùng header "###" cho mỗi section. Mỗi điểm viết ngắn gọn, kèm số liệu thực tế từ data:

### Vấn đề cần xử lý ngay
Các vấn đề nghiêm trọng cần action trong 24-48h: campaign lỗ tiền (ROAS < 1.0x), ACOS > 40%, CTR thấp bất thường.

### Cơ hội tăng trưởng
Các cơ hội để scale hoặc tối ưu: campaign ROAS xuất sắc (≥ 5.0x) đang under-invest, sản phẩm tiềm năng chưa được push ngân sách.

### Khuyến nghị hành động
Danh sách 3-5 bước cụ thể cần thực hiện, theo thứ tự ưu tiên, nêu rõ campaign/sản phẩm và hành động cần làm."""

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
