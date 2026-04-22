# Budget

**Scope:** Financial stewardship of the engineering org. Declared category taxonomy, plan / actual / forecast tracking per category per period, budget-to-actual variance, budget-narrative authoring for reporting audiences. Role-shape module — essential for P&L-owning roles.

**Out of scope:** Build-vs-buy architectural decisions (Technical Strategy owns those; this module provides cost context); workforce plan (Hiring owns the plan, this module tracks the financial envelope); non-engineering budget; payroll execution; invoice-level AP/procurement.

**Frameworks:** [Geoffrey Moore — Core vs Context](https://a16z.com/the-core-vs-context-model/) as the lens for contested spend decisions. Standard financial-planning concepts (capex/opex, unit economics, fully-loaded headcount cost, zero-based budgeting) form the conceptual basis but aren't single-framework-anchored.

**Depends on:**
- Required: none
- Optional: `hiring` (open reqs + planned hires drive headcount cost), `tech-ops` (infrastructure spend context), `business-alignment` (financial targets from company goals), `technical-strategy` (build-vs-buy ADRs for category-level spend explanations)

**Example tasks:**
- "Forecast Q3 engineering spend given the current hiring plan."
- "Log the actual cloud spend for March — came in at $X."
- "Show me variance across all categories for Q2."
- "Draft the budget section of next board update — explain the vendor overrun."
- "Close Q2 — snapshot everything to history and roll to Q3."

**State location:** `cto-os-data/modules/budget/state/`
