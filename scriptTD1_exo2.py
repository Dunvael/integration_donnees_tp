import pandas as pd
import time

# Lecture complète
start = time.time()
pd.read_csv("flight_data_2024.csv")
print(f"Lecture complète CSV : {time.time() - start:.2f} s")

start = time.time()
pd.read_parquet("flight_data_2024.parquet")
print(f"Lecture complète Parquet : {time.time() - start:.2f} s")

start = time.time()
pd.read_parquet("flight_data_2024_compressed.parquet")
print(f"Lecture complète Parquet compressé : {time.time() - start:.2f} s")

# Lecture ciblée : deux colonnes
cols = ["Airline", "DepDelay"]  # ex. une string et une integer
start = time.time()
pd.read_csv("flight_data_2024.csv", usecols=cols)
print(f"Lecture ciblée CSV : {time.time() - start:.2f} s")

start = time.time()
pd.read_parquet("flight_data_2024.parquet", columns=cols)
print(f"Lecture ciblée Parquet : {time.time() - start:.2f} s")
