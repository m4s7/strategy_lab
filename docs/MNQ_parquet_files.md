# TickTradingData Bundle - MNQ 202504

## Schema
```json
{
  "fields": [
    {
      "name": "level",
      "nullable": "false",
      "type": "string"
    },
    {
      "name": "mdt",
      "nullable": "false",
      "type": "int8"
    },
    {
      "name": "timestamp",
      "nullable": "false",
      "type": "timestamp",
      "unit": "nanoseconds"
    },
    {
      "name": "operation",
      "nullable": "true",
      "type": "int8"
    },
    {
      "name": "depth",
      "nullable": "true",
      "type": "int8"
    },
    {
      "name": "market_maker",
      "nullable": "true",
      "type": "string"
    },
    {
      "name": "price",
      "nullable": "false",
      "precision": "13",
      "scale": "2",
      "type": "decimal128"
    },
    {
      "name": "volume",
      "nullable": "false",
      "type": "int32"
    }
  ],
  "schema_type": "arrow_dynamic",
  "version": "1.0"
}
```

## MDT = MarketDataType – identifies what kind of tick you’re receiving.

- 0 = Ask – current best offer price; use it to calculate spreads, mid-price, or simulate slippage on buy orders.
- 1 = Bid – current best bid price; combine with Ask for spreads and to test whether sell limits would fill.
- 2 = Last – price of the most recent trade, comes with the trade’s volume; core input for building OHLC bars or tape-reading logic.
- 3 = DailyHigh – new session high whenever it is broken; handy for breakout triggers or drawing “high of day”.
- 4 = DailyLow – new session low; used for downside breakouts, trailing stops, and range analysis.
- 5 = DailyVolume – running total volume for the session (cumulative, not delta); subtract previous value to get per-trade size, or gate strategies until liquidity ≥ x.
- 6 = LastClose – official close of the prior session; needed for gap calculations and reference lines.
- 7 = Opening – official session open price (usually sent once); basis for opening-range breakout stats.
- 8 = OpenInterest – total open contracts in futures; rising OI with rising price implies new money entering.
- 9 = Settlement – exchange-published settlement price after the close; used for margin revaluation and back-office accounting.
- 10 = Unknown – tick type the feed could not classify; safest action is to log or ignore it.

## Operation – appears only in level-2 (order-book) ticks and tells you what to do with that depth row.

- 0 = Add     — insert a new depth level
- 1 = Update  — modify the size of an existing level
- 2 = Remove  — delete the depth level from the book

## MNQ Parquet Files

### Date to File reference

`./MNQ_parquet_files.json`

### Sample

```json
[
  {
    "date": "2019-05-16",
    "entries": [
      {
        "file_path": "./MNQ/06-19/20190516.parquet",
        "file_date": "2019-05-16",
        "total_rows": 7585369,
        "l2_count": 5724939,
        "l1_count": 65051,
        "l1_volume": 120106,
        "status": "success"
      },
      {
        "file_path": "./MNQ/09-19/20190516.parquet",
        "file_date": "2019-05-16",
        "total_rows": 98439,
        "l2_count": 68388,
        "l1_count": 21,
        "l1_volume": 28,
        "status": "success"
      }
    ]
  },
  {
    "date": "2019-05-17",
    "entries": [
      {
        "file_path": "./MNQ/06-19/20190517.parquet",
        "file_date": "2019-05-17",
        "total_rows": 10883671,
        "l2_count": 8247210,
        "l1_count": 94196,
        "l1_volume": 172054,
        "status": "success"
      },
      {
        "file_path": "./MNQ/09-19/20190517.parquet",
        "file_date": "2019-05-17",
        "total_rows": 41008,
        "l2_count": 29894,
        "l1_count": 22,
        "l1_volume": 29,
        "status": "success"
      }
    ]
  },
  {
    "date": "2019-05-19",
    "entries": [
      {
        "file_path": "./MNQ/06-19/20190519.parquet",
        "file_date": "2019-05-19",
        "total_rows": 670124,
        "l2_count": 556581,
        "l1_count": 5356,
        "l1_volume": 6587,
        "status": "success"
      },
      {
        "file_path": "./MNQ/09-19/20190519.parquet",
        "file_date": "2019-05-19",
        "total_rows": 46135,
        "l2_count": 34355,
        "l1_count": 4,
        "l1_volume": 4,
        "status": "success"
      }
    ]
  },
]
```