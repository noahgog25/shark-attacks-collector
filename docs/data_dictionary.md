# Dictionnaire de données

## Grain et clé métier

Une ligne représente un incident déclaré dans le GSAF. La source ne fournit
pas d'identifiant stable : le pipeline déduplique sur l'ensemble des champs
source. Cette clé technique est reproductible mais peut fusionner deux
incidents distincts dont toutes les valeurs seraient identiques; elle ne
constitue pas une clé métier naturelle.

## Source brute

| Champ | Type attendu | Obligatoire | Description | Traitement |
|---|---|---:|---|---|
| `date` | date texte | Non | Date de l'incident | Convertie en `date_complete` |
| `year` | numérique | Oui | Année déclarée | Validée entre 1000 et l'année courante |
| `type` | catégorie | Oui | Type d'attaque | Doit appartenir aux catégories connues |
| `country` | texte | Oui | Pays déclaré | Rejet si absent |
| `area` | texte | Non | Zone ou région | Conservée et renommée `zone` |
| `location` | texte | Non | Localité déclarée | Conservée et renommée `localite` |
| `activity` | texte | Non | Activité de la victime | Valeur manquante remplacée par `Inconnue` |
| `name` | texte sensible | Non | Nom de la victime | Raw uniquement, jamais curated |
| `sex` | catégorie | Non | Sexe déclaré | Conservé seulement si `M` ou `F` |
| `age` | texte/numérique | Non | Âge déclaré | Extrait, puis validé dans [0, 120] |

## Dataset curated

Une ligne représente un incident accepté, transformé et dédupliqué.

| Champ | Type de sortie | Nullable | Description |
|---|---|---:|---|
| `date_complete` | datetime | Oui | Date complète interprétée |
| `annee` | Int64 | Oui | Année validée |
| `pays` | texte | Non | Pays normalisé en majuscules |
| `zone` | texte | Oui | Zone d'incident |
| `localite` | texte | Oui | Localité d'incident |
| `activite` | texte | Non | Activité, ou `Inconnue` |
| `type_attaque` | catégorie | Non | Type validé |
| `sexe` | catégorie | Oui | `M`, `F` ou null |
| `age` | Int64 | Oui | Âge nettoyé |
| `tranche_age` | texte | Oui | Tranche décennale calculée |

Les fichiers d'enrichissement géographique et GBIF ne remplacent pas ce
dataset principal. Ils conservent leur propre provenance et leurs incertitudes.

## Enrichissement environnemental facultatif

Le fichier généré `data/curated/attacks_enriched.csv` est ignoré par Git. Il ne
contient pas la colonne `name` ni les données brutes. `incident_id` est le
SHA-256 des champs curated et sert uniquement à rattacher les coordonnées au
même incident.

| Champ | Unité / type | Signification |
|---|---|---|
| `incident_id` | SHA-256 | Identifiant stable calculé sans nom personnel |
| `date` | date | Date retenue; le 1er janvier est exclu des tests d'hypothèse |
| `latitude`, `longitude` | degrés | Coordonnées géocodées; souvent un centre de localité, pas le point exact |
| `geocode_precision` | catégorie | Type de résultat géographique ou `centre_de_localite_approximatif` |
| `hemisphere` | `N` / `S` | Hémisphère déterminé par la latitude |
| `sst_c` | °C | SST NOAA OISST v2.1 à la date et cellule retenue |
| `sst_clim_c` | °C | Moyenne locale 1982–2011, fenêtre circulaire de 31 jours |
| `sst_anom_c` | °C | `sst_c - sst_clim_c`, anomalie calculée localement |
| `sst_anom_noaa_c` | °C | Anomalie fournie par NOAA, conservée comme référence |
| `sst_control_mean_c` | °C | Moyenne SST de jusqu'à 10 jours témoins de la même année et du même lieu |
| `air_tmax_c` | °C | Maximum journalier ERA5 à la position géocodée |
| `air_tmax_control_mean_c` | °C | Moyenne des jours témoins pour la température de l'air |
| `precip_mm`, `wind_max_kmh` | mm, km/h | Pluie et vent maximum journaliers ERA5 |
| `precip_control_mean_mm`, `wind_control_mean_kmh` | mm, km/h | Moyennes ERA5 pour les jours témoins |
| `precip_3d_mm` | mm | Pluie cumulée des trois jours précédant l'incident |
| `precip_3d_control_mean_mm` | mm | Moyenne des cumuls 3 jours précédant les jours témoins |
| `gbif_2025_2026_within_100km` | entier | Occurrences locales GBIF datées 2025–2026 dans un rayon de 100 km |
| `env_status` | catégorie | `OK`, `NO_OCEAN_CELL`, `PRE_1982`, `API_FAIL` ou fenêtre OISST dépassée |

Les contrôles sont tirés de façon reproductible (graine fixe) dans la même
année et au même lieu. Les exclusions (géocodage, date invalide, 1er janvier,
type provoqué, seuil temporel) sont comptées dans le rapport de run. Une
coordonnée de ville demeure approximative; aucune corrélation ou proximité ne
doit être interprétée comme une cause.