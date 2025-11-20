# Livrables pour le TP - Cycle de vie de la donnée : de la source au Dashboard

*Formateur* : Mourad El Chyaki

*Membres du groupe* : 

* Aymeric BOISGONTIER
* Dunvael LE ROUX

Lien GitHub docker : <https://github.com/mouradelchyakhi/enseignement_epsi/tree/main/tp_docker_light>

---

# Étapes principales du projet

**Etape 1 - Connexion à OpenMetadata**

* Se connecter à l’instance OpenMetadata VeloCity
* Explorer les tables avec les tags utiles (ex. "Source", "PII")
* Lister les tables de fait et de dimension qui semblent pertinentes pour le dashboard

*Besoin client* : La direction Marketing souhaite un Dashboard pour suivre l'activité quotidienne : nombre de locations, durée moyenne des trajets, les vélos les plus utilisés, habitude par ville, âge des consommateurs, type d’abonnement pris, … etc

4. Tables et faits pertinents : 

* Bikes rentals -> (nbr de locations) / Start T- end T fait (vélos les + utilisés)
* Bikes Station -> Station ID, Station Name, Capacity fait
* Bikes -> Bike ID (type) et Status dimensions
* Cities -> City ID (city name) et region dimensions (habitudes et villes)
* Daily activity summary old -> Total rentals faits (évolution des rentals)
* Marketings campaigns ->  Start date et end date => à lier avec Start T- end de bike rentals faits
* Rental archives 2022 -> Start T et End T + Bike ID faits (historique des ventes d'une année à une autre)
* subscriptions -> sub type + sub ID Faits
* User accounts -> Birthdate + sud ID Faits => lier avec sub
* User session logs -> device type Faits (déterminer le type de connexion pour les lcoations - téléphone, web, ...)
* Weather forecast hourly -> Temperature Celsius et Precipitation Mm faits
* Bike maintenance logs -> Bike ID  et Issue description dimension et faits


| **Aspect** | **Table de faits**   | **Table de dimensions**   |
| ---------- | -------------------- | ------------------------- |
| Contenu    | Mesures, chiffres    | Descriptions, attributs   |
| Rôle       | Analyse quantitative | Contexte et qualification |
| Type       | Numérique            | Textuel / catégoriel      |
| Volume     | Très élevé           | Moyen / faible            |
| Exemple    | Montant des ventes   | Produit, magasin, client  |


**Etape 2 - Analyse des tables**

* Pour chaque table, consulter schéma, description, profils de données, documentation
* Identifier les anomalies potentielles (formats incohérents, valeurs manquantes)

Oui on relève des anomalies potentielles (null, station invalid/orpheline, coord_lon pas de chiffre) => cf captures d'écran.


| Table | Anomalies Principale | Correction à appliquer |  
| --- | --- | --- |  
| bike_maintenance_logs | Dates au format texte/timestamp mixte | Cast en DATE standard |
| bikes | "Types hétérogènes (""E-bike"" vs ""Electrique"")" | Standardisation via CASE WHEN |  
| bikes_rentals | Trajets < 2 min et IDs non standards | Filtre durée & Renommage colonnes |  
| bikes_station | "Lat/Lon en texte, Ville 99, Doublons" | Nettoyage Regex & suppression orphelins |  
| cities | Régions vides | "Remplacement par ""Region Inconnue"" |  
| daily_activity | Colonne date mal nommée | Renommage |  
| marketing_campaigns | Budgets vides | Remplacement par 0 |  
| rental_archives | Trajets < 2 min et IDs non standards | Filtre durée & Renommage colonnes |  
| subscriptions | Types d'abo vides | "Valeur par défaut ""Standard"" |  
| user_accounts | Dates FR/EN mélangées | Parsing intelligent avec Regex |  
| user_session_logs | Appareils inconnus | "Remplacement par ""unknown"" |  
| weather_forecast_hourly | Précipitations NULL | Remplacement par 0 |  

---

**Etape 3 - Création du schéma de transformation dans PostgreSQL**

* Création du schéma de transformation dans PostgreSQL : 
* Se connecter à la base PostgreSQL avec pgAdmin
* Créer un nouveau schéma pour les transformations

```
CREATE SCHEMA IF NOT EXISTS analytics_le_roux_boisgontier;
```

CF schéma capture d'écran

**Etape 4 - Nettoyage et transformation (Couche Silver)**

* Copier les données brutes dans ce schéma.
* Appliquer les corrections nécessaires :  Conversion de formats (dates, timestamps) Calculs dérivés (durée des trajets) Filtrage des valeurs aberrantes Standardisation de formats et valeurs

Création d'une table nettoyée par table brute, avec conversions de types, corrections de valeurs manquantes ou aberrantes, et ajouts de calculs métiers (durée, statuts, etc.).

Vérification du nom des tables dans le schéma RAW avec : 

```
sql 
SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
ORDER BY table_schema, table_name;
```

```
-- ==============================================================================
-- SCRIPT DE NETTOYAGE "SILVER" - CORRECTIFS COMPLETS
-- Objectif : Transformer les données brutes (Raw) en données fiables (Silver)
-- ==============================================================================

-- 1. Initialisation : On repart d'une page blanche pour le schéma cible
DROP SCHEMA IF EXISTS analytics_le_roux_boisgontier CASCADE;
CREATE SCHEMA analytics_le_roux_boisgontier;

-- ==============================================================================
-- TABLE 1 : STATIONS (Le plus gros nettoyage)
-- Anomalies traitées : Coordonnées texte, Noms nuls, Doublons, Villes inconnues
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.bikes_station AS
SELECT DISTINCT ON (station_name, city_id) -- Dédoublonnage strict
    station_id,
    station_name,
    -- Conversion forcée des coordonnées, NULL si c'est du texte
    CASE WHEN latitude ~ '^[0-9.-]+$' THEN latitude::numeric ELSE NULL END AS latitude,
    CASE WHEN longitude ~ '^[0-9.-]+$' THEN longitude::numeric ELSE NULL END AS longitude,
    COALESCE(capacity, 0) AS capacity,
    city_id
FROM raw.bike_stations
WHERE 
    station_name IS NOT NULL           -- Filtre noms vides
    AND latitude ~ '^[0-9.-]+$'        -- Filtre lat invalide
    AND longitude ~ '^[0-9.-]+$'       -- Filtre lon invalide
    AND city_id IN (SELECT city_id FROM raw.cities); -- Filtre villes fantômes (99)

-- ==============================================================================
-- TABLE 2 : VÉLOS (Standardisation)
-- Anomalies traitées : "E-bike"/"electrique", Statuts NULL
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.bikes AS
SELECT
    bike_id,
    -- Harmonisation du vocabulaire
    CASE 
        WHEN LOWER(bike_type) LIKE '%e-bike%' OR LOWER(bike_type) LIKE '%electrique%' THEN 'Electrique'
        ELSE INITCAP(bike_type) -- Met la 1ère lettre en majuscule (Mecanique)
    END AS bike_type,
    model_name,
    COALESCE(status, 'unknown') AS status,
    commissioning_date
FROM raw.bikes
WHERE bike_id IS NOT NULL;

-- ==============================================================================
-- TABLE 3 : UTILISATEURS (Le casse-tête des dates)
-- Anomalies traitées : Dates FR/EN mélangées, Âges > 100 ans
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.user_accounts AS
SELECT
    user_id,
    first_name,
    last_name,
    email,
    -- Détection et correction du format de date de naissance
    CASE 
        WHEN birthdate ~ '^\d{4}-\d{2}-\d{2}$' THEN TO_DATE(birthdate, 'YYYY-MM-DD')
        WHEN birthdate ~ '^\d{2}/\d{2}/\d{4}$' THEN TO_DATE(birthdate, 'DD/MM/YYYY')
        ELSE NULL 
    END AS birthdate,
    -- Même logique pour inscription
    CASE 
        WHEN registration_date ~ '^\d{4}-\d{2}-\d{2}$' THEN TO_DATE(registration_date, 'YYYY-MM-DD')
        WHEN registration_date ~ '^\d{2}/\d{2}/\d{4}$' THEN TO_DATE(registration_date, 'DD/MM/YYYY')
        ELSE NULL
    END AS registration_date,
    subscription_id AS sub_id
FROM raw.user_accounts
WHERE 
    user_id IS NOT NULL
    -- Filtre supplémentaire : On ignore les dates de naissance antérieures à 1920 (aberrations)
    AND (
        (birthdate ~ '^\d{4}' AND LEFT(birthdate, 4)::int > 1920) OR
        (birthdate ~ '^\d{2}/\d{2}/\d{4}$' AND RIGHT(birthdate, 4)::int > 1920)
    );

-- ==============================================================================
-- TABLE 4 : LOCATIONS (Filtres métier)
-- Anomalies traitées : Trajets < 2 min, Noms colonnes
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.bikes_rentals AS
SELECT
    rental_id AS id,
    bike_id,
    user_id,
    start_station_id AS station_start_id,
    end_station_id AS station_end_id,
    start_t::timestamp AS start_time,
    end_t::timestamp AS end_time,
    GREATEST(EXTRACT(EPOCH FROM (end_t::timestamp - start_t::timestamp))/60, 0) AS duration_minutes
FROM raw.bike_rentals
WHERE 
    start_t IS NOT NULL 
    AND end_t IS NOT NULL
    AND end_t > start_t -- La fin doit être après le début
    AND (EXTRACT(EPOCH FROM (end_t::timestamp - start_t::timestamp))/60) >= 2; -- Durée min 2 min

-- ==============================================================================
-- TABLE 5 : ARCHIVES LOCATIONS (Même traitement)
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.rental_archives_2022 AS
SELECT
    rental_id AS archive_id,
    bike_id,
    user_id,
    start_t::timestamp AS start_time,
    end_t::timestamp AS end_time,
    GREATEST(EXTRACT(EPOCH FROM (end_t::timestamp - start_t::timestamp))/60, 0) AS duration_minutes
FROM raw.rentals_archive_2022
WHERE 
    start_t IS NOT NULL 
    AND end_t > start_t
    AND (EXTRACT(EPOCH FROM (end_t::timestamp - start_t::timestamp))/60) >= 2;

-- ==============================================================================
-- TABLE 6 : VILLES
-- Anomalie : Régions manquantes
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.cities AS
SELECT
    city_id,
    city_name,
    COALESCE(region, 'Region Inconnue') AS region
FROM raw.cities
WHERE city_id IS NOT NULL;

-- ==============================================================================
-- TABLE 7 : MÉTÉO
-- Anomalie : Précipitations NULL -> 0
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.weather_forecast_hourly AS
SELECT
    forecast_time AS date_time,
    city_id,
    COALESCE(temperature_celsius, 0) AS temperature_celsius,
    COALESCE(precipitation_mm, 0) AS precipitation_mm
FROM raw.weather_forecast_hourly
WHERE forecast_time IS NOT NULL;

-- ==============================================================================
-- TABLES SIMPLES (Juste renommage/Typage standard)
-- ==============================================================================

-- 8. Maintenance
CREATE TABLE analytics_le_roux_boisgontier.bike_maintenance_logs AS
SELECT
    log_id AS maintenance_id,
    bike_id,
    issue_description,
    report_date::date AS maintenance_date,
    cost_eur
FROM raw.bike_maintenance_logs
WHERE bike_id IS NOT NULL;

-- 9. Campagnes Marketing
CREATE TABLE analytics_le_roux_boisgontier.marketing_campaigns AS
SELECT
    campaign_id,
    campaign_name,
    start_date,
    end_date,
    COALESCE(budget_eur, 0) AS budget_eur
FROM raw.marketing_campaigns
WHERE start_date IS NOT NULL;

-- 10. Abonnements
CREATE TABLE analytics_le_roux_boisgontier.subscriptions AS
SELECT
    subscription_id AS sub_id,
    COALESCE(subscription_type, 'Standard') AS sub_type,
    price_eur
FROM raw.subscriptions
WHERE subscription_id IS NOT NULL;

-- 11. Logs Session
CREATE TABLE analytics_le_roux_boisgontier.user_session_logs AS
SELECT
    session_id,
    user_id,
    COALESCE(device_type, 'unknown') AS device_type,
    login_time AS start_time,
    (login_time + (duration_seconds || ' seconds')::interval) AS end_time,
    duration_seconds
FROM raw.user_session_logs
WHERE login_time IS NOT NULL;

-- 12. Résumé Activité
CREATE TABLE analytics_le_roux_boisgontier.daily_activity_summary_old AS
SELECT
    summary_date AS date,
    COALESCE(total_rentals, 0) AS total_rentals,
    total_revenue_eur
FROM raw.daily_activity_summary_old
WHERE summary_date IS NOT NULL;
```

Les noms de colonnes sont adaptés aux attentes métiers du TP

**Etape 5 - Agrégation métier (Couche Gold)**

* Créer une table avec les métriques clefs agrégées au bon niveau (jour, ville, type vélo etc.) :  totalrentals, averagedurationminutes, uniqueusers, etc.
* Exemple de requête d'agrégation en SQL pour la table gold.

```
CREATE TABLE analytics_le_roux_boisgontier.gold_daily_activity AS
SELECT
    -- 1. Dimensions (Axes d'analyse)
    DATE(r.start_time) AS rental_date,       -- Granularité : Jour 
    c.city_name,                             -- Granularité : Ville 
    s.station_name,                          -- Granularité : Station 
    b.bike_type,                             -- Granularité : Type de vélo 
    sub.sub_type AS subscription_type,       -- Granularité : Abonnement 

    -- 2. Métriques (KPIs)
    COUNT(r.id) AS total_rentals,                        -- Nombre total de locations [cite: 44]
    ROUND(AVG(r.duration_minutes)::numeric, 2) AS average_duration_minutes, -- Durée moyenne [cite: 45]
    COUNT(DISTINCT r.user_id) AS unique_users            -- Utilisateurs uniques [cite: 45]

FROM 
    -- Table de faits (Silver)
    analytics_le_roux_boisgontier.bikes_rentals r
    
    -- Jointures vers les dimensions (Silver)
    JOIN analytics_le_roux_boisgontier.bikes b ON r.bike_id = b.bike_id
    JOIN analytics_le_roux_boisgontier.bikes_station s ON r.station_start_id = s.station_id
    JOIN analytics_le_roux_boisgontier.cities c ON s.city_id = c.city_id
    JOIN analytics_le_roux_boisgontier.user_accounts u ON r.user_id = u.user_id
    JOIN analytics_le_roux_boisgontier.subscriptions sub ON u.sub_id = sub.sub_id

GROUP BY
    DATE(r.start_time),
    c.city_name,
    s.station_name,
    b.bike_type,
    sub.sub_type;

-- Vérification rapide du résultat
SELECT * FROM analytics_le_roux_boisgontier.gold_daily_activity LIMIT 10;
```

Cf capture d'écran gold

**Etape 6 - Création du Dashboard dans Metabase**

* Ajouter la source PostgreSQL
* Importer la table gold comme dataset

**Cf capture d'écran**

* Créer les graphiques attendus : évolution des locations, top villes, KPI.
* Construire un dashboard final avec ces éléments.

Cf capture d'écran des dashboards

**Etape 7 - Identifier les rôles utilisateurs (ex : marketinguser)**

* Identifier les rôles utilisateurs (ex : marketinguser) :
* Implémenter les droits avec commandes SQL GRANT/REVOKE pour restreindre l'accès.
* Tester les permissions pour s’assurer que les données brutes ne sont pas accessibles
* Mettre en place une sécurité au niveau ligne si besoin (Row-level Security)

o Si marketing_user essaie de faire SELECT * FROM raw.user_accounts;, que doit-il 
se passer ? => il a permission denied cf capture
o Si il fait SELECT * FROM analytics_nom1_nom2.gold_daily_activity; ? => il a accès à tout cf capture

Script tâches revoke/grant et manager de Lyon :

```
-- ==============================================================================
-- PARTIE 4 : SÉCURITÉ ET GOUVERNANCE
-- Objectif : Gestion des droits (RBAC) et Row-Level Security (RLS)
-- ==============================================================================

-- 1. CRÉATION DU RÔLE MARKETING (Utilisateur global)
-- ------------------------------------------------------------------------------
-- On supprime le rôle s'il existe déjà pour pouvoir relancer le script
DROP ROLE IF EXISTS marketing_user;

-- Création du rôle avec un mot de passe
CREATE ROLE marketing_user WITH LOGIN PASSWORD 'password123';

-- SÉCURITÉ : On s'assure qu'il n'a accès à RIEN par défaut sur le schéma raw
REVOKE ALL ON SCHEMA raw FROM marketing_user;
REVOKE ALL ON ALL TABLES IN SCHEMA raw FROM marketing_user;

-- SÉCURITÉ : On donne l'accès SEULEMENT au schéma analytics (usage pour traverser)
GRANT USAGE ON SCHEMA analytics_le_roux_boisgontier TO marketing_user;

-- SÉCURITÉ : On donne le droit de lecture (SELECT) UNIQUEMENT sur la table Gold
GRANT SELECT ON TABLE analytics_le_roux_boisgontier.gold_daily_activity TO marketing_user;

-- ------------------------------------------------------------------------------
-- 2. ROW-LEVEL SECURITY (RLS) - MANAGER LYON
-- ------------------------------------------------------------------------------
DROP ROLE IF EXISTS manager_lyon;
CREATE ROLE manager_lyon WITH LOGIN PASSWORD 'lyon123';

-- Même accès de base que le marketing : Usage du schéma et Select sur la table
GRANT USAGE ON SCHEMA analytics_le_roux_boisgontier TO manager_lyon;
GRANT SELECT ON TABLE analytics_le_roux_boisgontier.gold_daily_activity TO manager_lyon;

-- ACTIVATION DE LA RLS SUR LA TABLE GOLD
-- Cela verrouille la table : personne ne voit rien sauf si une "POLICY" l'autorise
ALTER TABLE analytics_le_roux_boisgontier.gold_daily_activity ENABLE ROW LEVEL SECURITY;

-- CRÉATION DE LA POLITIQUE (POLICY) POUR LYON
-- Le manager_lyon ne verra que les lignes où city_name = 'Lyon'
DROP POLICY IF EXISTS lyon_access_policy ON analytics_le_roux_boisgontier.gold_daily_activity;

CREATE POLICY lyon_access_policy
ON analytics_le_roux_boisgontier.gold_daily_activity
FOR SELECT
TO manager_lyon
USING (city_name = 'Lyon');

-- CRÉATION DE LA POLITIQUE POUR LE MARKETING (GLOBAL)
-- Important : Une fois la RLS activée, il faut explicitement dire que le marketing voit TOUT (ou true)
-- Sinon, marketing_user ne verrait plus rien.
DROP POLICY IF EXISTS marketing_global_access ON analytics_le_roux_boisgontier.gold_daily_activity;

CREATE POLICY marketing_global_access
ON analytics_le_roux_boisgontier.gold_daily_activity
FOR SELECT
TO marketing_user
USING (true); -- 'true' signifie accès à toutes les lignes

-- ==============================================================================
-- 3. TESTS DE VÉRIFICATION (Simulation)
-- Exécutez ces blocs un par un pour tester
-- ==============================================================================

-- TEST A : Vérification Marketing (Doit voir toutes les villes)
SET ROLE marketing_user;
SELECT city_name, count(*) FROM analytics_le_roux_boisgontier.gold_daily_activity GROUP BY city_name;
-- Doit échouer (Permission denied) :
-- SELECT * FROM raw.user_accounts; 
RESET ROLE; -- Revenir admin

-- TEST B : Vérification Manager Lyon (Ne doit voir QUE Lyon)
SET ROLE manager_lyon;
SELECT city_name, count(*) FROM analytics_le_roux_boisgontier.gold_daily_activity GROUP BY city_name;
-- Résultat attendu : Une seule ligne 'Lyon'.
RESET ROLE;
```

---

# Livrables

## Partie 1

Un document (Markdown ou PDF) listant les tables sources identifiées et répondant aux questions posées.

--- 

## Partie 2

Un script SQL unique (.sql) contenant la création des schémas, tables, transformations

```
script SQL
```

---

## Partie 3

Une capture d’écran du Dashboard final

---

## Partie 4

Les commandes GRANT / REVOKE pour les accès (à ajouter au script de la partie 2)