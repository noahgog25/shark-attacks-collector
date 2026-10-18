# Évaluation des sources

| Critère | Source A — retenue | Source B — écartée |
|---|---|---|
| Producteur et URL | Global Shark Attack File, extrait via Kaggle — [gauravkumar2525/shark-attacks](https://www.kaggle.com/datasets/gauravkumar2525/shark-attacks) | [Maven Analytics Data Playground — Shark Attacks](https://mavenanalytics.io/data-playground/shark-attacks) |
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
