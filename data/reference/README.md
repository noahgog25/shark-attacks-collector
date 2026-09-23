# Donnees ecologiques externes

Cette zone accueillera des observations externes sans les melanger au dataset
des incidents declares.

Chaque observation doit conserver au minimum :

- `source` : `ocearch`, `gbif` ou `sst` ;
- `source_record_id` ;
- `observed_at` ;
- `latitude`, `longitude` ;
- `species` si disponible ;
- `retrieved_at` ;
- `source_url` ;
- `spatial_uncertainty_km` si disponible.

## Sources prevues

- **OCEARCH** : trajectoires de requins marques. L'endpoint public non
  documente ne doit pas etre appele par defaut ; conserver un export brut et
  sa date de recuperation.
- **GBIF** : occurrences geolocalisees et taxonomie via son API officielle.
  Une occurrence ne represente ni l'abondance ni une route migratoire.
- **NOAA/Copernicus** : temperature de surface, anomalies et courants pour
  contextualiser les observations dans le temps et l'espace.
- **Nominatim/OpenStreetMap** : geocodage des villes et lieux textuels des
  attaques. Les coordonnees sont des approximations de lieu, pas des points
  GPS exacts de l'incident.

Les jointures futures devront conserver la distance et l'ecart temporel de
la correspondance. Une absence de correspondance est une information, pas un
motif de rejet d'un incident.

## Coordonnees des attaques

```bash
python -m src.geocode --limit 25
```

La commande geocode uniquement les lieux les plus frequents, conserve les
reponses dans `nominatim_cache.json`, et laisse les lieux non demandes ou non
trouves avec un statut explicite. Ne pas lancer une requete par ligne : les
services publics imposent des limites d'usage.

## Import GBIF

Depuis la racine du projet :

```bash
python -m src.gbif "Carcharodon carcharias" --limit 100
```

La commande appelle le service de correspondance taxonomique GBIF puis
`/occurrence/search?taxonKey=...&hasCoordinate=true`. Elle sauvegarde le JSON
brut et un CSV avec les coordonnees, la date, le stade de vie, la licence et
l'URL de chaque occurrence. Les lignes `JUVENILE` sont des indices possibles
de zone de nurserie, pas une preuve de lieu de reproduction.