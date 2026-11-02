# Citi Bike Trips Pipeline

A batch ETL pipeline that cleans one month of Citi Bike trip data (June 2013)
and loads it into a PostgreSQL star schema. It is safe to re-run: running it
twice leaves the database unchanged.

## Pipeline

```
CSV file  ->  pandas (clean + validate)  ->  staging tables  ->  PostgreSQL (fact + dimension)
                    |
                    +-> data/rejected_trips.csv (bad rows, with a reason)
```

## Results

- 577,703 rows in = 577,352 loaded + 351 rejected
- 337 stations, 577,352 trips

## Data cleaning decisions

| Problem found | Rule | Rows |
|---|---|---|
| Same bike, same start second (duplicate) | Keep the shortest trip, reject the others | 6 |
| Trip longer than 24 hours (likely lost or undocked bikes) | Reject and record the reason | 344 |
| Trip started outside the file's month (July 1st) | Reject and record the reason | 1 |
| Missing end station | Keep the row, leave the end station empty | 18,059 |
| Missing birth year (casual riders don't register one) | Keep the row, leave birth year empty | 240,321 |

Rejected rows are saved to `data/rejected_trips.csv` with a reason, so no
row disappears silently. The pipeline stops with an error if
rows in does not equal rows loaded plus rows rejected.

## Schema

- `dim_stations(station_id, station_name, latitude, longitude)`
- `fact_trips(bike_id, start_time, end_time, duration_sec, start_station_id, end_station_id, rider_type, birth_year, gender_code)`
- The primary key of `fact_trips` is `(bike_id, start_time)`, which makes the
  load idempotent via `ON CONFLICT DO NOTHING`.

## How to run

1. Download the June 2013 Citi Bike trip file from the Citi Bike system data
   page and put it in a `data/` folder.
2. Start the database: `docker compose up -d`
3. Create tables: `Get-Content schema.sql | docker compose exec -T db psql -U de_user -d bikes`
4. Install packages: `pip install pandas sqlalchemy psycopg2-binary`
5. Run: `python pipeline.py`
6. Explore: `Get-Content queries.sql | docker compose exec -T db psql -U de_user -d bikes`

## Findings

- Casual riders' median trip is 19.1 minutes versus 11.8 for subscribers.
- The evening rush (5 to 6 pm) has about 53,000 trips, well above the morning
  peak of about 32,000.
- Weekends average more trips per day (22,277) than weekdays (about 17,700).
- A check on my own results showed 21 weekdays in a June file. One trip
  started on July 1st, so I added a rule to reject trips outside the file's
  month. The weekday vs weekend conclusion held after the fix.

## What I learned

- Check the data before writing code: the dataset had no trip ID, so I built a
  key from bike and start time.
- Average trip length is misleading because of outliers, so I report the median.
- Rejecting rows with a reason is safer than deleting them.
- Sanity-checking my own results (days per month) caught a bad row that the
  earlier cleaning rules missed.
- Idempotent inserts do not remove old rows, so fixing a cleaning rule needs
  a manual cleanup (or a full reload) of the data already loaded.

## What I would improve

- Add automated tests for the cleaning rules.
- Replace a whole month's data on each load, so rule changes do not leave old
  rows behind.
- Schedule the pipeline with Airflow.
- Process several months, and add a date dimension table.
- Add data-quality checks that fail the run on unexpected values.