-- ============================================================
--  E-COMMERCE ANALYTICS — SQL QUERIES
--  Author : Abhay Yadav
--  Tools  : SQLite / PostgreSQL compatible
--  Tables : customers, products, orders, order_items, reviews
-- ============================================================


-- ─────────────────────────────────────────────────────────────
-- Q1. TOTAL REVENUE & KEY METRICS (Executive Summary)
-- ─────────────────────────────────────────────────────────────
SELECT
    COUNT(DISTINCT o.order_id)                        AS total_orders,
    COUNT(DISTINCT o.customer_id)                     AS unique_customers,
    ROUND(SUM(oi.total_price), 2)                     AS gross_revenue,
    ROUND(SUM(oi.discount_amt), 2)                    AS total_discount_given,
    ROUND(SUM(oi.total_price) / COUNT(DISTINCT o.order_id), 2)  AS avg_order_value,
    ROUND(SUM(oi.total_price) / COUNT(DISTINCT o.customer_id),2) AS revenue_per_customer
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'Delivered';


-- ─────────────────────────────────────────────────────────────
-- Q2. MONTHLY REVENUE TREND (2023 vs 2024)
-- ─────────────────────────────────────────────────────────────
SELECT
    STRFTIME('%Y', o.order_date)     AS year,
    STRFTIME('%m', o.order_date)     AS month,
    COUNT(DISTINCT o.order_id)       AS orders_placed,
    ROUND(SUM(oi.total_price), 2)    AS monthly_revenue,
    ROUND(AVG(oi.total_price), 2)    AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'Delivered'
GROUP BY year, month
ORDER BY year, month;


-- ─────────────────────────────────────────────────────────────
-- Q3. TOP 10 BEST-SELLING PRODUCTS BY REVENUE
-- ─────────────────────────────────────────────────────────────
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity)                                  AS units_sold,
    ROUND(SUM(oi.total_price), 2)                     AS total_revenue,
    ROUND(SUM(oi.total_price - (p.cost_price * oi.quantity)), 2) AS gross_profit,
    ROUND(
        (SUM(oi.total_price - (p.cost_price * oi.quantity))
         / NULLIF(SUM(oi.total_price), 0)) * 100, 2)  AS profit_margin_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o   ON oi.order_id   = o.order_id
WHERE o.status = 'Delivered'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────
-- Q4. CATEGORY-WISE PERFORMANCE
-- ─────────────────────────────────────────────────────────────
SELECT
    p.category,
    COUNT(DISTINCT oi.order_id)          AS total_orders,
    SUM(oi.quantity)                     AS units_sold,
    ROUND(SUM(oi.total_price), 2)        AS revenue,
    ROUND(AVG(oi.unit_price), 2)         AS avg_unit_price,
    ROUND(SUM(oi.discount_amt), 2)       AS discount_given,
    ROUND(
        SUM(oi.discount_amt)
        / NULLIF(SUM(oi.total_price + oi.discount_amt), 0) * 100, 2) AS discount_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders   o ON oi.order_id   = o.order_id
WHERE o.status = 'Delivered'
GROUP BY p.category
ORDER BY revenue DESC;


-- ─────────────────────────────────────────────────────────────
-- Q5. CUSTOMER SEGMENTATION — RFM ANALYSIS
--     (Recency, Frequency, Monetary)
-- ─────────────────────────────────────────────────────────────
WITH rfm_raw AS (
    SELECT
        o.customer_id,
        JULIANDAY('2024-12-31') - JULIANDAY(MAX(o.order_date)) AS recency_days,
        COUNT(DISTINCT o.order_id)                              AS frequency,
        ROUND(SUM(oi.total_price), 2)                          AS monetary
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status = 'Delivered'
    GROUP BY o.customer_id
),
rfm_scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days ASC)  AS r_score,   -- lower days = better
        NTILE(5) OVER (ORDER BY frequency DESC)     AS f_score,
        NTILE(5) OVER (ORDER BY monetary DESC)      AS m_score
    FROM rfm_raw
),
rfm_final AS (
    SELECT *,
        (r_score + f_score + m_score)               AS rfm_total,
        CASE
            WHEN (r_score + f_score + m_score) >= 13 THEN 'Champions'
            WHEN (r_score + f_score + m_score) >= 10 THEN 'Loyal Customers'
            WHEN (r_score + f_score + m_score) >= 7  THEN 'Potential Loyalists'
            WHEN (r_score + f_score + m_score) >= 4  THEN 'At Risk'
            ELSE 'Lost Customers'
        END AS customer_segment
    FROM rfm_scored
)
SELECT
    customer_segment,
    COUNT(*)                       AS customer_count,
    ROUND(AVG(recency_days),1)     AS avg_recency_days,
    ROUND(AVG(frequency),1)        AS avg_orders,
    ROUND(AVG(monetary),2)         AS avg_spent
FROM rfm_final
GROUP BY customer_segment
ORDER BY avg_spent DESC;


-- ─────────────────────────────────────────────────────────────
-- Q6. TOP 10 HIGH-VALUE CUSTOMERS (LTV)
-- ─────────────────────────────────────────────────────────────
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    c.segment,
    COUNT(DISTINCT o.order_id)     AS total_orders,
    SUM(oi.quantity)               AS items_bought,
    ROUND(SUM(oi.total_price), 2)  AS lifetime_value,
    ROUND(AVG(oi.total_price), 2)  AS avg_order_value,
    MAX(o.order_date)              AS last_purchase_date
FROM customers c
JOIN orders     o  ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id   = oi.order_id
WHERE o.status = 'Delivered'
GROUP BY c.customer_id, c.customer_name, c.city, c.segment
ORDER BY lifetime_value DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────
-- Q7. CITY-WISE SALES PERFORMANCE
-- ─────────────────────────────────────────────────────────────
SELECT
    o.shipping_city                AS city,
    COUNT(DISTINCT o.order_id)     AS total_orders,
    COUNT(DISTINCT o.customer_id)  AS unique_customers,
    ROUND(SUM(oi.total_price), 2)  AS revenue,
    ROUND(AVG(oi.total_price), 2)  AS avg_order_value,
    ROUND(
        COUNT(CASE WHEN o.status='Cancelled' THEN 1 END) * 100.0
        / COUNT(*), 2)             AS cancellation_rate_pct
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.shipping_city
ORDER BY revenue DESC;


-- ─────────────────────────────────────────────────────────────
-- Q8. PAYMENT METHOD PREFERENCE & CONVERSION
-- ─────────────────────────────────────────────────────────────
SELECT
    payment_method,
    COUNT(*)                                              AS total_orders,
    COUNT(CASE WHEN status='Delivered' THEN 1 END)        AS delivered,
    COUNT(CASE WHEN status='Cancelled' THEN 1 END)        AS cancelled,
    COUNT(CASE WHEN status='Returned'  THEN 1 END)        AS returned,
    ROUND(
        COUNT(CASE WHEN status='Delivered' THEN 1 END) * 100.0
        / COUNT(*), 2)                                    AS delivery_success_rate
FROM orders
GROUP BY payment_method
ORDER BY total_orders DESC;


-- ─────────────────────────────────────────────────────────────
-- Q9. ORDER STATUS FUNNEL & RETURN ANALYSIS
-- ─────────────────────────────────────────────────────────────
SELECT
    status,
    COUNT(*)                                  AS order_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM orders
GROUP BY status
ORDER BY order_count DESC;


-- ─────────────────────────────────────────────────────────────
-- Q10. PRODUCT RATING & REVIEW ANALYSIS
-- ─────────────────────────────────────────────────────────────
SELECT
    p.category,
    p.product_name,
    COUNT(r.review_id)              AS total_reviews,
    ROUND(AVG(r.rating), 2)         AS avg_rating,
    COUNT(CASE WHEN r.rating=5 THEN 1 END) AS five_star,
    COUNT(CASE WHEN r.rating<=2 THEN 1 END) AS low_ratings,
    ROUND(
        COUNT(CASE WHEN r.rating>=4 THEN 1 END) * 100.0
        / NULLIF(COUNT(r.review_id),0), 2) AS satisfaction_pct
FROM reviews r
JOIN orders     o  ON r.order_id    = o.order_id
JOIN order_items oi ON o.order_id   = oi.order_id
JOIN products   p  ON oi.product_id = p.product_id
GROUP BY p.category, p.product_name
HAVING total_reviews >= 5
ORDER BY avg_rating DESC, total_reviews DESC
LIMIT 15;


-- ─────────────────────────────────────────────────────────────
-- Q11. COHORT RETENTION — Monthly Customer Cohorts
-- ─────────────────────────────────────────────────────────────
WITH first_purchase AS (
    SELECT
        customer_id,
        STRFTIME('%Y-%m', MIN(order_date)) AS cohort_month
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY customer_id
),
customer_activity AS (
    SELECT
        o.customer_id,
        fp.cohort_month,
        STRFTIME('%Y-%m', o.order_date)  AS activity_month,
        (STRFTIME('%Y', o.order_date) - STRFTIME('%Y', fp.cohort_month || '-01')) * 12 +
        (STRFTIME('%m', o.order_date) - STRFTIME('%m', fp.cohort_month || '-01'))
            AS month_number
    FROM orders o
    JOIN first_purchase fp ON o.customer_id = fp.customer_id
    WHERE o.status = 'Delivered'
)
SELECT
    cohort_month,
    month_number,
    COUNT(DISTINCT customer_id) AS active_customers
FROM customer_activity
WHERE month_number BETWEEN 0 AND 5
GROUP BY cohort_month, month_number
ORDER BY cohort_month, month_number;


-- ─────────────────────────────────────────────────────────────
-- Q12. DISCOUNT IMPACT ON REVENUE
-- ─────────────────────────────────────────────────────────────
SELECT
    o.discount_pct                                    AS discount_tier,
    COUNT(DISTINCT o.order_id)                        AS orders,
    ROUND(AVG(oi.total_price), 2)                     AS avg_order_value,
    ROUND(SUM(oi.total_price), 2)                     AS total_revenue,
    ROUND(SUM(oi.discount_amt), 2)                    AS discount_given,
    ROUND(
        COUNT(CASE WHEN o.status='Cancelled' THEN 1 END) * 100.0
        / COUNT(*), 2)                                AS cancel_rate_pct
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.discount_pct
ORDER BY o.discount_pct;
