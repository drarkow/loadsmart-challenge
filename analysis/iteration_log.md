# AI iteration log

The challenge requires one initial run, documentation/model fixes for failures, and a re-run.

## Run 1

| Question | Failure / ambiguity | Root cause | Fix location | Before | After |
|---|---|---|---|---|---|
| Q1 | Initial ambiguity expected | "Last full month" could mean latest complete calendar month (February 2025) or latest month with delivery activity (January 2025) | Documentation | February 2025 / 0 delivered | TBD after Claude run |
| Q2 | No known semantic issue | Book price aggregation is available at load grain and shipper dimension | YML documentation if needed | TBD | TBD |
| Q3 | No known semantic issue | Pickup state is explicitly parsed in dim_lane | YML documentation if needed | TBD | TBD |
| Q4 | Pending execution | TBD | TBD | TBD | TBD |
| Q5 | Initial ambiguity expected | "Moved" could mean booked, sourced, or delivered; model documents delivered interpretation | Documentation | Delivered into TX | TBD after Claude run |
| Q6 | Initial ambiguity expected | Intrastate/interstate is a business classification derived from pickup/delivery states | Documentation | Explicit haul_type | TBD after Claude run |
| Q7 | Initial ambiguity expected | Monthly volume needs delivered-load grain and delivery month; complete dim_date preserves zero months | Documentation / model | Feb 2025 can appear as zero | TBD after Claude run |
| Q8 | Initial ambiguity expected | Both the >=10 threshold and average must use delivered loads | Documentation | Explicit in question metadata | TBD after Claude run |

## Rule for iteration decisions

- Fix the **data model** when the required business concept is not represented or grain is wrong.
- Fix **dbt YML documentation** when the model contains the needed concept but Claude cannot reliably infer the intended business meaning.
- Fix the **prompt** only for agent behavior that is not a data/semantic issue (for example, returning SQL only).
