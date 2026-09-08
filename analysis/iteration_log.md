# AI iteration log

The challenge requires one initial run, documentation/model fixes for failures, and a re-run.

## Run 1

| Question | Failure / ambiguity | Root cause | Fix location | Before | After |
|---|---|---|---|---|---|
| Q1 | Pending execution | Ambiguity around "last full month"; February has no delivery rows while March is partial | Documentation / semantic definition | TBD | TBD |
| Q2 | Pending execution | TBD | TBD | TBD | TBD |
| Q3 | Pending execution | TBD | TBD | TBD | TBD |
| Q4 | Pending execution | TBD | TBD | TBD | TBD |
| Q5 | Pending execution | "moved" may require an explicit delivered-load definition | Documentation | TBD | TBD |
| Q6 | Pending execution | Need explicit haul_type semantics | Documentation | TBD | TBD |
| Q7 | Pending execution | Need explicit use of delivery month and delivered-load grain | Documentation | TBD | TBD |
| Q8 | Pending execution | Threshold and average both need delivered-load semantics | Documentation | TBD | TBD |

## Rule for iteration decisions

- Fix the **data model** when the required business concept is not represented or grain is wrong.
- Fix **dbt YML documentation** when the model contains the needed concept but Claude cannot reliably infer the intended business meaning.
- Fix the **prompt** only for agent behavior that is not a data/semantic issue (for example, returning SQL only).
