-- Part 1 Task 3: Reports
-- Comments display exact query results.
-- Queries process uncleaned data with 180 raw orders.

-- Query a: Order totals, revenue, and average order value
-- Output:
-- total_orders  total_revenue  avg_order_value
-- 180           99860.20       554.78

SELECT
    COUNT(*)                                                                    AS total_orders,
    ROUND(SUM(o.quantity * p.price * (1.0 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_revenue,
    ROUND(AVG(o.quantity * p.price * (1.0 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS avg_order_value
FROM orders o
JOIN products p ON o.product_id = p.product_id;


-- Query b: Row count comparison identifies unrated orders
-- Output:
-- total_rows  rated_rows  difference
-- 180         165         15

SELECT
    COUNT(*)              AS total_rows,
    COUNT(rating)         AS rated_rows,
    COUNT(*) - COUNT(rating) AS difference
FROM orders;


-- Query c: Zero order customer identification using left join and not in validation
-- Query 1 Output:
-- customer_id  name    order_count
-- C045         Vihaan  0
--
-- Query 2 Output:
-- customer_id  name
-- C045         Vihaan

-- Left join query
SELECT
    c.customer_id,
    c.name,
    COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) = 0;

-- Validation query confirms the zero order customer
SELECT customer_id, name
FROM customers
WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM orders);


-- Query d: City return rates exceeding twenty percent threshold
-- Output:
-- city       total_orders  returned_orders  return_rate_pct
-- Jaipur     19            8                42.1
-- Lucknow    49            15               30.6
-- Bangalore  33            8                24.2

SELECT
    c.city,
    COUNT(*)                                          AS total_orders,
    SUM(o.returned)                                   AS returned_orders,
    ROUND(100.0 * SUM(o.returned) / COUNT(*), 1)      AS return_rate_pct
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;


-- Query e: Customer ranking by spend volume
-- Secondary customer identifier sort provides stable tie break ordering.
-- Top 5 Output:
-- customer_id  name      total_spend
-- C043         Reyansh   12920.00
-- C026         Isha       8371.60
-- C008         Meera      4564.60
-- C011         Arjun      4111.00
-- C042         Sanya      3785.00
--
-- Offset query ranks three to five output:
-- customer_id  name   total_spend
-- C008         Meera  4564.60
-- C011         Arjun  4111.00
-- C042         Sanya  3785.00

-- Top five spenders
SELECT
    c.customer_id,
    c.name,
    ROUND(SUM(o.quantity * p.price * (1.0 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o
JOIN products  p ON o.product_id  = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC   -- Stable tie break sort
LIMIT 5;

-- Middle rank spenders using offset
SELECT
    c.customer_id,
    c.name,
    ROUND(SUM(o.quantity * p.price * (1.0 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o
JOIN products  p ON o.product_id  = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;


-- Query f: Revenue summary by product category
-- Three table join combines orders, products, and customer records.
-- Output:
-- category      order_count  category_revenue
-- Haircare      54           44956.10
-- Skincare      60           27346.00
-- Babycare      30           16805.00
-- PersonalCare  36           10753.10

SELECT
    p.category,
    COUNT(*)                                                                           AS order_count,
    ROUND(SUM(o.quantity * p.price * (1.0 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS category_revenue
FROM orders o
JOIN products  p ON o.product_id  = p.product_id
JOIN customers c ON o.customer_id = c.customer_id   -- Three table join
GROUP BY p.category
ORDER BY category_revenue DESC;


-- Query g: Customer names starting with letter A
-- Output:
-- customer_id  name     city
-- C001         Aarav    Mumbai
-- C003         Aditi    Mumbai
-- C031         Aditya   Jaipur
-- C036         Aisha    Delhi
-- C004         Ananya   Lucknow
-- C030         Anika    Bangalore
-- C044         Aria     Bangalore
-- C011         Arjun    Bangalore
-- C021         Aryan    Bangalore
-- C041         Ayaan    Lucknow
-- (10 rows)

SELECT customer_id, name, city
FROM customers
WHERE name LIKE 'A%'
ORDER BY name;


-- Query h: Distinct customer acquisition channels
-- Output:
-- acquisition_source
-- Ad
-- Organic
-- Referral
-- Social
-- (4 rows)

SELECT DISTINCT acquisition_source
FROM customers
ORDER BY acquisition_source;


-- Query i: Loyalty tier derivation from city tier
-- Output:
-- loyalty_tier  customer_count
-- Gold          28
-- Silver        17

ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);

-- Conditional logic assigns tier value to every customer row
UPDATE customers
SET loyalty_tier = CASE
    WHEN city_tier = 1 THEN 'Gold'
    ELSE                    'Silver'
END;

SELECT loyalty_tier, COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier;
