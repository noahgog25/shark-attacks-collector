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
7. Relancer le pipeline et vérifier que le curated et les rejets conservent leurs volumes; le fichier raw canonique est remplacé sans créer de nouveau snapshot.
8. Présenter une limite : les hotspots sont des incidents déclarés, pas un taux de dangerosité, et l'espèce responsable n'est pas connue.

## Commandes d'enrichissement optionnelles

```bash
python -m src.gbif "Carcharodon carcharias" --limit 100
python -m src.geocode --limit 100
python -m src.compare_ecology
python -m src.csv_comparison_visualize
```