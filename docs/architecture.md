# Architecture

```
[Source locale]       [Collecteur]        [Zone raw]         [Validation]        [Zone curated]      [Application]
CSV fourni         ->  src/collect.py  ->  data/raw/      ->  src/validate.py ->  data/curated/   ->  src/visualize.py
(extrait autorisé,    (copie sans          (snapshot           (5 règles de        (données propres,    (rapports,
 conservé localement) transformation)      horodaté)           qualité)            typées, dédupliquées) graphiques)
                                                                   |
                                                                   v
                                                              [Zone rejected]
                                                              data/rejected/
                                                              (lignes écartées
                                                               + raison du rejet)
```

- **Source initiale** : extrait Kaggle / Global Shark Attack File, fourni localement sous `data/raw/global_shark_attacks_raw.csv` ou en argument.
- **Collecteur** (`src/collect.py`) : conserve une copie brute horodatée et non transformée pour chaque exécution.
- **Validation** (`src/validate.py`) : applique les 5 règles de qualité du contrat de données (`config/data_contract.yaml`), sépare accepté / rejeté.
- **Curated** (`src/transform.py`) : normalise et type les données acceptées, produit `data/curated/shark_attacks_curated.csv`.
- **Analyse** (`src/analyze.py`) : produit des hotspots d'incidents déclarés et une saisonnalité mensuelle. Ces sorties sont descriptives et ne mesurent pas la dangerosité biologique.
- **Application** : visualisation des attaques par année (`src/visualize.py`) et rapport d'exécution (`reports/interpretation/run_report.json`). Les sorties sont classées dans `reports/images/`, `reports/data/` et `reports/interpretation/`. Les observations OCEARCH, GBIF et SST sont conservées séparément dans `data/reference/` avant toute jointure documentée.

Le pipeline est batch et rejouable à l'identique (idempotence assurée par le remplacement complet des fichiers curated/rejected à chaque run). Les snapshots raw sont ignorés par Git car ils peuvent contenir des données nominatives.
