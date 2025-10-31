import pandas as pd
import os
import time

# 1. Chargement CSV
start = time.time()
df = pd.read_csv("flight_data_2024.csv")
end = time.time()
print(f"Temps de chargement CSV : {end - start:.2f} s")

# 2. Conversion en Parquet
df.to_parquet("flight_data_2024.parquet")
df.to_parquet("flight_data_2024_compressed.parquet", compression="snappy")

# 3. Analyse d’espace
size_csv = os.path.getsize("flight_data_2024.csv")
size_parquet = os.path.getsize("flight_data_2024.parquet")
size_parquet_comp = os.path.getsize("flight_data_2024_compressed.parquet")

print(f"Taille CSV : {size_csv/1e6:.2f} MB")
print(f"Taille Parquet : {size_parquet/1e6:.2f} MB")
print(f"Taille Parquet (compressé) : {size_parquet_comp/1e6:.2f} MB")

# 4. Taux de réduction
reduction_parquet = (1 - size_parquet / size_csv) * 100
reduction_parquet_comp = (1 - size_parquet_comp / size_csv) * 100
print(f"Réduction Parquet vs CSV : {reduction_parquet:.2f}%")
print(f"Réduction Parquet compressé vs CSV : {reduction_parquet_comp:.2f}%")