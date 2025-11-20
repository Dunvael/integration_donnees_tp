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