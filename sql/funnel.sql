-- Strictly chronological, visitor-level funnel (not a same-item purchase funnel).
-- One first qualifying action per visitor; timestamps are Unix milliseconds.
-- This ensures: view < addtocart < transaction.
WITH first_views AS (
    SELECT visitorid, MIN(timestamp) AS first_view_ms
    FROM events WHERE event = 'view'
    GROUP BY visitorid
),
first_carts AS (
    SELECT v.visitorid, MIN(e.timestamp) AS first_cart_ms
    FROM first_views v JOIN events e ON e.visitorid = v.visitorid
    WHERE e.event='addtocart' AND e.timestamp > v.first_view_ms
    GROUP BY v.visitorid
),
first_purchases AS (
    SELECT c.visitorid, MIN(e.timestamp) AS first_purchase_ms
    FROM first_carts c JOIN events e ON e.visitorid = c.visitorid
    WHERE e.event='transaction' AND e.timestamp > c.first_cart_ms
    GROUP BY c.visitorid
)
SELECT v.visitorid, v.first_view_ms, c.first_cart_ms, p.first_purchase_ms
FROM first_views v
LEFT JOIN first_carts c ON c.visitorid=v.visitorid
LEFT JOIN first_purchases p ON p.visitorid=v.visitorid;
