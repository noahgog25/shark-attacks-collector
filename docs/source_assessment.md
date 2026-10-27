# Évaluation des sources

| Critère | Source A — retenue | Source B — écartée |
|---|---|---|
| Producteur et URL | Dataset Kaggle « Sharks Attack collector », extrait du Global Shark Attack File (GSAF) — [gauravkumar2525/shark-attacks](https://www.kaggle.com/datasets/gauravkumar2525/shark-attacks) | [Maven Analytics Data Playground — Shark Attacks](https://mavenanalytics.io/data-playground/shark-attacks) |
| Mode d'accès | Téléchargement direct du CSV | Téléchargement direct du CSV |
| Format | CSV, table unique | CSV, table unique |
| Fréquence de mise à jour | Ponctuelle, non garantie | Ponctuelle, non garantie |
| Volume | 6 890 lignes (extrait, 10 colonnes retenues) | 499 lignes, 25 champs |
| Clé ou identifiant | Aucune clé naturelle — ligne = un incident | Aucune clé naturelle — ligne = un incident |
| Licence / conditions | Accès via Kaggle; licence et droit de redistribution de l'extrait local à confirmer avant toute remise publique. Le dépôt ne redistribue pas le CSV réel. | Conditions d'utilisation Maven Analytics à vérifier avant redistribution |
| Risque technique | Champs texte peu normalisés (pays, activité, âge) | Dataset plus petit, moins représentatif dans la durée |
| Données personnelles | Nom de la victime en clair sur certaines lignes — champ à exclure ou anonymiser en usage réel | Idem |

## Pourquoi la source A

Volume nettement supérieur (6 890 vs 499 lignes), échelle temporelle beaucoup plus large, et les colonnes disponibles couvrent directement les trois cas d'usage retenus (tendance temporelle, profil des victimes, gravité par pays). La source B reste une alternative de secours si la source A devenait indisponible.

## Limite à documenter

Le champ `name` contient des données personnelles identifiables (nom de victimes réelles). Il n'est pas utilisé dans le dataset curated ni dans les visualisations — il est conservé uniquement dans la zone raw à titre de traçabilité de la source, jamais republié.

## Reproductibilité de l'extrait

Le fichier `data/raw/global_shark_attacks_raw.csv` est un export local non
versionné, car il peut contenir des noms. Le collecteur ne contourne pas
l'authentification Kaggle et ne scrape pas le site. Pour un clone propre, un
échantillon synthétique non nominatif de 121 lignes est fourni sous
`data/samples/sample_source.csv`. Pour traiter un autre export autorisé,
passer son chemin à `python -m src.pipeline chemin/vers/fichier.csv`. Chaque
run conserve un snapshot raw horodaté; le rapport contient son nom et son
SHA-256. Vérifier les conditions de licence auprès du producteur avant de
redistribuer le CSV réel.

## Sources d'environnement (enrichissement facultatif)

| Source | Données utilisées | Couverture / accès | Attribution et limites |
|---|---|---|---|
| NOAA OISST v2.1, [ERDDAP griddap](https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.html) | `sst`, `anom`; grille quotidienne 0,25°; dimensions `time`, `zlev`, `latitude`, `longitude` | Requête par cellule unique; série analysée de 1982 à 2023; cellule de repli la plus proche à moins de 0,5° | Produit SST de NOAA; une cellule côtière terrestre peut manquer. La distance et les coordonnées de géocodage sont approximatives. |
| Open-Meteo [Archive API (ERA5)](https://archive-api.open-meteo.com/v1/archive) | `temperature_2m_max`, `precipitation_sum`, `wind_speed_10m_max` | Une requête par lieu unique et plage d'années, `timezone=auto` | Attribution obligatoire : Open-Meteo Archive (ERA5), CC BY 4.0. Les variables de météo ne mesurent pas la fréquentation humaine. |
| GBIF | Occurrences géolocalisées locales datées 2025–2026 | Réutilisation des exports présents dans `data/reference/`, sans requête pendant l'analyse | Piste secondaire : une présence proche ne prouve ni présence le jour de l'incident, ni espèce responsable. |

L'API Marine d'Open-Meteo n'est pas retenue : son historique de vagues est
trop court pour comparer de façon cohérente la série historique des incidents.
Les métadonnées CoastWatch live (`.html` et `.das`) n'étaient pas accessibles
lors de cette mise en œuvre; l'ordre des dimensions et les centres de grille
sont recoupés dans l'[ADR 002](ADR_002.md) et devront être revérifiés avant une
collecte complète.
L'enrichissement est opt-in (`python -m src.pipeline --enrich`). Les réponses
brutes sont mises en cache sous `data/raw/external/` par hash de requête,
réutilisées hors ligne, et exclues de Git. Une indisponibilité sans cache
produit `API_FAIL` et un statut d'enrichissement `WARN`, sans interrompre le
pipeline principal.

### Hypothèses et interprétation

Les hypothèses H1 à H5 sont testées contre jusqu'à dix jours témoins du même
lieu et de la même année (graine fixe). Les analyses excluent explicitement
les dates du 1er janvier, les dates invalides, les incidents non géocodés et,
si le type est présent, les incidents provoqués. Chaque filtre indique ses
volumes et sa part d'exclusion dans le rapport de run. Les résultats incluent
la taille d'échantillon, une différence médiane, Mann–Whitney, delta de Cliff
et IC bootstrap à 95 % lorsque les données le permettent. « Soutenue » indique
un signal statistique selon cette règle, jamais une causalité.
