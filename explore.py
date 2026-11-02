
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