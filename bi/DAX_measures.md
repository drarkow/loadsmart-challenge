# Power BI DAX measures

These measures assume the imported model uses the table names shown below.

## Core volume

```DAX
Total Loads =
COUNTROWS('fct_loads')
```

```DAX
Delivered Loads =
CALCULATE(
    [Total Loads],
    'fct_loads'[is_delivered] = "True"
)
```

```DAX
Delivery Rate =
DIVIDE(
    [Delivered Loads],
    [Total Loads]
)
```

## Revenue / pricing

```DAX
Total Book Price =
SUM('fct_loads'[book_price])
```

```DAX
Average Book Price =
AVERAGE('fct_loads'[book_price])
```

```DAX
Delivered Book Price =
CALCULATE(
    [Total Book Price],
    'fct_loads'[is_delivered] = "True"
)
```

```DAX
Delivered Average Book Price =
CALCULATE(
    [Average Book Price],
    'fct_loads'[is_delivered] = "True"
)
```

## P&L

```DAX
Total P&L =
SUM('fct_loads'[pnl])
```

```DAX
Delivered P&L =
CALCULATE(
    [Total P&L],
    'fct_loads'[is_delivered] = "True"
)
```

```DAX
P&L Margin =
DIVIDE(
    [Total P&L],
    [Total Book Price]
)
```

```DAX
Delivered P&L Margin =
DIVIDE(
    [Delivered P&L],
    [Delivered Book Price]
)
```

## Carrier quality

```DAX
Average Carrier Rating =
AVERAGE('fct_loads'[carrier_rating])
```

```DAX
Average On-Time Pickup =
AVERAGE('fct_loads'[carrier_on_time_to_pickup])
```

```DAX
Average On-Time Delivery =
AVERAGE('fct_loads'[carrier_on_time_to_delivery])
```

```DAX
Average On-Time Overall =
AVERAGE('fct_loads'[carrier_on_time_overall])
```

## Date relationship examples

The active relationship should normally be:

`dim_date[date_day] -> fct_loads[delivery_date]`

To analyze booked volume using the inactive booked-date relationship:

```DAX
Booked Loads =
CALCULATE(
    [Total Loads],
    USERELATIONSHIP(
        'dim_date'[date_day],
        'fct_loads'[booked_date]
    )
)
```

To analyze pickup volume:

```DAX
Pickup Loads =
CALCULATE(
    [Total Loads],
    USERELATIONSHIP(
        'dim_date'[date_day],
        'fct_loads'[pickup_date]
    )
)
```

## Useful ranking measure

```DAX
Delivered Loads Rank =
RANKX(
    ALLSELECTED('dim_carrier'[carrier_name]),
    [Delivered Loads],
    ,
    DESC,
    DENSE
)
```
