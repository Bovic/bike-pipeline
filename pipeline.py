import pandas as pd
from sqlalchemy import create_engine, text

RAW_FILE = "data/201306-citibike-tripdata.csv"
DB_URL = "postgresql+psycopg2://de_user:de_pass@localhost:5432/bikes"


def extract(path):
    return pd.read_csv(path)


def transform(df):
    df = df.copy()

    # 1. Friendly column names (no spaces)
    df = df.rename(columns={
        "tripduration": "duration_sec",
        "starttime": "start_time",
        "stoptime": "end_time",
        "start station id": "start_station_id",
        "start station name": "start_station_name",
        "start station latitude": "start_station_lat",
        "start station longitude": "start_station_lon",
        "end station id": "end_station_id",
        "end station name": "end_station_name",
        "end station latitude": "end_station_lat",
        "end station longitude": "end_station_lon",
        "bikeid": "bike_id",
        "usertype": "rider_type",
        "birth year": "birth_year",
        "gender": "gender_code",
    })

    # 2. Fix data types
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])
    df["birth_year"] = df["birth_year"].astype("Int64")
    df["end_station_id"] = df["end_station_id"].astype("Int64")

    # 3. Mark bad rows with a reason instead of deleting them
    df["reject_reason"] = None

    df = df.sort_values(["bike_id", "start_time", "duration_sec"])
    is_dup = df.duplicated(subset=["bike_id", "start_time"], keep="first")
    df.loc[is_dup, "reject_reason"] = "duplicate_bike_start"

    too_long = (df["duration_sec"] > 86400) & df["reject_reason"].isnull()
    df.loc[too_long, "reject_reason"] = "over_24_hours"
    main_month = df["start_time"].dt.to_period("M").mode()[0]
    wrong_month = (df["start_time"].dt.to_period("M") != main_month) & df["reject_reason"].isnull()
    df.loc[wrong_month, "reject_reason"] = "outside_file_month"
    

    # 4. Split into good and rejected
    clean = df[df["reject_reason"].isnull()].drop(columns="reject_reason")
    rejected = df[df["reject_reason"].notnull()]
    return clean, rejected


def build_stations(df):
    cols = ["station_id", "station_name", "latitude", "longitude"]

    start = df[["start_station_id", "start_station_name",
                "start_station_lat", "start_station_lon"]].copy()
    start.columns = cols

    end = df[["end_station_id", "end_station_name",
              "end_station_lat", "end_station_lon"]].dropna(subset=["end_station_id"]).copy()
    end.columns = cols

    stations = pd.concat([start, end]).drop_duplicates(subset="station_id")
    stations["station_id"] = stations["station_id"].astype(int)
    return stations


def load(clean, engine):
    stations = build_stations(clean)
    trips = clean[["bike_id", "start_time", "end_time", "duration_sec",
                   "start_station_id", "end_station_id", "rider_type",
                   "birth_year", "gender_code"]]

    # engine.begin() = one transaction: if anything fails, nothing is saved
    with engine.begin() as conn:
        stations.to_sql("stg_stations", conn, if_exists="replace", index=False)
        conn.execute(text("""
            INSERT INTO dim_stations (station_id, station_name, latitude, longitude)
            SELECT station_id, station_name, latitude, longitude FROM stg_stations
            ON CONFLICT (station_id) DO NOTHING
        """))

        trips.to_sql("stg_trips", conn, if_exists="replace", index=False,
                     chunksize=10000, method="multi")
        conn.execute(text("""
            INSERT INTO fact_trips (bike_id, start_time, end_time, duration_sec,
                                    start_station_id, end_station_id, rider_type,
                                    birth_year, gender_code)
            SELECT bike_id, start_time, end_time, duration_sec,
                   start_station_id, end_station_id, rider_type,
                   birth_year, gender_code
            FROM stg_trips
            ON CONFLICT (bike_id, start_time) DO NOTHING
        """))

        conn.execute(text("DROP TABLE stg_stations"))
        conn.execute(text("DROP TABLE stg_trips"))


if __name__ == "__main__":
    raw = extract(RAW_FILE)
    clean, rejected = transform(raw)

    print("rows in:       ", len(raw))
    print("rows clean:    ", len(clean))
    print("rows rejected: ", len(rejected))
    assert len(raw) == len(clean) + len(rejected), "Rows went missing!"
    rejected.to_csv("data/rejected_trips.csv", index=False)

    engine = create_engine(DB_URL)
    load(clean, engine)

    with engine.connect() as conn:
        n_trips = conn.execute(text("SELECT COUNT(*) FROM fact_trips")).scalar()
        n_stations = conn.execute(text("SELECT COUNT(*) FROM dim_stations")).scalar()
    print("fact_trips in database:  ", n_trips)
    print("dim_stations in database:", n_stations)
    assert n_trips == len(clean), "Database count does not match clean data!"