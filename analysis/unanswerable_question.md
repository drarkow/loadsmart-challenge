# Model limitation

**Question the current model cannot answer:**

> What percentage of loads were rejected by carriers before being booked, and which carriers had the highest rejection rate?

The current dataset records booked loads and some carrier/load attributes, but it does not contain tender/offer attempts, rejection events, or a denominator representing carrier opportunities to accept a load. A valid rejection rate therefore cannot be derived from the current fact table without inventing observations.

## What would need to change

- **Data:** add tender/offer attempt events with load ID, carrier ID, offer timestamp, and outcome (accepted/rejected/expired).
- **Model:** create a fact table at tender-attempt grain and relate it to the existing load and carrier dimensions.
- **Documentation:** define rejection-rate numerator and denominator, treatment of expired/no-response offers, and the observation window.
