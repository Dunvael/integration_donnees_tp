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
-- TABLES SIMPLES (Renommage/Typage standard)
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