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
- **Analyse** (`src/analyze.py`, `src/seasonal_analysis.py`) : produit des hotspots d'incidents déclarés, une rosace mensuelle des activités et un test de sensibilité aux dates du 1er janvier. Le V de Cramer décrit l'association entre mois et activité, sans mesurer la dangerosité biologique.
- **Enrichissement environnemental facultatif** (`src/enrich/`, `src/analysis/environment.py`) : `python -m src.pipeline --enrich` réutilise le géocodage local, interroge NOAA OISST v2.1 et Open-Meteo Archive (ERA5), construit dix jours témoins par incident et enregistre cache, exclusions, statuts et hypothèses. Les appels API ne sont pas exécutés par défaut.
- **Graphiques environnementaux** (`src/viz/environment_charts.py`) : distribue les comparaisons H1–H5, affiche `n` et les sources, et distingue les hypothèses des faits observés.
- **Comparaison écologique** (`src/compare_ecology.py`) : mesure des proximités géographiques entre incidents géocodés et occurrences GBIF disponibles localement. Elle conserve les limites temporelles, spatiales et d'identification des espèces.
- **Synthèse PDF** (`scripts/build_synthesis.py`) : assemble hors ligne les rapports et graphiques locaux; les API ne sont pas appelées pendant la génération.
- **Application** : visualisation des attaques par année (`src/visualize.py`) et rapport d'exécution (`reports/interpretation/run_report.json`). Les sorties sont classées dans `reports/images/`, `reports/data/` et `reports/interpretation/`. Les observations OCEARCH, GBIF et SST sont conservées séparément dans `data/reference/` avant toute jointure documentée.

Le pipeline est batch et rejouable à l'identique (idempotence assurée par le remplacement complet des fichiers curated/rejected à chaque run). Les snapshots raw, caches environnementaux et sorties enrichies sont ignorés par Git; aucun appel réseau n'est effectué dans les tests automatisés.
