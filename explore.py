##Load the data and explore it

import pandas as pd


df = pd.read_csv("data/201306-citibike-tripdata.csv")

print(df.shape)           # (rows, columns)
print(df.head())          # first 5 rows
print(df.dtypes)          # data type of each column
print(df.isnull().sum())  # missing values per column
print(df.duplicated().sum())                              # fully identical rows
print(df.duplicated(subset=["bikeid", "starttime"]).sum())  # same bike, same start time
print(df["usertype"].value_counts())                      # rider types
print(df["tripduration"].describe())                      # min, max, average
print(df[df["birth year"].isnull()]["usertype"].value_counts())  # who has no birth year?

import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

df = pd.read_csv("data/201306-citibike-tripdata.csv")

# 1. The 6 suspicious duplicates
dupes = df[df.duplicated(subset=["bikeid", "starttime"], keep=False)]
print(dupes.sort_values(["bikeid", "starttime"])[["bikeid", "starttime", "stoptime", "tripduration", "start station id"]])

# 2. How many trips are longer than 24 hours?
print((df["tripduration"] > 86400).sum())

# 3. The 5 longest trips
print(df.nlargest(5, "tripduration")[["tripduration", "starttime", "stoptime", "bikeid"]])

# 4. Does tripduration match stoptime minus starttime?
calc = (pd.to_datetime(df["stoptime"]) - pd.to_datetime(df["starttime"])).dt.total_seconds()
print((calc - df["tripduration"]).abs().gt(1).sum())

# Cleaning the data
import pandas as pd

RAW_FILE = "data/201306-citibike-tripdata.csv"


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
    df["birth_year"] = df["birth_year"].astype("Int64")        # whole numbers, blanks allowed
    df["end_station_id"] = df["end_station_id"].astype("Int64")

    # 3. Mark bad rows with a reason instead of deleting them
    df["reject_reason"] = None

    df = df.sort_values(["bike_id", "start_time", "duration_sec"])
    is_dup = df.duplicated(subset=["bike_id", "start_time"], keep="first")
    df.loc[is_dup, "reject_reason"] = "duplicate_bike_start"

    too_long = (df["duration_sec"] > 86400) & df["reject_reason"].isnull()
    df.loc[too_long, "reject_reason"] = "over_24_hours"

    # 4. Split into good and rejected
    clean = df[df["reject_reason"].isnull()].drop(columns="reject_reason")
    rejected = df[df["reject_reason"].notnull()]
    return clean, rejected


if __name__ == "__main__":
    raw = extract(RAW_FILE)
    clean, rejected = transform(raw)

    print("rows in:       ", len(raw))
    print("rows clean:    ", len(clean))
    print("rows rejected: ", len(rejected))
    print(rejected["reject_reason"].value_counts())

    assert len(raw) == len(clean) + len(rejected), "Rows went missing!"
    rejected.to_csv("data/rejected_trips.csv", index=False)
    print(clean.dtypes)