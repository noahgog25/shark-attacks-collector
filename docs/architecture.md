# Architecture

```
[Kaggle CSV]        [Collecteur]        [Zone raw]         [Validation]        [Zone curated]      [Application]
data/source/    ->  src/collect.py  ->  data/raw/      ->  src/validate.py ->  data/curated/   ->  src/visualize.py
(source figée,       (copie horodatée,   (immuable,          (5 règles de        (données propres,    (rapports,
 propriété Kaggle)     jamais modifiée)    jamais réécrite)    qualité)            typées, dédupliquées)  graphiques)
                                                                   |
                                                                   v
                                                              [Zone rejected]
                                                              data/rejected/
                                                              (lignes écartées
                                                               + raison du rejet)
```

- **Source** : `data/source/global_shark_attacks-selected-columns.csv`, propriété Kaggle / Global Shark Attack File, jamais modifiée.
- **Collecteur** (`src/collect.py`) : copie horodatée vers `data/raw/`, une nouvelle preuve de collecte à chaque exécution.
- **Validation** (`src/validate.py`) : applique les 5 règles de qualité du contrat de données (`config/data_contract.yaml`), sépare accepté / rejeté.
- **Curated** (`src/transform.py`) : normalise et type les données acceptées, produit `data/curated/global_shark_attacks-selected-columns.csv`.
- **Analyse** (`src/analyze.py`) : produit des hotspots d'incidents déclarés et une saisonnalité mensuelle. Ces sorties sont descriptives et ne mesurent pas la dangerosité biologique.
- **Application** : visualisation des attaques par année (`src/visualize.py`) et rapport d'exécution (`reports/run_report.json`). Les observations OCEARCH, GBIF et SST seront conservées séparément dans `data/reference/` avant toute jointure documentée.

Le pipeline est batch et rejouable à l'identique (idempotence assurée par le remplacement complet des fichiers curated/rejected à chaque run).
