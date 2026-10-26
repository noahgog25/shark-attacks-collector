# Shark Attacks Collector

Pipeline batch qui transforme un extrait du Global Shark Attack File en un dataset propre, validé et documenté, pour décrire les incidents recensés dans le temps et l'espace et tester des hypothèses environnementales sans les présenter comme des causes.

## Objectif

Une ligne du dataset curated représente un incident d'attaque de requin, avec sa date, sa localisation, l'activité pratiquée et le profil de la victime. Détail complet dans `config/data_contract.yaml`.

## Question, utilisateur et décision

Le projet est cadré dans [docs/project_brief.md](docs/project_brief.md).

- **Question centrale :** où et quand les incidents de requins sont-ils recensés, et quelles espèces sont candidates dans les régions où une présence GBIF est documentée ?
- **Utilisateur :** étudiant, enseignant ou analyste qui veut explorer les incidents sans confondre signalement et dangerosité.
- **Décision :** prioriser des zones ou périodes à examiner et choisir les données écologiques complémentaires à collecter.
- **KPI :** incidents déclarés par lieu/pays/année, incidents par mois, rapprochements attaque-espèce à moins de 25 km et 100 km.

## Source et conditions

- **Source initiale** : Global Shark Attack File, extrait via Kaggle — [gauravkumar2525/shark-attacks](https://www.kaggle.com/datasets/gauravkumar2525/shark-attacks)
- **Licence** : usage pédagogique, conditions Kaggle
- **Date d'accès** : 2026-09-22
- Détail de l'évaluation des sources candidates : `docs/source_assessment.md`

## Prérequis

- Python 3.11 ou plus récent

## Installation

Depuis la racine du projet, sur macOS ou Linux :

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Sous Windows, dans PowerShell :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Dans l'invite de commandes Windows (`cmd`) :

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

Si PowerShell bloque l'activation du script, utilise directement
`.venv\Scripts\python.exe -m pip install -r requirements.txt`, puis remplace
`python` par `.venv\Scripts\python.exe` dans les commandes suivantes.
Python 3.11 ou plus récent est requis; les dépendances sont dans
`requirements.txt`.

## Exécution

```bash
python -m src.pipeline
```

Le fichier réel `data/raw/global_shark_attacks_raw.csv` est local et exclu de Git, car il contient des noms. S'il est absent, le pipeline utilise automatiquement [l'échantillon synthétique](data/samples/sample_source.csv), qui contient plus de 100 observations et aucun sujet réel. Pour une autre source autorisée, passe son chemin en argument. Dans tous les cas, le collecteur conserve une copie brute horodatée et ne modifie pas le fichier fourni. Détails : [guide de la zone raw](data/raw/README.md).

Le pipeline :
1. lit le CSV réel local, l'échantillon synthétique de secours, ou le CSV fourni en argument ;
2. applique 5 règles de qualité et sépare les lignes acceptées des lignes rejetées ;
3. transforme les lignes acceptées en dataset curated propre et typé ;
4. génère une première visualisation (attaques par année) ;
5. génère un dashboard `dashboard_incidents.png` avec évolution annuelle, saisonnalité, pays et localités ;
6. génère les rapports `hotspots_incidents_declares.csv` et `saisonnalite_incidents_declares.csv` ;
7. écrit un rapport d'exécution avec `run_id`, statut d'exécution, statut qualité, hash, compteurs, durée, date de l'incident le plus récent et âge de cette donnée.

L'étape environnementale est optionnelle et ne fait aucun appel réseau par
défaut. Après un export de coordonnées produit avec `python -m src.geocode`,
active-la avec :

```bash
python -m src.pipeline --enrich
```

Cette étape écrit `data/curated/attacks_enriched.csv`, les tests d'hypothèse
dans `reports/data/environment_hypotheses.csv`, les sensibilités et cinq
graphiques. Elle interroge NOAA OISST v2.1 et Open-Meteo Archive (ERA5), en
cache les réponses sous `data/raw/external/` par hash de requête et les
réutilise lors des relances. Un cache absent ou une API indisponible donne
`API_FAIL` et `enrichment.status = WARN` dans le rapport de run, sans arrêter
le pipeline de validation. Sur l'échantillon synthétique sans coordonnées,
les données environnementales restent insuffisantes (`WARN`, n=0), sans appel
réseau.

H1 à H5 sont des hypothèses et non des causes établies. H3 utilise les mois
alignés par hémisphère. Le rapport compte la part exclue à chaque filtre;
les dates du 1er janvier sont exclues des tests et apparaissent en sensibilité
dans le dashboard mensuel, avec et sans ces dates. Les coordonnées de localité
restent approximatives et les sources météo ne mesurent pas l'exposition
humaine. Voir [ADR 002](docs/ADR_002.md) et [l'évaluation des sources](docs/source_assessment.md).

Les logs d'étapes et les erreurs sont écrits dans le terminal. Une erreur écrit
un rapport `FAIL` avec son type et son message, conserve le snapshot déjà créé,
puis retourne un code d'échec. Un traitement achevé est `PASS`; les rejets et
doublons restent signalés dans `quality_status` et `warnings`. Corrige la source et relance la même commande;
les sorties curated/rejected sont remplacées. Le scénario est détaillé dans
[docs/incident_test.md](docs/incident_test.md).

Pour utiliser un autre fichier source :

```bash
python -m src.pipeline chemin/vers/un_autre_export.csv
python -m src.pipeline chemin/vers/un_autre_export.csv --enrich
```

Le pipeline est **idempotent** : les fichiers `data/curated/shark_attacks_curated.csv` et `data/rejected/rejected_rows.csv` sont entièrement remplacés à chaque exécution. Chaque exécution ajoute une copie source horodatée en zone raw; ces copies ne sont pas suivies par Git.

Le rapport d'exécution se trouve dans `reports/interpretation/run_report.json`;
le profil initial est dans `source_profile.json`. Les compteurs de validation
et le hash assurent la traçabilité de la source traitée.

## Reproduire depuis un clone propre

Après installation, `python -m src.pipeline` fonctionne sans téléchargement
externe grâce à l'échantillon synthétique versionné. Pour produire de nouveau
les échantillons raw, curated et rejected :

```bash
python scripts/build_demo_data.py
python -m src.pipeline
python -m pytest tests/
```

Les commandes équivalentes Windows sont les mêmes dans un environnement
virtuel activé; sans activation, remplace `python` par
`.venv\Scripts\python.exe`. L'extrait GSAF réel doit être obtenu séparément
dans le respect de ses conditions d'utilisation.

## Architecture et décisions

- [Architecture V1 (SVG)](docs/architecture_v1.svg) : chaîne initiale raw, qualité et curated.
- [Architecture V2 (SVG)](docs/architecture_v2.svg) : observabilité, reprise et produit métier.
- [ADR 001](docs/ADR_001.md) : comparaison CSV batch, SQLite et options distribuées.
- [ADR 002](docs/ADR_002.md) : NOAA OISST, ERA5 et méthode de test environnemental.
- [Dictionnaire de données](docs/data_dictionary.md) et [contrat versionné](config/data_contract.yaml).
- [Synthèse finale PDF](docs/Synthese_Sharks_Collector.pdf), format de 4 à 6 pages.

## Arborescence

```
shark-attacks-collector/
  README.md
  requirements.txt
  .gitignore
  config/
    data_contract.yaml       # contrat de données v1
    processing_register.yaml # registre de traitement RGPD minimal
  data/
    raw/                     # snapshots locaux, exclus de Git
    samples/                 # source synthétique + exemples curated/rejected
    curated/                 # shark_attacks_curated.csv — données validées et propres
    rejected/                # rejected_rows.csv — lignes écartées + raison
  docs/
    architecture.md
    architecture_v1.svg
    architecture_v2.svg
    ADR_001.md
    incident_test.md
    Synthese_Sharks_Collector.pdf       # synthèse initiale + suite de « Ce que montrent les données »
    Synthese_Sharks_Collector_base.pdf  # version initiale conservée pour reconstruire le PDF
    data_dictionary.md
    demo.md
    project_brief.md
    rgpd_audit.md
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
    profile.py                # profilage avant validation
    validate.py                # étape 2 : 5 règles de qualité
    transform.py                # étape 3 : dataset curated
    visualize.py                 # étape 4 : visualisation simple
    pipeline.py                  # orchestrateur
  scripts/
    build_demo_data.py            # régénère l'échantillon synthétique
    build_synthesis.py            # reconstruit la synthèse finale à partir des rapports locaux
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

Après activation de l'environnement virtuel :

```bash
python -m pytest tests/
```

Sous Windows sans activation, lance `.venv\Scripts\python.exe -m pytest tests/`.

La suite vérifie les règles de qualité, les rejets, le profilage, le collecteur,
le test d'incident et de reprise, les sorties de visualisation, le géocodage et
les comparaisons écologiques.

## Usage d'outils d'IA

- Outil utilise : GitHub Copilot.
- Taches assistees : amélioration du collecteur et de l’orchestrateur, génération de données de démonstration, rédaction de documentation (ADR, architecture), ajout de tests.
- Vérifications realisees : exécution du pipeline (sources réelle et synthétique), installation des dépendances dans un environnement Python 3.11 neuf, exécution des tests.
- Parties retravaillees personnellement :
--> Choix du dataset.
--> Choix de l’API.
--> Mise en relation du dataset et de l’API.
--> Définition des règles de validation des données.
--> Conception de l’architecture du projet.
--> Élaboration du document PDF de synthèse du projet.
--> Relecture et validation de chaque modification assistée avant remise.
--> ...

## Limites connues

- Le champ `name` (nom de la victime) n'est présent qu'en zone raw, jamais dans le dataset curated ni dans les visualisations.
- Le dataset ne couvre que les incidents effectivement recensés par le GSAF : les zones sous-déclarantes seront sous-représentées.
- Pas de clé d'identifiant naturelle dans la source : la déduplication se fait sur l'ensemble des champs, ce qui peut laisser passer deux incidents distincts aux caractéristiques identiques par coïncidence.
- Les hotspots représentent des **incidents déclarés**, pas la dangerosité intrinsèque d'un lieu : ils dépendent aussi de la fréquentation humaine, du signalement et de la couverture géographique.
- Le dataset curated principal ne contient ni espèce de requin, ni coordonnées, ni météo; ces enrichissements restent séparés et facultatifs. Ils ne permettent pas de conclure sur les migrations, les zones de reproduction ou une agressivité liée à la reproduction.

## Axes écologiques

Les futures observations doivent rester séparées du dataset d'incidents :

- **OCEARCH** : trajectoires de requins marqués, utiles pour étudier des déplacements individuels. Son endpoint non officiel n'est pas appelé automatiquement ; un export brut doit être conservé avec sa date et son URL.
- **GBIF** : occurrences géolocalisées et espèces observées. Elles documentent une présence, pas une abondance ni une migration complète.
- **NOAA OISST v2.1 / Open-Meteo Archive (ERA5)** : SST, anomalies, température de l'air, pluie et vent pour tester des hypothèses avec des témoins, sans inférer de causalité.

Pour répondre à la question « pourquoi deviennent-ils agressifs ? », il faudra croiser les incidents avec l'espèce, la saison, la température, l'activité humaine et l'effort d'observation. Une corrélation simple ne suffit pas à démontrer un effet de la reproduction.

## Améliorations prévues

- Passage de `data/curated/shark_attacks_curated.csv` vers une base SQLite en étoile (schéma déjà défini, voir échanges précédents).
- Visualisations complémentaires : top pays, répartition par activité et tranche d'âge.
- Import contrôlé d'exports OCEARCH et d'occurrences GBIF, avec distance spatiale, écart temporel et provenance conservés pour chaque jointure.

### Démonstration

Le déroulé reproductible et les commandes de soutenance sont dans [docs/demo.md](docs/demo.md).

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

### Approfondir les associations mensuelles et la synthèse

À partir du CSV curated, une analyse complémentaire produit une rosace circulaire des cinq activités les plus fréquentes (plus « Autres »), leur répartition mensuelle normalisée, un V de Cramer descriptif et un test de sensibilité aux dates du 1er janvier :

```bash
python -m src.seasonal_analysis
```

Les livrables sont [la rosace](reports/images/seasonal_activity_rose.png), [la matrice mensuelle](reports/data/activity_month_distribution.csv), [les résultats chiffrés](reports/data/seasonality_analysis.json) et [leur interprétation](reports/interpretation/seasonality_analysis.md). Le visuel met en avant la saisonnalité relative de chaque activité, pas le risque ni l'exposition humaine.

Pour mettre à jour le PDF après le pipeline et les analyses GBIF/saisonnières :

```bash
python -m src.compare_ecology
python -m src.seasonal_analysis
python -m scripts.build_synthesis
```

Le générateur fonctionne hors ligne et produit une synthèse de six pages. Les
résultats GBIF existants (642 des 1 011 incidents géocodés proches d'une
occurrence de requin-bouledogue à moins de 100 km; 526 pour le requin-tigre)
sont des proximités géographiques non exclusives, pas une corrélation
temporelle. L'association mois-activité regroupée est faible (V de Cramer
0,083). 347 dates sont au 1er janvier; le dashboard montre les comptes avec
et sans ces dates (janvier baisse lorsque les dates du 1er janvier sont
exclues). Les hypothèses environnementales H1–H5 sont ajoutées uniquement
après `python -m src.pipeline --enrich`; sans résultats locaux, la synthèse
les marque comme non concluantes plutôt que d'inventer une association.
