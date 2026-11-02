CREATE TABLE IF NOT EXISTS dim_stations (
    station_id   INTEGER PRIMARY KEY,
    station_name TEXT NOT NULL,
    latitude     DOUBLE PRECISION,
    longitude    DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS fact_trips (
    bike_id          INTEGER   NOT NULL,
    start_time       TIMESTAMP NOT NULL,
    end_time         TIMESTAMP NOT NULL,
    duration_sec     INTEGER   NOT NULL,
    start_station_id INTEGER   NOT NULL REFERENCES dim_stations (station_id),
    end_station_id   INTEGER   REFERENCES dim_stations (station_id),
    rider_type       TEXT      NOT NULL,
    birth_year       INTEGER,
    gender_code      SMALLINT,
    PRIMARY KEY (bike_id, start_time)
);