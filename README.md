# 🛍️ Shopee Analytics Dashboard

Dashboard phân tích Shopee Ads — clone từ VSTu Analytics v2.

---

## 📁 Cấu trúc file

```
shopee_dashboard/
├── app.py              ← File chính (toàn bộ dashboard)
├── requirements.txt    ← Các thư viện cần cài
└── README.md           ← File này
```

---

## 🚀 Cách deploy lên Streamlit Cloud (FREE)

### Bước 1 — Cài Git & tạo GitHub account
- Vào https://github.com → Sign up (nếu chưa có)
- Tải GitHub Desktop: https://desktop.github.com (dễ dùng hơn command line)

### Bước 2 — Tạo repository trên GitHub
1. Vào https://github.com/new
2. Repository name: `shopee-dashboard`
3. Chọn **Private** (để bảo mật data)
4. Bấm **Create repository**

### Bước 3 — Upload file lên GitHub
1. Mở GitHub Desktop → **Add existing repository** → chọn folder `shopee_dashboard`
2. Hoặc dùng web: vào repo vừa tạo → **Add file** → **Upload files**
3. Upload 2 file: `app.py` và `requirements.txt`
4. Bấm **Commit changes**

### Bước 4 — Deploy lên Streamlit Cloud
1. Vào https://share.streamlit.io → **Sign in with GitHub**
2. Bấm **New app**
3. Chọn:
   - Repository: `shopee-dashboard`
   - Branch: `main`
   - Main file path: `app.py`
4. Bấm **Deploy** → đợi ~2 phút
5. App sẽ có link dạng: `https://[your-name]-shopee-dashboard.streamlit.app`

---

## 📊 Cách dùng dashboard

### Upload data
1. Vào sidebar bên trái → **Upload Raw Data**
2. Upload file `.xlsx` export từ Shopee Seller Center
3. Có thể upload **nhiều file cùng lúc** (nhiều tháng) — data sẽ tự merge

### Format file cần upload
File export từ **Shopee Seller Center → Advertising → Reports → All CPC**

Sheet cần có:
- `All Campaigns` — với các cột: Campaign, Ad/Product Name, Ad Status, Impression, Clicks, CTR, Expense, GMV, ROAS, ACOS, Items Sold
- `Shop Ad - Keywords` (optional) — keyword data

### Tỷ giá
Hiện tại mặc định: **1 THB = 830 VNĐ**
Để thay đổi: mở file `app.py`, dòng 4: `THB_TO_VND = 830` → sửa số

---

## 📦 Các tab trong dashboard

| Tab | Nội dung |
|-----|----------|
| 🏥 Business Health | KPI tổng, GMV/ROAS by campaign, bubble chart |
| 🏷️ Brand & Product | Product impressions, CTR, revenue, units sold |
| 📊 Onsite Ads Performance | Campaign table, charts, CTR vs ROAS bubble |
| 🔍 Campaign Setup Audit | ROAS tier, ACOS analysis, naming convention |
| 📌 Summary Insight | Auto-generated issues, data quality score |
| 🚀 Action Plan | Scale/Pause recommendations, checklist |

---

## 🔧 Thêm data Shopee Insights (sau)

Các section sau đang để trống chờ data:
- Daily GMV Trend (cần file export từ Shopee Insights)
- Traffic Overview (visitors, page views)
- Orders data

Khi có file → upload thêm vào sidebar, t sẽ update code để đọc thêm các sheet này.
