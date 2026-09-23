# Cadrage du projet

## Application

**Nom :** Shark Attacks Collector.

**Utilisateur cible :** un étudiant, un enseignant ou un analyste souhaitant
explorer les incidents de requins recensés sans confondre fréquence de
signalement et dangerosité biologique.

**Problème :** les données brutes mélangent des dates, lieux, catégories et
âges parfois incomplets ou incohérents, ce qui empêche une comparaison fiable.

**Décision rendue possible :** choisir les zones et périodes à examiner en
priorité, puis décider quelles données écologiques complémentaires collecter
pour tester une hypothèse sur les espèces, les migrations ou l'environnement.

**Question centrale :** où et quand les incidents de requins sont-ils
recensés, et quelles espèces sont candidates dans les régions où une présence
GBIF est documentée ?

**Périmètre inclus :** incidents GSAF, validation, transformation, rejets,
hotspots déclarés, saisonnalité, géocodage approximatif, occurrences GBIF et
comparaison spatiale exploratoire.

**Périmètre exclu :** taux de risque individuel, abondance des requins,
identification certaine de l'espèce responsable, preuve d'un lieu de
reproduction, causalité entre réchauffement et agressivité.

## Cas d'usage et KPI

| Cas d'usage | KPI | Données nécessaires | Fréquence |
|---|---|---|---|
| Repérer les lieux où les incidents sont le plus souvent recensés | Nombre d'incidents déclarés par localité, pays et année | GSAF curated | Ponctuelle / batch |
| Examiner la saisonnalité des incidents | Nombre d'incidents déclarés par mois | Date de l'incident | Ponctuelle / batch |
| Orienter une recherche écologique | Nombre d'attaques à moins de 25 km et 100 km d'une occurrence GBIF | Attaques géocodées + GBIF | À chaque nouvel export |

Les KPI sont des **comptes d'incidents ou de rapprochements**, jamais des taux
de dangerosité : aucun dénominateur d'exposition humaine n'est disponible.