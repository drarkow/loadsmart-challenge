# AI Iteration Log

## Purpose

This log documents the first AI run, the issues identified, the chosen remediation (prompt, dbt YAML documentation, or data model), and the resulting behavior after the changes.

The implementation intentionally treats the **dbt artifacts as the AI's semantic contract**. The context sent to Claude is generated programmatically from `manifest.json` and `catalog.json`; question-level assumptions from `questions.yml` are not injected into the AI prompt. This follows the challenge requirement that the dbt YAML documentation be the contract between the model and the AI rather than relying on hand-written context. 

## Baseline configuration

- LLM provider: Anthropic Claude
- Model: `claude-sonnet-5` (configured through `CLAUDE_MODEL`)
- Warehouse/database: DuckDB
- AI context: generated from dbt `manifest.json` and `catalog.json`
- Table rows: not sent to Claude
- SQL execution: DuckDB read-only connection
- Question runner: `ai/run_questions.py`

## Initial run

The first run was executed against the initial documented dimensional model. Q1-Q8 were successfully answered with usable SQL and results. Three additional questions were intentionally useful for testing semantic gaps and ambiguity: Q9 (P&L ratio), Q10 (carrier rating), and Q11 (profitability after operating overhead).

### Initial findings

| Question | Initial behavior | Diagnosis | Remediation category |
|---|---|---|---|
| Q1-Q8 | Correct / usable | No material semantic issue identified | None required |
| Q9 | Claude refused to answer because `pnl ratio` was not defined in its metadata context | The model contained the underlying `pnl` and `book_price` measures, but the business definition of the ratio was not documented in dbt | **dbt YAML documentation gap** identified |
| Q10 | Claude refused because it could not find carrier-rating information in its metadata context | `carrier_rating` existed in `fct_loads`, but the column was not documented in the dbt semantic metadata | **dbt YAML documentation gap** |
| Q11 | Claude generated SQL using `pnl > 0` as a proxy for profitability | The question explicitly requires profitability after operating overhead; positive load-level P&L is not equivalent | **Prompt change** |

## Q9 — P&L ratio

### Before

Claude returned an unsupported response because the documented metadata did not define a `pnl ratio` metric. The model correctly avoided inventing a formula from undocumented business semantics.

The question includes an assumption in `questions.yml`:

> Define lane P&L ratio as total P&L divided by total book price for the lane. Use all modeled loads and exclude lanes where total book price is zero.

It also contains a business definition:

> pnl ratio is pnl divided by the book price

However, these question-level fields are deliberately **not passed to Claude**. The AI context is restricted to dbt-generated metadata so that the dbt documentation remains the authoritative semantic contract.

### Decision

No prompt-side workaround was added. No external question context was injected into the AI request.

The correct long-term fix is to document the business metric in dbt, for example by adding a documented semantic field or metric definition for P&L ratio. For this challenge run, the question remains unresolved intentionally so the AI exposes the documentation gap.

### After

Claude continues to return:

```text
UNSUPPORTED: ... "pnl ratio" is not a defined metric in the documented model ...
```

This is treated as an intentional semantic-layer finding rather than an AI failure.

## Q10 — Carrier rating

### Before

Claude initially returned an unsupported response stating that carrier ratings were not available in the documented model.

### Investigation

The underlying fact model already contained `carrier_rating`. The issue was not missing data or an incorrect fact model; the column simply was not documented in the dbt YAML consumed by the semantic-context generator.

### Fix

Added `carrier_rating` to the documented `fct_loads` model in `schema.yml` and rebuilt the dbt project / regenerated the dbt artifacts.

This was intentionally fixed in the semantic layer rather than by changing the AI prompt.

### After

Claude successfully generated and executed a query that:

1. filters to non-null carrier ratings;
2. groups ratings by carrier;
3. calculates average rating and number of ratings; and
4. keeps carriers whose average rating is below 3.0.

The resulting SQL executed successfully against the dimensional model.

The working assumption recorded for Q10 is:

> Include only non-null carrier ratings. Calculate the average rating and count of ratings for each carrier whose average rating is lower than 3.0.

## Q11 — Profitability after operating overhead

### Before

Claude generated a valid-looking query, but the logic was semantically incorrect. It interpreted profitability as:

```sql
CASE WHEN f.pnl > 0 THEN 1 ELSE 0 END
```

and returned the percentage of delivered loads with positive load-level P&L.

That does **not** answer the stated question because the question explicitly asks for profitability after accounting for operating overhead.

### Diagnosis

The data model contains load-level P&L, but there is no documented operating-overhead measure or overhead allocation methodology. The model therefore cannot support the requested metric as stated.

The main problem in the AI behavior was **semantic substitution**: Claude replaced an unavailable metric with a related but different metric without making the substitution explicit.

### Fix

The system prompt was strengthened to explicitly prohibit substitution of related metrics and to require an `UNSUPPORTED:` response when required data or definitions are absent.

Examples added to the prompt include:

- `profitability after overhead` is not the same as `pnl > 0`;
- an undefined `pnl ratio` must not be inferred automatically; and
- an unavailable field cannot be inferred from an unrelated attribute.

The response contract was also changed so that Claude can return either:

```text
SELECT ...
```

or:

```text
UNSUPPORTED: <brief explanation>
```

The Python runner now treats `UNSUPPORTED:` as a valid semantic response rather than as invalid SQL.

### After

Claude correctly returns an unsupported response explaining that the model does not define operating overhead or a profitability metric that incorporates it.

This is the desired behavior. It avoids producing a plausible-looking but incorrect business answer.

## Summary of changes

| Area | Change | Why |
|---|---|---|
| dbt YAML | Added `carrier_rating` documentation to `fct_loads` | The field existed in the model but was invisible to the AI metadata contract |
| AI prompt | Added explicit anti-substitution rules | Prevent the AI from silently replacing unavailable metrics with related proxies |
| AI response contract | Added `UNSUPPORTED:` as a valid response | Allows the AI to decline questions that cannot be answered from documented metadata |
| Python runner | Added handling for `UNSUPPORTED:` | Prevents a valid semantic refusal from being treated as invalid SQL |
| Q9 | Left unresolved intentionally | Demonstrates a genuine gap in documented semantic definitions when the AI context is restricted to dbt artifacts |
| Q10 | Fixed through documentation | Demonstrates that improving dbt documentation can directly improve AI performance |
| Q11 | Fixed through prompt behavior | Demonstrates protection against semantic hallucination/substitution |

## Final outcome

The iteration resulted in three different and intentional behaviors:

- **Q9:** remains unsupported because the metric definition is not part of the dbt semantic contract.
- **Q10:** becomes answerable after the existing data field is properly documented in dbt.
- **Q11:** becomes unsupported rather than incorrectly answered after strengthening the AI's semantic-safety rules.

This outcome demonstrates the intended relationship between the components: the **data model provides the data**, **dbt documentation provides the semantics**, and the **AI is responsible for translating questions into SQL without inventing unsupported business meaning**.
