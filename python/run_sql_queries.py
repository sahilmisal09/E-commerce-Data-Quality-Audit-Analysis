"""
E-Commerce Analytics — SQL Query Runner
Loads CSVs into SQLite and executes all business queries.
Author: Abhay Yadav
"""

import pandas as pd
import sqlite3
import os

BASE = '/home/claude/ecommerce_analytics'

# ─── Load into SQLite ────────────────────────────────────────────────────────
conn = sqlite3.connect(':memory:')

customers   = pd.read_csv(f'{BASE}/data/customers.csv',   parse_dates=['registration_date'])
products    = pd.read_csv(f'{BASE}/data/products.csv')
orders      = pd.read_csv(f'{BASE}/data/orders.csv',      parse_dates=['order_date'])
order_items = pd.read_csv(f'{BASE}/data/order_items.csv')
reviews     = pd.read_csv(f'{BASE}/data/reviews.csv',     parse_dates=['review_date'])

for df, name in [(customers,'customers'),(products,'products'),
                 (orders,'orders'),(order_items,'order_items'),(reviews,'reviews')]:
    df.to_sql(name, conn, if_exists='replace', index=False)

print("✅ All tables loaded into SQLite\n")

# ─── Query Definitions ───────────────────────────────────────────────────────
queries = {
    "01_Executive_Summary": """
        SELECT
            COUNT(DISTINCT o.order_id)  AS total_orders,
            COUNT(DISTINCT o.customer_id) AS unique_customers,
            ROUND(SUM(oi.total_price),2) AS gross_revenue,
            ROUND(SUM(oi.discount_amt),2) AS total_discount,
            ROUND(SUM(oi.total_price)/COUNT(DISTINCT o.order_id),2) AS avg_order_value,
            ROUND(SUM(oi.total_price)/COUNT(DISTINCT o.customer_id),2) AS revenue_per_customer
        FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
        WHERE o.status='Delivered'
    """,
    "02_Monthly_Revenue": """
        SELECT
            STRFTIME('%Y',o.order_date) AS year,
            STRFTIME('%m',o.order_date) AS month,
            COUNT(DISTINCT o.order_id)  AS orders,
            ROUND(SUM(oi.total_price),2) AS revenue
        FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
        WHERE o.status='Delivered'
        GROUP BY year,month ORDER BY year,month
    """,
    "03_Top10_Products": """
        SELECT p.product_name, p.category,
            SUM(oi.quantity) AS units_sold,
            ROUND(SUM(oi.total_price),2) AS revenue,
            ROUND(SUM(oi.total_price-(p.cost_price*oi.quantity)),2) AS gross_profit
        FROM order_items oi
        JOIN products p ON oi.product_id=p.product_id
        JOIN orders o   ON oi.order_id=o.order_id
        WHERE o.status='Delivered'
        GROUP BY p.product_name,p.category
        ORDER BY revenue DESC LIMIT 10
    """,
    "04_Category_Performance": """
        SELECT p.category,
            COUNT(DISTINCT oi.order_id) AS orders,
            SUM(oi.quantity) AS units_sold,
            ROUND(SUM(oi.total_price),2) AS revenue,
            ROUND(AVG(oi.unit_price),2) AS avg_price
        FROM order_items oi
        JOIN products p ON oi.product_id=p.product_id
        JOIN orders o   ON oi.order_id=o.order_id
        WHERE o.status='Delivered'
        GROUP BY p.category ORDER BY revenue DESC
    """,
    "05_RFM_Segments": """
        WITH rfm AS (
            SELECT o.customer_id,
                JULIANDAY('2024-12-31')-JULIANDAY(MAX(o.order_date)) AS recency,
                COUNT(DISTINCT o.order_id) AS frequency,
                ROUND(SUM(oi.total_price),2) AS monetary
            FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
            WHERE o.status='Delivered' GROUP BY o.customer_id
        ),
        scored AS (
            SELECT *, NTILE(5) OVER(ORDER BY recency ASC) r,
                NTILE(5) OVER(ORDER BY frequency DESC) f,
                NTILE(5) OVER(ORDER BY monetary DESC) m FROM rfm
        )
        SELECT
            CASE WHEN r+f+m>=13 THEN 'Champions'
                 WHEN r+f+m>=10 THEN 'Loyal'
                 WHEN r+f+m>=7  THEN 'Potential'
                 WHEN r+f+m>=4  THEN 'At Risk'
                 ELSE 'Lost' END AS segment,
            COUNT(*) AS customers,
            ROUND(AVG(recency),1) AS avg_recency_days,
            ROUND(AVG(frequency),1) AS avg_orders,
            ROUND(AVG(monetary),2) AS avg_spent
        FROM scored GROUP BY segment ORDER BY avg_spent DESC
    """,
    "06_City_Sales": """
        SELECT o.shipping_city AS city,
            COUNT(DISTINCT o.order_id) AS orders,
            ROUND(SUM(oi.total_price),2) AS revenue,
            ROUND(AVG(oi.total_price),2) AS avg_order_value,
            ROUND(COUNT(CASE WHEN o.status='Cancelled' THEN 1 END)*100.0/COUNT(*),2) AS cancel_rate
        FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
        GROUP BY city ORDER BY revenue DESC
    """,
    "07_Payment_Analysis": """
        SELECT payment_method,
            COUNT(*) AS total,
            COUNT(CASE WHEN status='Delivered' THEN 1 END) AS delivered,
            COUNT(CASE WHEN status='Cancelled' THEN 1 END) AS cancelled,
            ROUND(COUNT(CASE WHEN status='Delivered' THEN 1 END)*100.0/COUNT(*),2) AS success_rate
        FROM orders GROUP BY payment_method ORDER BY total DESC
    """,
    "08_Discount_Impact": """
        SELECT o.discount_pct,
            COUNT(DISTINCT o.order_id) AS orders,
            ROUND(AVG(oi.total_price),2) AS avg_order_value,
            ROUND(SUM(oi.total_price),2) AS revenue,
            ROUND(SUM(oi.discount_amt),2) AS discount_given
        FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
        GROUP BY o.discount_pct ORDER BY o.discount_pct
    """,
}

# ─── Execute & Export ────────────────────────────────────────────────────────
out_dir = f'{BASE}/powerbi_export/sql_results'
os.makedirs(out_dir, exist_ok=True)

for qname, sql in queries.items():
    df = pd.read_sql_query(sql, conn)
    df.to_csv(f'{out_dir}/{qname}.csv', index=False)
    print(f"  ✅ {qname} → {len(df)} rows")

conn.close()
print(f"\n📁 All query results exported to: {out_dir}")
