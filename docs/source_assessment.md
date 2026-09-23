# Évaluation des sources

| Critère | Source A — retenue | Source B — écartée |
|---|---|---|
| Producteur et URL | Global Shark Attack File, extrait via Kaggle — [gauravkumar2525/shark-attacks](https://www.kaggle.com/datasets/gauravkumar2525/shark-attacks) | [Maven Analytics Data Playground — Shark Attacks](https://mavenanalytics.io/data-playground/shark-attacks) |
| Mode d'accès | Téléchargement direct du CSV | Téléchargement direct du CSV |
| Format | CSV, table unique | CSV, table unique |
| Fréquence de mise à jour | Ponctuelle, non garantie | Ponctuelle, non garantie |
| Volume | 6 890 lignes (extrait, 10 colonnes retenues) | 499 lignes, 25 champs |
| Clé ou identifiant | Aucune clé naturelle — ligne = un incident | Aucune clé naturelle — ligne = un incident |
| Licence / conditions | Conditions d'utilisation et licence à vérifier sur la page Kaggle avant redistribution; usage limité au TP | Conditions d'utilisation Maven Analytics à vérifier avant redistribution |
| Risque technique | Champs texte peu normalisés (pays, activité, âge) | Dataset plus petit, moins représentatif dans la durée |
| Données personnelles | Nom de la victime en clair sur certaines lignes — champ à exclure ou anonymiser en usage réel | Idem |

## Pourquoi la source A

Volume nettement supérieur (6 890 vs 499 lignes), échelle temporelle beaucoup plus large, et les colonnes disponibles couvrent directement les trois cas d'usage retenus (tendance temporelle, profil des victimes, gravité par pays). La source B reste une alternative de secours si la source A devenait indisponible.

## Limite à documenter

Le champ `name` contient des données personnelles identifiables (nom de victimes réelles). Il n'est pas utilisé dans le dataset curated ni dans les visualisations — il est conservé uniquement dans la zone raw à titre de traçabilité de la source, jamais republié.

## Reproductibilité de l'extrait

Le fichier exact utilisé par défaut est
`data/raw/global_shark_attacks_raw.csv`, conservé localement car le
téléchargement Kaggle peut nécessiter une session utilisateur. Le collecteur
ne contourne pas cette authentification et ne scrape pas le site.
La copie raw canonique et son SHA-256 sont inscrits dans
`reports/interpretation/run_report.json`. Pour reproduire un autre extrait,
passer explicitement son chemin à `python -m src.pipeline chemin/vers/fichier.csv`.
