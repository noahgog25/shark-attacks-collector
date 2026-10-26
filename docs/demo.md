9. Présenter l'audit RGPD [rgpd_audit.md](rgpd_audit.md) : données nécessaires, finalités, conservation, droits, risques et décision AIPD.


# Démonstration finale

## Préparer

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Déroulé en 3 à 5 minutes

1. Montrer la question centrale, l'utilisateur, les trois cas d'usage et les KPI dans [project_brief.md](project_brief.md).
2. Montrer la source retenue, ses conditions et la zone raw dans [source_assessment.md](source_assessment.md) et [../data/raw/README.md](../data/raw/README.md).
3. Lancer le pipeline :

   ```bash
   python -m src.pipeline
   ```

4. Ouvrir le curated, les rejets et le rapport [run_report.json](../reports/interpretation/run_report.json).
5. Montrer le profil source [source_profile.json](../reports/interpretation/source_profile.json), les compteurs des cinq règles et le hash SHA-256.
6. Montrer le dashboard [dashboard_incidents.png](../reports/images/dashboard_incidents.png) et les hotspots dans [hotspots_incidents_declares.csv](../reports/data/hotspots_incidents_declares.csv).
7. Relancer le pipeline et vérifier que le curated et les rejets conservent leurs volumes; un nouveau snapshot raw horodaté est créé et son hash apparaît dans le rapport.
8. Présenter une limite : les hotspots sont des incidents déclarés, pas un taux de dangerosité, et l'espèce responsable n'est pas connue.
9. Lancer `python -m src.compare_ecology` puis `python -m src.seasonal_analysis`; comparer la rosace et les rapports Markdown/CSV/JSON.
10. Si un géocodage local existe, lancer `python -m src.pipeline --enrich` pour calculer les hypothèses environnementales, les contrôles et les cinq graphiques; l'option peut afficher `WARN` si des données ou API manquent.
11. Lancer `python -m scripts.build_synthesis` et présenter le PDF final de six pages.

Les appels d'enrichissement ne sont jamais exécutés par la suite pytest : les
clients sont testés avec des réponses et erreurs simulées. Les réponses déjà
en cache permettent un rejeu hors ligne. Une hypothèse soutenue n'est pas une
preuve de causalité.

## Commandes d'enrichissement optionnelles

```bash
python -m src.gbif "Carcharodon carcharias" --limit 100
python -m src.geocode --limit 100
python -m src.compare_ecology
python -m src.csv_comparison_visualize
```