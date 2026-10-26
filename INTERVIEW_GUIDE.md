# Interview explanation / walkthrough

**Project:** E-commerce Conversion Funnel

**What it does:** A SQL-first visitor funnel with chronological view → add-to-cart → transaction events, conversion rates, and first-view cohort trends.

**Workflow:** Load validated CSV → compute SQL or Python metrics → render KPI dashboard → explain limits → propose next product action.

**Q: Why is stage order important?**

A: A cart or purchase event that occurred earlier than the visitor’s first qualifying event cannot count as successful progression.

**Q: Why not call this a session funnel?**

A: We do not sessionize events. The analysis is visitor-level and multiple products/sessions can participate.

**Q: Does the largest drop prove a broken feature?**

A: No. It is observational; we would build a testable hypothesis and experiment.

**Important:** The bundled outputs are synthetic demonstrations. Re-run on genuine public data before discussing any dataset-specific results in interviews.
