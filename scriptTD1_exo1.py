import pandas as pd
import time, os

CSV = r"C:\Users\IDLE6450\OneDrive - France Travail\Documents\EPSI - Cours\Data Management\Mourad\flight_data_2024.csv"
PQ  = r"C:\Users\IDLE6450\OneDrive - France Travail\Documents\EPSI - Cours\Data Management\Mourad\flight_data_2024.parquet"
PQC = r"C:\Users\IDLE6450\OneDrive - France Travail\Documents\EPSI - Cours\Data Management\Mourad\flight_data_2024_snappy.parquet"

# Chargement CSV
t0 = time.time()
df = pd.read_csv(CSV)
print(f"Temps lecture CSV: {time.time()-t0:.2f}s")

# Écriture Parquet (pyarrow)
df.to_parquet(PQ, engine="pyarrow")
df.to_parquet(PQC, engine="pyarrow", compression="snappy")

# Tailles
for p in [CSV, PQ, PQC]:
    print(p, f"{os.path.getsize(p)/1e6:.2f} MB")

# Lecture complète
t0 = time.time(); pd.read_parquet(PQ, engine="pyarrow");  print(f"Parquet: {time.time()-t0:.2f}s")
t0 = time.time(); pd.read_parquet(PQC, engine="pyarrow"); print(f"Parquet (snappy): {time.time()-t0:.2f}s")

# Lecture ciblée de 2 colonnes
cols = ["Airline", "DepDelay"]  # adapte aux noms réels
t0 = time.time(); pd.read_csv(CSV, usecols=cols);                 print(f"CSV (2 cols): {time.time()-t0:.2f}s")
t0 = time.time(); pd.read_parquet(PQ,  engine="pyarrow", columns=cols); print(f"Parquet (2 cols): {time.time()-t0:.2f}s")
