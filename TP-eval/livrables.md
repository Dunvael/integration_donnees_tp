# Livrables pour le TP - Cycle de vie de la donnée : de la source au Dashboard - 1ère Version du TP

*Formateur* : Mourad Elchyakhi

*Membres du groupe* : 

* Aymeric BOISGONTIER
* Dunvael LE ROUX

---

# Projet

## Objectifs

=> Simuler un projet data complet, de la découverte de la donnée brute à la création d'un Dashboard décisionnel, en intégrant les bonnes pratiques de modélisation (Médaillon) et de sécurité.

## Outils

OpenMetadata(image Docker complète seulement), PostgreSQL, Metabase.

## Scénario

Vous êtes Data Engineer/Analyst chez "VéloCity", une entreprise de location de vélos en libre-service. La direction Marketing souhaite un Dashboard pour suivre l'activité quotidienne : nombre de locations, durée moyenne des trajets, les vélos les plus utilisés, habitude par ville, âge des consommateurs, type d’abonnement pris, ... etc.

Lien GitHub docker : <https://github.com/mouradelchyakhi/enseignement_epsi/tree/main/tp_docker_light>

---

# Étapes du projet

## Partie 1 : Découverte et Compréhension (OpenMetadata ou fichier yaml)

***Objectif*** : Identifier les données sources pertinentes pour répondre aux besoins métiers.

### 1. Nous nous sommes connectés à l'instance OpenMetadata de "VéloCity"

![Bienvenue sur Metabase](./Images/Part1/connexion_metabase1.PNG)
![Création compte 1](./Images/Part1/connexion_metabase2.PNG)
![Création compte 2](./Images/Part1/connexion_metabase3.PNG)

Nous avons ensuite ajouté la base de données :

![Ajout de la base de données](./Images/Part1/connexion_metabase4.PNG)
![Metabase Accueil](./Images/Part1/connexion_metabase5.PNG)

---

### 2. Exploration d'OpenMetadata

* Nous avons navigué dans le catalogue et identifié les tables qui semblent pertinentes pour ce TP.

* Nous avons utilisé la recherche et les "Tags" (ex: "Source", "PII") pour trouver les bonnes tables.  

### 3. Analyse des tables sur OpenMetadata

* Nous avons analysé (quand disponible) les schémas, documentations, profils de données et propriétaires.

### 4. Tables et faits pertinents

Après réflexion et analyse, nous sommes partis sur ces douze tables de données qui permettent de réaliser des dashboards complets et croisés :

<p align="center">
  <img src="./Images/Part1/tables_choisies.webp" alt="Tables et faits pertinents">
</p>

=> Avant de justifier les choix de tables et de déterminer s'il s'agit de tables de faits ou de dimensions, nous avons défini et synthétisé les cacarctéristiques d'une table de fait et d'une table de dimensions dans un tableau :

| **Aspect** | **Table de faits**   | **Table de dimensions**   |
| :--------: | :------------------: | :-----------------------: |
| Contenu    | Mesures, chiffres    | Descriptions, attributs   |
| Rôle       | Analyse quantitative | Contexte et qualification |
| Type       | Numérique            | Textuel / catégoriel      |
| Volume     | Très élevé           | Moyen / faible            |
| Fréquence d'ajout de lignes/données | Très élevée | Peu élevée |
| Exemple    | Montant des ventes   | Produit, magasin, client  |

*Il est possible d'avoir une table de faits et de dimensions associés*.

**Justification des tables et attribution Fait/Dimension :**

| **Tables** | **Données sélectionnés**   | **justification**   | **Faits** | **Dimensions** |  
| :---------: | :-------------------------: | :------------------: | :--------: | :-------------: |
| Bikes rentals | Nombre de locations / Start T - End T | Vélos les plus utilisés  | &#x2611;  |   |
| Bikes Station |  Station ID, Station Name, Capacity   |   | &#x2611;  |   |
| Bikes | Bike ID (type) et Status |   | &#x2611; |   |
| Cities | City ID (city name), Regions |   |   | &#x2611;  |
| Daily activity summary old | Total rentals | évolution des rentals | &#x2611; |   |
| Marketings campaigns | Start date, End date | à lier avec Start T- end de bike rentals | &#x2611; |   |
| Rental archives 2022 | Start T, End T, Bike ID | historique des ventes d'une année à une autre | &#x2611; |   |
| Subscriptions | Sub type, Sub ID |   | &#x2611; |   |
| User accounts | Birthdate, Sub ID | lier avec sub | &#x2611; |   |
| User session logs | Device type | Déterminer le type de connexion pour les locations, téléphone, web, ...  | &#x2611; |   |
| Bike maintenance logs | Bike ID  et Issue description |   | &#x2611; | &#x2611; |
| Weather forecast hourly |  Temperature Celsius, Precipitations Mm |   | &#x2611; | |

---

## Partie 2 : Modélisation et Transformation (PostgreSQL)

### 1. Connection à la base PostGreSQL

Nous nous sommes connectés à la base PostgreSQL avec pgAdmin.

![Connexion pgAdmin 1](./Images/Part1/connexion_pgAdmin1.PNG)
![Connexion pgAdmin 2](./Images/Part1/connexion_pgAdmin2.PNG)
![Connexion Serveur EPSI 1](./Images/Part1/connexion_pgAdmin3_epsi-server.PNG)
![Connexion Serveur EPSI 2](./Images/Part1/connexion_pgAdmin3_epsi-server2.PNG)
![Connexion Serveur EPSI 3](./Images/Part1/connexion_pgAdmin3_epsi-server3.PNG)

Nous trouvons les mêmes informations, la différence réside dans l'interface utilisateur (visuel et présentation).  

Exemple :

<p align="center">
  <img src="./Images/Part2/diff_metadata_pgadmin1.webp" alt="Données pour la table Bike Rentals sur pgAdmin">
</p>

<p align="center">
  <img src="./Images/Part2/diff_metadata_pgadmin2.webp" alt="Données pour la table Bike Rentals sur Metadata">
</p>

Nous avons relevés des anomalies potentielles (doublons, manque de données ou "null" ou "inconnu", problème de nommage de colonne, IDs non standard, type hétérogène, dates au format texte/timestamp mixte...).  

Exemple :

<p align="center">
  <img src="./Images/Part2/problemes_releves_oui.webp" alt="Problèmes relevés">
</p>

Puis nous avons réalisé un tableau reccueillant les différentes anomalies pour les tables que nous avons sélectionnées :

| Table | Anomalies Principale | Correction à appliquer |  
| ----- | -------------------- | ---------------------- |  
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

Nous avons ensuite créé un nouveau schéma pour les transformations avec la commande SQL suivante :

```
CREATE SCHEMA IF NOT EXISTS analytics_le_roux_boisgontier;
```

<p align="center">
  <img src="./Images/Part2/nouveau_schema_transformations.webp" alt="Nouveau schéma de transformations">
</p>

### 2. Couche Silver (raffinage)

Afin de nettoyer, typer et standardiser les données brutes pour qu'elles soient exploitables, nous avons créé une table nettoyée avec conversions de types, corrections de valeurs manquantes ou aberrantes, et ajouts de calculs métiers (durée, statuts, etc.).

***Cf. le fichier script SQl_unique.sql qui contient la création des schémas, tables, transformations et commandes GRANT et REVOKE pour les accès.***

Nous avons requêté en amont PostgreSQL afin de lister les tables présentes pour notre script SQL :

```
SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
ORDER BY table_schema, table_name;
```

### 3. Couche Gold (Agrégation métier)

Afin de créer une table prête à l'emploi pour le Dashboard et répondant au besoin métier, nous avons créé une table avec les métriques clefs agrégées au bon niveau (jour, ville, type vélo etc.) :  totalrentals, averagedurationminutes, uniqueusers, etc :

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

<p align="center">
  <img src="./Images/Part2/couche_gold.webp" alt="Table Couche Gold">
</p>

---

# Partie 3 : Visualisation (Metabase)

Afin de créer un Dashboard simple pour le métier Marketing, nous nous sommes connectés à Metabase et avons ajouté la table 

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