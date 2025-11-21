import pandas as pd
import os, time

# === Paramètres ===
CSV = r"C:\Users\IDLE6450\OneDrive - France Travail\Documents\EPSI - Cours\Data Management\Mourad\TD1\flight_data_2024.csv"
PQ  = r"C:\Users\IDLE6450\OneDrive - France Travail\Documents\EPSI - Cours\Data Management\Mourad\TD1\flight_data_2024.parquet"          # non compressé
PQS = r"C:\Users\IDLE6450\OneDrive - France Travail\Documents\EPSI - Cours\Data Management\Mourad\TD1\flight_data_2024_snappy.parquet"  # snappy
PQZ = r"C:\Users\IDLE6450\OneDrive - France Travail\Documents\EPSI - Cours\Data Management\Mourad\TD1\flight_data_2024_zstd.parquet"    # zstd (bonus)

# === 0) Inspecter les colonnes réelles du CSV ===
# nrows=0 lit uniquement l'en-tête, très rapide
cols_all = pd.read_csv(CSV, nrows=0).columns.tolist()
print(f"\nColonnes détectées ({len(cols_all)}): {cols_all[:12]}{' ...' if len(cols_all)>12 else ''}")

# === 1) Charger le CSV (avec low_memory=False pour éviter DtypeWarning) ===
t0 = time.time()
df = pd.read_csv(CSV, low_memory=False)
print(f"Temps lecture CSV : {time.time()-t0:.2f}s")

# === 2) Écrire en Parquet : non compressé vs snappy vs zstd ===
# IMPORTANT : pour avoir un "Parquet simple", il faut compression=None
df.to_parquet(PQ,  engine="pyarrow", compression=None)
df.to_parquet(PQS, engine="pyarrow", compression="snappy")
df.to_parquet(PQZ, engine="pyarrow", compression="zstd")  # souvent plus compact que snappy

# === 3) Tailles + taux de réduction vs CSV ===
def size_mb(p): return os.path.getsize(p)/1e6

size_csv = size_mb(CSV)
size_pq  = size_mb(PQ)
size_pqs = size_mb(PQS)
size_pqz = size_mb(PQZ)

print(f"\nTailles :")
print(f"CSV     : {size_csv:.2f} MB")
print(f"Parquet : {size_pq:.2f} MB (compression=None)")
print(f"Snappy  : {size_pqs:.2f} MB")
print(f"ZSTD    : {size_pqz:.2f} MB")

def reduc(a, b):  # % de réduction de b vers a
    return (1 - a/b) * 100

print(f"\nRéductions vs CSV :")
print(f"Parquet (no-comp) : {reduc(size_pq,  size_csv):.2f}%")
print(f"Snappy            : {reduc(size_pqs, size_csv):.2f}%")
print(f"ZSTD              : {reduc(size_pqz, size_csv):.2f}%")

# === 4) Choisir 1 colonne string + 1 colonne numérique existantes ===
# On détecte sur le DataFrame chargé
obj_cols = [c for c in df.columns if df[c].dtype == "object"]
num_cols = [c for c in df.columns if pd.api.types.is_integer_dtype(df[c]) or pd.api.types.is_float_dtype(df[c])]

if not obj_cols or not num_cols:
    raise RuntimeError("Impossible de trouver une colonne string ET une colonne numérique dans le CSV.")

str_col = obj_cols[0]
num_col = num_cols[0]
cols = [str_col, num_col]
print(f"\nColonnes choisies pour la lecture ciblée : string='{str_col}' | numeric='{num_col}'")

# === 5) Mesures de lecture complète ===
t0 = time.time(); _ = pd.read_parquet(PQ,  engine="pyarrow");  print(f"Lecture complète Parquet (no-comp) : {time.time()-t0:.2f}s")
t0 = time.time(); _ = pd.read_parquet(PQS, engine="pyarrow");  print(f"Lecture complète Parquet (snappy)  : {time.time()-t0:.2f}s")
t0 = time.time(); _ = pd.read_parquet(PQZ, engine="pyarrow");  print(f"Lecture complète Parquet (zstd)    : {time.time()-t0:.2f}s")

# === 6) Mesures de lecture ciblée (2 colonnes) ===
t0 = time.time(); _ = pd.read_csv(CSV, usecols=cols);                                   print(f"CSV (2 cols)          : {time.time()-t0:.2f}s")
t0 = time.time(); _ = pd.read_parquet(PQ,  engine="pyarrow", columns=cols);             print(f"Parquet no-comp (2 c) : {time.time()-t0:.2f}s")
t0 = time.time(); _ = pd.read_parquet(PQS, engine="pyarrow", columns=cols);             print(f"Parquet snappy  (2 c) : {time.time()-t0:.2f}s")
t0 = time.time(); _ = pd.read_parquet(PQZ, engine="pyarrow", columns=cols);             print(f"Parquet zstd    (2 c) : {time.time()-t0:.2f}s")
