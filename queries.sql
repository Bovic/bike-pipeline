-- 1. Top 10 busiest start stations
SELECT s.station_name, COUNT(*) AS trips
FROM fact_trips t
JOIN dim_stations s ON s.station_id = t.start_station_id
GROUP BY s.station_name
ORDER BY trips DESC
LIMIT 10;

-- 2. Trip length by rider type (average and median, in minutes)
SELECT rider_type,
       COUNT(*) AS trips,
       ROUND(AVG(duration_sec) / 60.0, 1) AS avg_minutes,
       ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_sec) / 60)::numeric, 1) AS median_minutes
FROM fact_trips
GROUP BY rider_type;

-- 3. Trips by hour of day
SELECT EXTRACT(HOUR FROM start_time)::int AS hour_of_day,
       COUNT(*) AS trips
FROM fact_trips
GROUP BY 1
ORDER BY 1;

-- 4. Weekday vs weekend (trips per day, so the comparison is fair)
SELECT CASE WHEN EXTRACT(ISODOW FROM start_time) IN (6, 7) THEN 'weekend' ELSE 'weekday' END AS day_type,
       COUNT(*) AS trips,
       COUNT(DISTINCT start_time::date) AS days,
       ROUND(COUNT(*)::numeric / COUNT(DISTINCT start_time::date)) AS trips_per_day
FROM fact_trips
GROUP BY 1;