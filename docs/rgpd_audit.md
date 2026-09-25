# Audit RGPD minimal

Ce document applique le cours RGPD au projet **Shark Attacks Collector**.
Il s'agit d'un audit pedagogique et non d'un avis juridique. La base legale
definitive et les conditions de reutilisation de la source doivent etre
confirmees avec l'enseignant ou le responsable du traitement.

## Finalite

Analyser des incidents de requins recenses afin de decrire leur repartition
dans le temps et l'espace, puis orienter une recherche ecologique. Les donnees
ne doivent pas servir a identifier, contacter, noter ou surveiller les
victimes.

## Donnees et minimisation

| Donnee | Personnelle ? | Necessaire ? | Decision |
|---|---|---:|---|
| `name` | Oui, identifiante directe | Non | Raw local uniquement; jamais curated ou publie |
| `age` | Oui par recoupement possible | Partiellement | Age nettoye et tranche, sans nom |
| `sex` | Peut etre personnelle | Partiellement | `M`/`F` uniquement, sans identifiant |
| pays/zone/localite | Peut devenir personnelle par recoupement | Oui pour l'etude spatiale | Agrégations et coordonnees approximatives |
| activite | Peut reveler une situation individuelle | Oui pour la saisonnalite | Analyse agregée, pas de profilage |

Aucune donnee de sante, biométrique, génétique, politique, religieuse ou de
vie sexuelle n'est necessaire. Par defaut, aucune nouvelle donnee personnelle
ne doit etre ajoutee.

## Registre du traitement

- Responsable pedagogique : etudiant, sous validation de l'enseignant.
- Personnes concernees : personnes decrites dans le fichier source, sans
  contact avec elles.
- Sources : extrait GSAF via Kaggle, GBIF, Nominatim/OpenStreetMap.
- Base legale a documenter : projet pedagogique et interet legitime de
  recherche descriptive, sous reserve de validation.
- Destinataires : etudiant et enseignant; aucune publication nominative.
- Hebergement : poste local et depot Git controle.
- Les appels GBIF/Nominatim n'envoient pas le fichier complet ni les noms.

## Conservation et securite

- Raw : duree du TP et de la verification, puis suppression ou anonymisation
  si les conditions de source le permettent.
- Curated et rejets : duree du projet pedagogique; aucune colonne `name` dans
  le curated.
- Rapports : agregats et interpretations pendant le projet.
- Le raw est ignore par Git; verifier `git status` avant chaque push.
- Acces local limite a l'etudiant et a l'enseignant; aucun secret dans le
  depot.

## Droits

Si une personne est identifiable, le responsable doit pouvoir rechercher,
rectifier, exporter ou supprimer la donnee, sous reserve des obligations de
conservation et des conditions de la source. Le projet ne collecte pas
directement de formulaire et ne contacte pas les personnes concernees.

## Risques et AIPD/PIA

Les risques principaux sont la fuite de `name`, la re-identification par
age+lieu+date, l'acces non autorise et le profilage abusif des lieux. Les
mesures sont la liste blanche curated, l'ignorance Git du raw, les agregations,
les coordonnees approximatives et la limitation des finalites.

Une AIPD complete ne parait pas necessaire pour le perimetre pedagogique
actuel : pas de surveillance systematique, pas de decision automatisee, pas
de traitement sensible intentionnel. Reevaluation obligatoire si une base
nominative, une surveillance, un profilage ou une publication de lieux precis
est ajoute.

## Decision RGPD

Le projet est acceptable pour le TP sous quatre conditions : ne pas publier ni
committer le raw contenant `name`; conserver seulement les colonnes necessaires
dans le curated; supprimer ou anonymiser le raw en fin de projet; ne pas
presenter les resultats comme un scoring des victimes.