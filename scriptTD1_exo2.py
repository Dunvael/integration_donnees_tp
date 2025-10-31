import pandas as pd
import hashlib, hmac, os, re, sys
from typing import Dict, List
try:
    from faker import Faker
except ImportError:
    print("La librairie 'faker' est requise. Installez-la avec: python -m pip install faker")
    sys.exit(1)

# ========= PARAMÈTRES =========
INPUT = r"clients_data.csv"  # adapte le chemin vers ton dataset
OUTPUT_ALL = r"clients_data_protege.csv"
SECRET_KEY = b"CHANGE_ME_WITH_A_SECURE_RANDOM_KEY"  # clé secrète pour HMAC (pseudonymes & hachage salé)
FAKER_LOCALE = "fr_FR"  # noms factices FR

# ========= OUTILS DE SÉCURITÉ =========
fake = Faker(FAKER_LOCALE)

# Caches pour cohérence (même entrée -> même sortie)
_CACHE_NOM = {}
_CACHE_PRENOM = {}

def deterministic_fake_name(key: str, which: str = "last") -> str:
    """
    Génère un nom/prénom factice COHÉRENT pour une même valeur source.
    which: 'last' ou 'first'
    """
    if not isinstance(key, str):
        key = str(key)
    cache = _CACHE_NOM if which == "last" else _CACHE_PRENOM
    if key in cache:
        return cache[key]
    # seed dérivé de la valeur pour cohérence
    seed_int = int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % (2**32)
    Faker.seed(seed_int)
    name = fake.last_name() if which == "last" else fake.first_name()
    cache[key] = name
    return name

def mask_phone(phone: str) -> str:
    """
    Masque un numéro de téléphone : conserve uniquement les 2 derniers chiffres visibles.
    Garde la ponctuation/espaces d'origine.
    Ex: 06 12 34 56 78 -> XX XX XX XX 78
    """
    if not isinstance(phone, str):
        phone = str(phone)
    digits = re.findall(r"\d", phone)
    if not digits:
        return phone
    keep = 2
    # recalculer une chaîne en remplaçant les chiffres sauf les keep derniers
    to_mask = max(0, len(digits) - keep)
    out = []
    digit_idx = 0
    for ch in phone:
        if ch.isdigit():
            if digit_idx < to_mask:
                out.append("X")
            else:
                out.append(ch)
            digit_idx += 1
        else:
            out.append(ch)
    return "".join(out)

def generalize_city_to_dept(row: pd.Series) -> str:
    """
    Généralisation 'ville_résidence' -> code départemental si possible.
    Méthode 1 (préférée): si 'code_postal' existe, on prend les 2 premiers chiffres.
    Méthode 2 (fallback): bucketiser par initiale de la ville (perte de précision, mais déterministe).
    """
    cp = None
    for k in ["code_postal", "CodePostal", "postal_code", "cp"]:
        if k in row and pd.notna(row[k]):
            cp = str(row[k])
            break
    if cp and re.match(r"^\d{5}$", cp):
        return cp[:2]  # département FR (approximation simple)
    # Fallback si pas de code postal exploitable
    ville_key = None
    for k in ["ville_résidence", "ville", "city"]:
        if k in row and pd.notna(row[k]) and str(row[k]).strip():
            ville_key = str(row[k]).strip().lower()
            break
    if ville_key:
        # ex: regrouper par 1re lettre comme "généralisation régionale" fictive
        return f"REG_{ville_key[0].upper()}"
    return "REG_INCONNU"

def salted_sha256(value: str, salt_key: bytes = SECRET_KEY) -> str:
    """
    Hachage SHA-256 salé (via HMAC pour résistance aux rainbow tables).
    """
    if value is None:
        value = ""
    mac = hmac.new(salt_key, value.encode("utf-8"), hashlib.sha256).hexdigest()
    return mac

def pseudonymize_id(value: str, secret_key: bytes = SECRET_KEY, length: int = 16) -> str:
    """
    Pseudonyme déterministe basé sur HMAC-SHA256(id).
    Retourne un identifiant court (length hex chars).
    """
    if value is None:
        value = ""
    token = hmac.new(secret_key, str(value).encode("utf-8"), hashlib.sha256).hexdigest()
    return token[:length]

# ========= CHARGEMENT =========
if not os.path.exists(INPUT):
    raise FileNotFoundError(f"Fichier introuvable: {INPUT}")

df = pd.read_csv(INPUT, low_memory=False)

# ========= MASQUAGE =========
# Noms / prénoms -> valeurs factices cohérentes
if "nom" in df.columns:
    df["nom_masque"] = df["nom"].apply(lambda x: deterministic_fake_name(str(x), which="last"))
if "prénom" in df.columns:
    df["prenom_masque"] = df["prénom"].apply(lambda x: deterministic_fake_name(str(x), which="first"))
elif "prenom" in df.columns:
    df["prenom_masque"] = df["prenom"].apply(lambda x: deterministic_fake_name(str(x), which="first"))

# Téléphone masqué
for tel_col in ["téléphone", "telephone", "tel", "phone"]:
    if tel_col in df.columns:
        df[f"{tel_col}_masque"] = df[tel_col].apply(mask_phone)
        break  # masque une colonne de téléphone

# ========= ANONYMISATION / GÉNÉRALISATION =========
# ville_résidence -> code départemental (ou REG_X fallback)
if "ville_résidence" in df.columns or "ville" in df.columns or "city" in df.columns:
    df["ville_generalisee"] = df.apply(generalize_city_to_dept, axis=1)

# ========= PSEUDONYMISATION / HACHAGE =========
# id_client -> pseudonyme
id_col = None
for k in ["id_client", "client_id", "id"]:
    if k in df.columns:
        id_col = k
        break

if id_col:
    df["id_client_pseudo"] = df[id_col].apply(lambda x: pseudonymize_id(str(x)))

# email -> hachage (simulation de chiffrement)
email_col = None
for k in ["email", "mail", "courriel"]:
    if k in df.columns:
        email_col = k
        break

if email_col:
    df["email_hash"] = df[email_col].apply(lambda x: salted_sha256(str(x)))

# ========= SAUVEGARDE VERSION PROTÉGÉE =========
df.to_csv(OUTPUT_ALL, index=False)
print(f"✅ Données protégées sauvegardées : {OUTPUT_ALL}")

# ========= RBAC =========
RBAC_COLUMNS: Dict[str, List[str]] = {
    "Analyste_Marketing": [
        "id_client_pseudo", "montant_achat", "ville_generalisee"
    ],
    "Support_Client_N1": [
        "id_client_pseudo", "nom_masque", "prenom_masque",
        # on essaie de trouver la colonne téléphone masquée créée plus haut
        next((c for c in df.columns if c.endswith("_masque") and ("tel" in c or "phone" in c or "téléphone" in c)), None),
        "montant_achat"
    ],
    "Admin_Sécurité": list(df.columns)  # accès complet (y compris hash email)
}

def get_data_by_role(role: str, dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Simule un contrôle d'accès par rôle en restreignant les colonnes visibles.
    - Ignore silencieusement les colonnes manquantes (robuste au schéma).
    """
    if role not in RBAC_COLUMNS:
        raise ValueError(f"Rôle inconnu: {role}. Choisissez parmi: {list(RBAC_COLUMNS)}")
    cols = [c for c in RBAC_COLUMNS[role] if c and (c in dataframe.columns)]
    return dataframe.loc[:, cols]

# ========= DÉMONSTRATION =========
for role in ["Analyste_Marketing", "Support_Client_N1", "Admin_Sécurité"]:
    print(f"\n--- Vue RBAC: {role} ---")
    try:
        view = get_data_by_role(role, df)
        print(view.head(5).to_string(index=False))
    except Exception as e:
        print(f"Erreur pour {role}: {e}")

# ========= NOTES POUR LE COMPTE-RENDU =========
notes = """
[Notes TD – Exercice 2]

• Masquage:
  - nom/prénom remplacés par des valeurs Faker cohérentes (même source -> même masque).
  - téléphone: conservation des 2 derniers chiffres, reste masqué.

• Anonymisation (Généralisation):
  - ville_résidence généralisée en code département (2 premiers chiffres du code postal).
  - fallback: REG_X si code postal indisponible (perte volontaire de précision).

• Pseudonymisation / Hachage:
  - id_client -> pseudonyme HMAC-SHA256(id, SECRET_KEY), tronqué (stable & non réversible sans clé).
  - email -> HMAC-SHA256(email, SECRET_KEY) (simulation d’un chiffrement en prod).

• En production: Chiffrement symétrique vs asymétrique
  - Symétrique (ex: AES-GCM): une clé K unique protège/déchiffre; stocker K dans un KMS (AWS KMS, Azure Key Vault, GCP KMS) et appliquer une politique RBAC stricte. Rotation régulière des clés.
  - Asymétrique (RSA/ECDSA): la clé publique chiffre, seule la clé privée (protégée en HSM/KMS) peut déchiffrer. Pratique pour partager l’ingestion sans exposer la clé de déchiffrement.
  - Toujours journaliser (audit), chiffrer “au repos” (at-rest) et “en transit” (TLS), et segmenter les droits (principe du moindre privilège).

• RBAC:
  - get_data_by_role(role, df) restreint les colonnes selon le rôle (marketing: agrégé/anonymisé; support: PII masquées; admin sécurité: complet).
  - En environnement réel: implémenter côté entrepôt/Cloud via rôles IAM (ex: AWS IAM + Lake Formation, GCP IAM + BigQuery Column ACLs, Azure Purview/SQL RBAC) et “column/row-level security”. Les clés de chiffrement restent gérées par KMS/HSM et jamais exposées aux utilisateurs finaux.
"""
print(notes)
