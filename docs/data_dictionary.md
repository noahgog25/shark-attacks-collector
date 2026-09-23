# Dictionnaire de données

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