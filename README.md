# Shark Attacks Collector

Pipeline batch qui transforme un extrait du Global Shark Attack File en un dataset propre, validé et documenté, pour répondre à trois besoins métier : suivre le risque dans le temps et l'espace, identifier les profils exposés et qualifier la gravité des incidents par pays.

## Objectif

Une ligne du dataset curated représente un incident d'attaque de requin, avec sa date, sa localisation, l'activité pratiquée et le profil de la victime. Détail complet dans `config/data_contract.yaml`.

## Source et conditions

- **Source** : Global Shark Attack File, extrait via Kaggle — [gauravkumar2525/shark-attacks](https://www.kaggle.com/datasets/gauravkumar2525/shark-attacks)
- **Licence** : usage pédagogique, conditions Kaggle
- **Date d'accès** : 2026-09-22
- Détail de l'évaluation des sources candidates : `docs/source_assessment.md`

## Prérequis

- Python 3.11 ou plus récent

## Installation

```bash
python -m venv .venv
source .venv/bin/activate   # sous Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Exécution

```bash
python -m src.pipeline
```

Le pipeline :
1. copie le CSV source vers `data/raw/` avec un nom horodaté (jamais modifié ensuite) ;
2. applique 5 règles de qualité et sépare les lignes acceptées des lignes rejetées ;
3. transforme les lignes acceptées en dataset curated propre et typé ;
4. génère une première visualisation (attaques par année) ;
5. génère un dashboard `dashboard_incidents.png` avec évolution annuelle, saisonnalité, pays et localités ;
6. génère les rapports `hotspots_incidents_declares.csv` et `saisonnalite_incidents_declares.csv` ;
7. écrit un rapport d'exécution.

Pour utiliser un autre fichier source :

```bash
python -m src.pipeline chemin/vers/un_autre_export.csv
```

Le pipeline est **idempotent** : les fichiers `data/curated/global_shark_attacks-selected-columns.csv` et `data/rejected/rejected_rows.csv` sont entièrement remplacés à chaque exécution, donc le relancer plusieurs fois sur la même source ne crée pas de doublons dans les sorties. Seule la zone `data/raw/` accumule une nouvelle preuve de collecte horodatée à chaque run — c'est voulu, c'est l'historique des collectes.

## Arborescence

```
shark-attacks-collector/
  README.md
  requirements.txt
  .gitignore
  config/
    data_contract.yaml       # contrat de données v1
  data/
    source/                  # fichier source original, jamais modifié
    raw/                     # copies horodatées (preuve de collecte)
    curated/                 # global_shark_attacks-selected-columns.csv — données validées et propres
    rejected/                # rejected_rows.csv — lignes écartées + raison
  docs/
    architecture.md
    source_assessment.md
  reports/
    images/                  # graphiques et cartes PNG
    data/                    # sorties CSV d'analyse
    interpretation/          # rapports Markdown et JSON
  data/reference/
    README.md                # contrat pour OCEARCH, GBIF et SST
    shark_species_profiles.csv # habitats et reproduction documentés
  src/
    collect.py                # étape 1 : collecte
    validate.py                # étape 2 : 5 règles de qualité
    transform.py                # étape 3 : dataset curated
    visualize.py                 # étape 4 : visualisation simple
    pipeline.py                  # orchestrateur
  tests/
    test_quality.py
```

## Règles de qualité

Définies et documentées dans `config/data_contract.yaml`, implémentées dans `src/validate.py` :

| Règle | Dimension | Action si échec |
|---|---|---|
| `completude_pays` | Complétude | Rejeter |
| `validite_annee` | Validité | Rejeter |
| `coherence_type` | Cohérence | Rejeter |
| `domaine_age` | Domaine | Corriger (mis à `NULL`), pas de rejet |
| `unicite` | Unicité | Dédupliquer, garder la première occurrence |

## Tests

```bash
pytest tests/
```

## Limites connues

- Le champ `name` (nom de la victime) n'est présent qu'en zone raw, jamais dans le dataset curated ni dans les visualisations.
- Le dataset ne couvre que les incidents effectivement recensés par le GSAF : les zones sous-déclarantes seront sous-représentées.
- Pas de clé d'identifiant naturelle dans la source : la déduplication se fait sur l'ensemble des champs, ce qui peut laisser passer deux incidents distincts aux caractéristiques identiques par coïncidence.
- Les hotspots représentent des **incidents déclarés**, pas la dangerosité intrinsèque d'un lieu : ils dépendent aussi de la fréquentation humaine, du signalement et de la couverture géographique.
- Le dataset actuel ne contient ni espèce de requin, ni coordonnées, ni température de surface, ni courants : il ne permet pas encore de conclure sur les migrations, les zones de reproduction ou une agressivité liée à la reproduction.

## Axes écologiques

Les futures observations doivent rester séparées du dataset d'incidents :

- **OCEARCH** : trajectoires de requins marqués, utiles pour étudier des déplacements individuels. Son endpoint non officiel n'est pas appelé automatiquement ; un export brut doit être conservé avec sa date et son URL.
- **GBIF** : occurrences géolocalisées et espèces observées. Elles documentent une présence, pas une abondance ni une migration complète.
- **NOAA/Copernicus** : température de surface, anomalies thermiques et courants pour contextualiser les dates et positions.

Pour répondre à la question « pourquoi deviennent-ils agressifs ? », il faudra croiser les incidents avec l'espèce, la saison, la température, l'activité humaine et l'effort d'observation. Une corrélation simple ne suffit pas à démontrer un effet de la reproduction.

## Améliorations prévues

- Passage de `data/curated/global_shark_attacks-selected-columns.csv` vers une base SQLite en étoile (schéma déjà défini, voir échanges précédents).
- Visualisations complémentaires : top pays, répartition par activité et tranche d'âge.
- Rapport de profilage automatique (`df.describe()`, taux de valeurs manquantes) avant validation.
- Import contrôlé d'exports OCEARCH et d'occurrences GBIF, avec distance spatiale, écart temporel et provenance conservés pour chaque jointure.

### Importer des observations officielles GBIF

GBIF est une API officielle adaptée aux occurrences géolocalisées et à la taxonomie :

```bash
python -m src.gbif "Carcharodon carcharias" --limit 100
```

La commande écrit un export brut JSON et un CSV dans `data/reference/`. Les observations avec `lifeStage=JUVENILE` peuvent aider à repérer des zones candidates de nurserie. GBIF ne fournit toutefois pas à lui seul une carte certaine des lieux de reproduction ni une mesure de l'agressivité.

### Visualiser les espèces

Après avoir téléchargé les occurrences GBIF :

```bash
python -m src.species_visualize
```

Le graphique [species_occurrences.png](reports/images/species_occurrences.png) compare les positions géographiques et la répartition latitudinale des espèces observées. Il représente une présence documentée, pas une abondance.

### Ajouter des coordonnées aux attaques

Les lieux du dataset sont géocodés avec Nominatim/OpenStreetMap, en commençant par les plus fréquents :

```bash
python -m src.geocode --limit 25
```

Le résultat est écrit dans `reports/data/attacks_with_coordinates.csv`. Les coordonnées correspondent au lieu ou au centre de la ville lorsque l'incident n'est pas plus précis ; elles ne remplacent donc pas une position GPS exacte. Le cache est conservé dans `data/reference/nominatim_cache.json` et le délai entre les requêtes respecte l'usage public du service.

Pour visualiser les attaques sur la carte mondiale :

```bash
python -m src.attacks_visualize
```

Le graphique [attack_locations.png](reports/images/attack_locations.png) utilise uniquement les lignes qui ont obtenu des coordonnées.

### Comparer les attaques et les espèces

Pour comparer les lieux d'attaques aux occurrences GBIF déjà téléchargées :

```bash
python -m src.compare_ecology
```

Cette commande produit [attack_species_comparison.png](reports/images/attack_species_comparison.png), un tableau détaillé des distances dans [attack_species_proximity.csv](reports/data/attack_species_proximity.csv), une synthèse par espèce et le rapport [ecological_hypotheses.md](reports/interpretation/ecological_hypotheses.md).

Une espèce est seulement considérée comme **candidate géographique** lorsqu'une occurrence GBIF est située à moins de 25 km ou 100 km du lieu d'attaque géocodé. Le calcul ne prouve pas que cette espèce a attaqué : le dataset GSAF ne contient pas l'identification du requin.

Une visualisation basée uniquement sur les deux CSV de comparaison est disponible avec :

```bash
python -m src.csv_comparison_visualize
```

Elle combine les volumes à moins de 25 km et 100 km, les observations juvéniles proches et la distribution des distances par espèce.

Pour générer un camembert simple et le tableau associé :

```bash
python -m src.csv_comparison_visualize
```

Le camembert classe les **espèces candidates géographiques** selon les proximités à moins de 100 km. Il ne permet pas d'affirmer quelle espèce a réellement attaqué, car cette information n'est pas présente dans le dataset source. L'interprétation détaillée est dans `reports/interpretation/csv_species_interpretation.md`.
