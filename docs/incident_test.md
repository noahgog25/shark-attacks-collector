# Test d'incident et reprise

## Incident reproduit

Le test `test_pipeline_documente_incident_source_absente_et_reprend` simule
une source indisponible. Le collecteur lève `FileNotFoundError`; le pipeline
écrit un rapport `FAIL` avec `run_id`, type et message d'erreur, puis relance
l'exception afin que le processus CLI ait un code de sortie non nul.

## Reprise vérifiée

Le même test fournit ensuite un CSV valide. Une nouvelle exécution obtient un
nouveau `run_id`, termine en `PASS`, produit les compteurs et les métriques de
fraîcheur. Les sorties curated et rejected sont remplacées, pas ajoutées.

Commande de reproduction manuelle depuis la racine :

```bash
python -m src.pipeline data/samples/fichier_absent.csv
python -m src.pipeline data/samples/sample_source.csv
```

La première commande doit échouer et écrire un rapport `FAIL`; la seconde doit
réussir. La preuve automatisée sans altérer les sorties locales réelles est :

```bash
python -m pytest tests/test_collect.py -q
```

Un CSV vide ou dont les colonnes requises (`country`, `year`, `type`, `age`)
ont disparu est refusé avant publication. Le snapshot brut déjà collecté reste
disponible pour diagnostiquer le problème. Après correction, le pipeline peut
être relancé; le rapport et les journaux identifient séparément chaque run.