# Comparaison attaques et presence des especes

Cette analyse compare 1011 attaques geocodees aux occurrences GBIF disponibles dans `data/reference/`.
Elle produit des hypotheses de proximite, pas une identification de l'espece responsable.

## Ce que les donnees montrent

- Une attaque est consideree proche d'une espece si une occurrence GBIF se trouve a moins de 25 km (proximite forte) ou 100 km (proximite regionale).
- Les coordonnees des attaques sont des coordonnees de villes ou de lieux textuels, et les occurrences GBIF sont soumises a un biais d'observation.
- Parmi les attaques avec une presence d'espece a moins de 100 km, les activites les plus frequentes sont : Surfing (502), Swimming (161), Inconnue (110), Wading (85), Standing (53).

## Hypotheses prudentes

1. **Chevauchement geographique** : une espece est candidate uniquement lorsqu'une occurrence GBIF est proche. Cela indique une presence documentee dans la region, pas la presence de l'animal au moment de l'attaque.
2. **Nurserie possible** : des occurrences GBIF marquees `JUVENILE` proches d'une zone peuvent signaler un habitat de juveniles. Elles ne prouvent pas un lieu de reproduction et ne disent rien sur l'agressivite.
3. **Activite humaine** : la frequence des activites comme la baignade, le surf ou la peche est un proxy de chevauchement humain. Sans nombre de personnes exposees ni temps passe dans l'eau, on ne peut pas calculer un risque.
4. **Courants chauds** : cette hypothese n'est pas testee ici. Le projet ne contient pas encore de temperature de surface, d'anomalie thermique ni de vecteur de courant. Il faut joindre une serie NOAA ou Copernicus par date et position.
5. **Reproduction et agressivite** : aucune donnee actuelle ne permet de conclure que la reproduction rend les requins plus agressifs. Il faudrait l'espece, le sexe, le stade de vie, la saison de reproduction et une mesure de l'exposition humaine.

## Conclusion

Les seules conclusions solides sont des proximités entre des lieux d'attaques approximatifs et des observations GBIF. Les noms d'especes produits sont des candidates geographiques et doivent etre confirmes par des donnees d'identification de l'animal, comme un rapport de terrain ou une trajectoire OCEARCH.
