# 🛒 E-Commerce Analytics Project

**End-to-End Analytics | SQL · Python · Power BI**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Power BI](https://img.shields.io/badge/Power%20BI-Ready-F2C811?logo=powerbi&logoColor=black)](https://powerbi.microsoft.com)
[![Status](https://img.shields.io/badge/Status-Complete-3FB950)](.)

---

## 📌 Project Overview

A full-stack data analytics project simulating a real-world **Indian e-commerce business** with 5,000+ orders across 1,000 customers and 36 products — covering two years of data (2023–2024).

The project demonstrates the complete analytics workflow: data engineering → SQL analysis → Python EDA → Power BI reporting.

---

## 🎯 Business Questions Answered

| # | Question | Tool Used |
|---|----------|-----------|
| 1 | What is total revenue, AOV, and delivery rate? | SQL + Power BI |
| 2 | Which months/quarters drive the most revenue? | SQL + Python |
| 3 | Which products and categories are most profitable? | SQL + Python |
| 4 | Who are our top customers (LTV + RFM)? | SQL |
| 5 | How does discount % affect revenue and cancellations? | SQL + Power BI |
| 6 | Which cities generate maximum orders? | Python + Power BI |
| 7 | What payment method do customers prefer? | SQL |
| 8 | What is the customer satisfaction score by category? | SQL |

---

## 📂 Project Structure

```
ecommerce_analytics/
│
├── data/
│   ├── generate_data.py        # Synthetic dataset generator
│   ├── customers.csv           # 1,000 customers (city, segment, age)
│   ├── products.csv            # 36 products across 6 categories
│   ├── orders.csv              # 5,000 orders (2023–2024)
│   ├── order_items.csv         # 8,700+ line items
│   └── reviews.csv             # 2,200+ product reviews
│
├── sql/
│   └── ecommerce_queries.sql   # 12 business SQL queries
│
├── python/
│   ├── eda_analysis.py         # EDA + dual dashboard generation
│   ├── run_sql_queries.py      # SQL runner (SQLite) + CSV export
│   ├── dashboard_1_sales_overview.png
│   └── dashboard_2_customer_insights.png
│
└── powerbi_export/
    ├── ecommerce_fact_table.csv    # Main fact table for Power BI
    ├── dim_customers.csv           # Customer dimension
    ├── dim_products.csv            # Product dimension
    └── sql_results/                # All SQL query outputs as CSVs
```

---

## 📊 Key Metrics (2023–2024)

| Metric | Value |
|--------|-------|
| 💰 Total Revenue | ₹13.92 Crore |
| 📦 Total Orders | 3,484 (delivered) |
| 👥 Unique Customers | 967 |
| 🏆 Best Category | Electronics |
| 🌆 Top City | Jaipur |
| 💳 Top Payment | UPI (35%) |
| ⭐ Avg Rating | 3.94 / 5.0 |
| 🎯 Delivery Rate | 69.7% |

---

## 🔍 SQL Highlights

### RFM Customer Segmentation
```sql
WITH rfm_scored AS (
    SELECT customer_id,
        NTILE(5) OVER (ORDER BY recency_days ASC)  AS r_score,
        NTILE(5) OVER (ORDER BY frequency DESC)     AS f_score,
        NTILE(5) OVER (ORDER BY monetary DESC)      AS m_score
    FROM rfm_raw
)
SELECT customer_segment, COUNT(*), AVG(monetary) FROM rfm_final
GROUP BY customer_segment ORDER BY avg_spent DESC;
```

### Monthly Cohort Retention
```sql
-- Tracks what % of each cohort returns in months 1–5
SELECT cohort_month, month_number,
       COUNT(DISTINCT customer_id) AS active_customers
FROM customer_activity
WHERE month_number BETWEEN 0 AND 5
GROUP BY cohort_month, month_number;
```

---

## 📈 Python Dashboard Previews

### Dashboard 1 — Sales Overview
- Monthly Revenue Trend (line + fill)
- Category Revenue (pie chart)
- Top 10 Products by Revenue (horizontal bar)
- Order Status Distribution (donut)

### Dashboard 2 — Customer & Payment Insights
- Revenue by Customer Segment
- Revenue by Age Group
- City-wise Sales Performance
- Payment Method Preferences
- Rating Distribution
- Discount % vs AOV (bubble chart)

---

## 🔌 Power BI Setup

1. Open Power BI Desktop
2. **Get Data → Text/CSV** → import `ecommerce_fact_table.csv`
3. Also import `dim_customers.csv` and `dim_products.csv`
4. Create relationships:
   - `fact[customer_id]` → `dim_customers[customer_id]`
   - `fact[product_id]` → `dim_products[product_id]`
5. Build visuals using pre-exported SQL result CSVs from `sql_results/`

### Recommended Power BI Visuals
- **Card KPIs**: Revenue, Orders, AOV, Delivery Rate
- **Line Chart**: Monthly Revenue Trend
- **Bar Chart**: Category / City Performance
- **Map**: City-wise order distribution
- **Pie**: Payment Method Share
- **Table**: Top Customers by LTV

---

## 🛠️ Tech Stack

| Layer | Tool |
|-------|------|
| Data Generation | Python (Pandas, NumPy) |
| Data Storage | CSV + SQLite (in-memory) |
| SQL Analysis | SQLite / PostgreSQL compatible |
| Visualization | Matplotlib, Seaborn |
| BI Reporting | Power BI Desktop |

---

## 🚀 How to Run

```bash
# 1. Clone the repo
git clone https://github.com/abhayadav692-sys/ecommerce-analytics.git
cd ecommerce-analytics

# 2. Install dependencies
pip install pandas numpy matplotlib seaborn

# 3. Generate dataset
python data/generate_data.py

# 4. Run EDA + Dashboards
python python/eda_analysis.py

# 5. Run SQL queries + export
python python/run_sql_queries.py
```

---

## 👨‍💻 Author

**Sahil Misal**
- 🔗 [LinkedIn](https://www.linkedin.com/in/sahil-misal-148752332/)
- 💻 [GitHub](https://github.com/sahilmisal09)
- 🛠️ Skills: SQL · Python · Power BI · Tableau · Excel

---

*Project built as part of data analytics portfolio — showcasing end-to-end analytics capabilities on a real-world business scenario.*
