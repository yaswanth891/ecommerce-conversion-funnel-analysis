# Product insight memo — Conversion Funnel

**Dataset:** Synthetic demonstration data (not actual shoppers)

**Question:** Where does the visitor conversion journey lose the most users?

**Definition:** First product view → first subsequent add-to-cart → first subsequent purchase, tracked at visitor level. Actions may relate to different items. Full observation window; no sessionization.

## Results

- Product viewers: **22,000**; added to cart: **7,099**; purchased: **3,242**.
- View-to-cart conversion: **32.27%**.
- Cart-to-purchase conversion: **45.67%**.
- Overall view-to-purchase conversion: **14.74%**.

## Recommendation

The largest conditional-stage loss is **view-to-cart**. Investigate whether product discovery and product-detail pages make it easy to add items to cart.

**Next experiment:** Define a specific UI hypothesis, randomly assign eligible visitors, and track purchase conversion plus guardrails such as errors and refunds.

## Limitations

Observational data do not establish causality. Visitor-level sequences can involve different products and multiple sessions. First-view cohorts near the dataset boundary have less time to convert. Do not describe synthetic demo results as real business impact.
