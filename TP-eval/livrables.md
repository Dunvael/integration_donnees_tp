# Livrables pour le TP - Cycle de vie de la donnée : de la source au Dashboard

*Formateur* : Mourad El Chyaki

*Membres du groupe* : 

* Aymeric 
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

**Etape 3 - Création du schéma de transformation dans PostgreSQL**

* Création du schéma de transformation dans PostgreSQL : 
* Se connecter à la base PostgreSQL avec pgAdmin
* Créer un nouveau schéma pour les transformations
* 
```
CREATE SCHEMA IF NOT EXISTS analytics_votreNom_silver;
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
-- 1. TABLE DE FAITS : LOCATIONS (TRANSACTIONS)
-- Cette table enregistre l'événement principal : la location d'un vélo.
-- Transformations : Conversion timestamps, calcul de durée, exclusion des trajets impossibles.
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.bikes_rentals AS
SELECT
    id,
    bike_id,             -- FK vers Dimension Bikes
    user_id,             -- FK vers Dimension Users
    station_start_id,    -- FK vers Dimension Stations
    station_end_id,      -- FK vers Dimension Stations
    start_time::timestamp AS start_time,
    end_time::timestamp AS end_time,
    -- Calcul de la durée en minutes. GREATEST assure qu'on a pas de durée négative.
    GREATEST(EXTRACT(EPOCH FROM (end_time::timestamp - start_time::timestamp))/60, 0) AS duration_minutes
FROM raw.bikes_rentals
WHERE 
    start_time IS NOT NULL
    AND end_time IS NOT NULL
    AND end_time > start_time;

-- ==============================================================================
-- 2. TABLE DE DIMENSION : STATIONS
-- Contexte : Où se trouvent les vélos ?
-- Transformations : Gestion des capacités nulles (par défaut à 0).
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.bikes_station AS
SELECT
    station_id,   -- PK
    station_name,
    COALESCE(capacity, 0) AS capacity 
FROM raw.bikes_station
WHERE station_id IS NOT NULL AND station_name IS NOT NULL;

-- ==============================================================================
-- 3. TABLE DE DIMENSION : VÉLOS (BIKES)
-- Contexte : Quel équipement a été utilisé ?
-- Transformations : Gestion des statuts inconnus.
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.bikes AS
SELECT
    bike_id,      -- PK
    bike_type,
    COALESCE(status, 'unknown') AS status
FROM raw.bikes
WHERE bike_id IS NOT NULL;

-- ==============================================================================
-- 4. TABLE DE DIMENSION : VILLES (CITIES)
-- Contexte : Géographie des stations.
-- Transformations : Région par défaut si vide.
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.cities AS
SELECT
    city_id,      -- PK
    city_name,
    COALESCE(region, 'inconnue') AS region
FROM raw.cities
WHERE city_id IS NOT NULL;

-- ==============================================================================
-- 5. TABLE D'AGRÉGAT (FAITS PRÉ-CALCULÉS)
-- Résumé quotidien historique. Utile pour les tableaux de bord rapides.
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.daily_activity_summary_old AS
SELECT
    date::date AS date,
    COALESCE(total_rentals, 0) AS total_rentals
FROM raw.daily_activity_summary_old
WHERE date IS NOT NULL;

-- ==============================================================================
-- 6. TABLE DE DIMENSION : CAMPAGNES MARKETING
-- Contexte : Pourquoi y a-t-il des pics de ventes ?
-- Transformations : Cast des dates au format timestamp.
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.marketing_campaigns AS
SELECT
    campaign_id,   -- PK
    campaign_name,
    start_date::timestamp AS start_date,
    end_date::timestamp AS end_date
FROM raw.marketing_campaigns
WHERE start_date IS NOT NULL AND end_date IS NOT NULL;

-- ==============================================================================
-- 7. TABLE DE FAITS : ARCHIVES 2022
-- Données froides (historique). Même structure que bikes_rentals.
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.rental_archives_2022 AS
SELECT
    archive_id,
    bike_id,
    start_time::timestamp AS start_time,
    end_time::timestamp AS end_time,
    GREATEST(EXTRACT(EPOCH FROM (end_time::timestamp - start_time::timestamp))/60, 0) AS duration_minutes
FROM raw.rental_archives_2022
WHERE start_time IS NOT NULL AND end_time IS NOT NULL AND end_time > start_time;

-- ==============================================================================
-- 8. TABLE DE DIMENSION (ou TABLE DE LIEN) : ABONNEMENTS
-- Relie un utilisateur à un type d'abonnement.
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.subscriptions AS
SELECT
    sub_id,
    sub_type,
    user_id
FROM raw.subscriptions
WHERE sub_id IS NOT NULL;

-- ==============================================================================
-- 9. TABLE DE DIMENSION : UTILISATEURS (ACCOUNTS)
-- Contexte : Qui loue les vélos ? (Âge, type d'abonnement)
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.user_accounts AS
SELECT
    user_id,       -- PK
    birthdate::date AS birthdate,
    sub_id         -- FK vers Subscriptions
FROM raw.user_accounts
WHERE user_id IS NOT NULL AND birthdate IS NOT NULL;

-- ==============================================================================
-- 10. TABLE DE FAITS : LOGS DE SESSION
-- Événements numériques (logs). Granularité fine (clic/connexion).
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.user_session_logs AS
SELECT
    session_id,
    user_id,
    COALESCE(device_type, 'unknown') AS device_type,
    start_time::timestamp AS start_time,
    end_time::timestamp AS end_time
FROM raw.user_session_logs
WHERE start_time IS NOT NULL AND end_time IS NOT NULL AND user_id IS NOT NULL;

-- ==============================================================================
-- 11. TABLE DE FAITS : MÉTÉO HORAIRE
-- Mesures environnementales. Souvent utilisée pour corréler avec les ventes.
-- Transformations : Gestion des valeurs nulles pour température/pluie.
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.weather_forecast_hourly AS
SELECT
    date_time::timestamp AS date_time,
    city_id,
    COALESCE(temperature_celsius, 0) AS temperature_celsius,
    COALESCE(precipitation_mm, 0) AS precipitation_mm
FROM raw.weather_forecast_hourly
WHERE date_time IS NOT NULL AND city_id IS NOT NULL;

-- ==============================================================================
-- 12. TABLE DE FAITS : MAINTENANCE
-- Événements techniques sur les vélos.
-- ==============================================================================
CREATE TABLE analytics_le_roux_boisgontier.bike_maintenance_logs AS
SELECT
    maintenance_id,
    bike_id,
    issue_description,
    maintenance_date::date AS maintenance_date
FROM raw.bike_maintenance_logs
WHERE bike_id IS NOT NULL AND maintenance_date IS NOT NULL;
```

Les noms de colonnes sont adaptés aux attentes métiers du TP

**Etape 5 - Agrégation métier (Couche Gold)**

* Créer une table avec les métriques clefs agrégées au bon niveau (jour, ville, type vélo etc.) :  totalrentals, averagedurationminutes, uniqueusers, etc.
* Exemple de requête d'agrégation en SQL pour la table gold.

**Etape 6 - Création du Dashboard dans Metabase**

* Ajouter la source PostgreSQL
* Importer la table gold comme dataset
* Créer les graphiques attendus : évolution des locations, top villes, KPI.
* Construire un dashboard final avec ces éléments.

**Etape 7 - Identifier les rôles utilisateurs (ex : marketinguser)**

* Identifier les rôles utilisateurs (ex : marketinguser) :
* Implémenter les droits avec commandes SQL GRANT/REVOKE pour restreindre l'accès.
* Tester les permissions pour s’assurer que les données brutes ne sont pas accessibles
* Mettre en place une sécurité au niveau ligne si besoin (Row-level Security)


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

---

## Commandes utiles

### How to run