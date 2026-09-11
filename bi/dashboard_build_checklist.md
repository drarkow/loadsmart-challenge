# Power BI dashboard build checklist

## Model

- [ ] Import fct_loads
- [ ] Import dim_shipper
- [ ] Import dim_carrier
- [ ] Import dim_lane
- [ ] Import dim_date
- [ ] Create dimension -> fact relationships
- [ ] Make delivery_date the active date relationship
- [ ] Keep booked_date and pickup_date inactive
- [ ] Hide technical keys from report view

## Executive Overview

- [ ] Total Loads card
- [ ] Delivered Loads card
- [ ] Delivery Rate card
- [ ] Total Book Price card
- [ ] Total P&L card
- [ ] P&L Margin card
- [ ] Monthly delivered-load trend
- [ ] Monthly book-price trend
- [ ] Intrastate vs interstate chart
- [ ] Top 10 shippers by book price

## Lane & Geography

- [ ] Top lanes by delivered loads
- [ ] Top lanes by average book price
- [ ] Pickup-state average book price
- [ ] Pickup-state load count
- [ ] Inbound Texas carriers

## Carrier Performance

- [ ] Carrier load volume
- [ ] Average rating
- [ ] On-time pickup
- [ ] On-time delivery
- [ ] On-time overall
- [ ] Carrier P&L

## Shipper Performance

- [ ] Shipper delivered loads
- [ ] Shipper book price
- [ ] Shipper P&L
- [ ] Monthly shipper volume

## UX

- [ ] Common slicers synchronized where useful
- [ ] Tooltips include load count and financial measures
- [ ] Number formats are consistent
- [ ] Zero-value pricing is not silently excluded
- [ ] Business definitions are visible on the report or documented here
