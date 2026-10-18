# Zone raw

`global_shark_attacks_raw.csv` est le fichier source réel local par défaut. Il
est lu sans transformation et copié dans un fichier `source_<horodatage>.csv`
distinct à chaque exécution. S'il manque, le pipeline se replie sur
`data/samples/sample_source.csv`, jeu synthétique d'au moins 100 lignes. Si un
autre CSV autorisé est fourni en argument, le collecteur copie celui-ci sans
modifier le fichier fourni.

Les fichiers source bruts peuvent contenir des noms de victimes. Ils sont
donc exclus de Git et doivent rester locaux, sauf autorisation explicite de
redistribution. Un nouveau clone doit recevoir un export CSV obtenu dans le
respect des conditions de la source. Les snapshots conservent les champs
d'origine, mais le champ `name` n'est jamais publie dans `data/curated/` ni
dans les visualisations. Le rapport conserve le hash SHA-256, la taille et le
nom du snapshot traité.