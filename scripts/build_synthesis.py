"""Build the five-page final project synthesis PDF."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_demo_data import build_sample_data

REPORT_PATH = ROOT / "reports" / "interpretation" / "run_report.json"
OUTPUT_PATH = ROOT / "docs" / "synthesis.pdf"
INK = colors.HexColor("#18323f")
TEAL = colors.HexColor("#31708e")
PALE = colors.HexColor("#edf3f5")
MUTED = colors.HexColor("#52616b")


def make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CoverTitle", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=24, leading=29, textColor=INK, alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "SectionTitle", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=18, leading=22, textColor=INK, spaceAfter=9,
        ),
        "h2": ParagraphStyle(
            "SubTitle", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=11, leading=14, textColor=TEAL, spaceBefore=7, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9.4, leading=13.2, textColor=INK, spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["BodyText"], fontName="Helvetica",
            fontSize=8, leading=10.5, textColor=MUTED, spaceAfter=4,
        ),
        "table": ParagraphStyle(
            "Table", parent=base["BodyText"], fontName="Helvetica",
            fontSize=8, leading=10, textColor=INK,
        ),
        "table_head": ParagraphStyle(
            "TableHead", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=8, leading=10, textColor=colors.white,
        ),
        "cover_sub": ParagraphStyle(
            "CoverSub", parent=base["BodyText"], fontName="Helvetica",
            fontSize=12, leading=17, textColor=MUTED, spaceAfter=14,
        ),
    }


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def table(rows, widths, styles, header=True):
    converted = []
    for row_index, row in enumerate(rows):
        selected = styles["table_head"] if header and row_index == 0 else styles["table"]
        converted.append([para(str(value), selected) for value in row])
    result = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#c9d4d9")),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ])
    result.setStyle(TableStyle(commands))
    return result


def on_page(canvas, doc):
    canvas.saveState()
    page_width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#d4dee2"))
    canvas.line(18 * mm, 15 * mm, page_width - 18 * mm, 15 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 10 * mm, "Shark Attacks Collector · Projet final ESEO")
    canvas.drawRightString(page_width - 18 * mm, 10 * mm, f"{doc.page} / 5")
    canvas.restoreState()


def build_pdf() -> Path:
    if not REPORT_PATH.exists():
        build_sample_data()
        from src.pipeline import run

        run()
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    styles = make_styles()
    story = []

    story.extend([
        Spacer(1, 14 * mm),
        para("Shark Attacks Collector", styles["title"]),
        para("Synthèse du projet final · Architecture BD et collecte de données", styles["cover_sub"]),
        para("1 · Problème, usage et sources", styles["h1"]),
        para(
            "Le projet transforme des incidents déclarés dans le Global Shark Attack File (GSAF) "
            "en données contrôlées et en indicateurs descriptifs. L'utilisateur cible est un étudiant, "
            "un enseignant ou un analyste qui veut repérer les lieux et périodes à examiner, sans "
            "confondre fréquence de signalement et dangerosité biologique.", styles["body"]
        ),
        para("Question centrale", styles["h2"]),
        para(
            "Où et quand les incidents de requins sont-ils recensés, et quelles espèces sont candidates "
            "dans les régions où une présence GBIF est documentée ?", styles["body"]
        ),
        table([
            ["Cas d'usage", "Indicateur"],
            ["Repérer les lieux les plus souvent déclarés", "Nombre d'incidents par localité, pays et année"],
            ["Examiner les variations saisonnières", "Nombre d'incidents par mois"],
            ["Orienter une recherche écologique", "Proximités attaque-occurrence à 25 km et 100 km"],
        ], [72 * mm, 94 * mm], styles),
        Spacer(1, 7),
        para("Source et conformité", styles["h2"]),
        para(
            "La source principale est un export CSV GSAF obtenu via Kaggle; sa mise à jour est ponctuelle "
            "et son accès peut demander une session. Le collecteur ne scrape pas le site et ne contourne "
            "pas l'authentification. Les conditions exactes de redistribution doivent être confirmées avant "
            "publication. Le CSV réel contenant des noms reste local et ignoré par Git. Un échantillon "
            "synthétique de 121 lignes permet la démonstration depuis un clone propre.", styles["body"]
        ),
        para(
            "Le grain est un incident déclaré. La source n'offre pas de clé naturelle; la déduplication "
            "stricte sur tous les champs est reproductible mais peut fusionner deux incidents identiques. "
            "La fréquence est batch et ponctuelle, car la source n'est pas un flux continu.", styles["small"]
        ),
        PageBreak(),
    ])

    story.extend([
        para("2 · Chaîne et architecture", styles["h1"]),
        para(
            "Le choix est une chaîne locale simple : le coût d'exploitation reste faible, chaque étape "
            "est inspectable et le volume du jeu (6 890 observations réelles dans le dernier run vérifié) "
            "ne justifie pas de plateforme distribuée.", styles["body"]
        ),
        table([
            ["Étape", "Entrée / action", "Sortie / preuve"],
            ["Collecte", "CSV local, chemin CLI ou échantillon", "Snapshot UTC non transformé, SHA-256"],
            ["Profil", "Snapshot brut", "Dimensions, types, manquants, doublons, modalités"],
            ["Qualité", "Schéma source", "Acceptés, rejetés, compteurs par règle"],
            ["Transformation", "Lignes acceptées", "CSV curated normalisé et typé"],
            ["Publication", "Curated", "Dashboard PNG, hotspots et saisonnalité CSV"],
            ["Observabilité", "Chaque run", "run_id, logs, rapport PASS/FAIL, durée, fraîcheur"],
        ], [34 * mm, 65 * mm, 67 * mm], styles),
        Spacer(1, 8),
        para("Architecture V1 et évolution V2", styles["h2"]),
        para(
            "La V1 représente le flux source → raw → validation → curated/rejected → restitution. La V2 "
            "ajoute l'entrée configurable, les contrôles de schéma, les logs et le rapport de run, ainsi "
            "que le chemin de reprise après incident. Les deux diagrammes SVG livrés dans docs/ sont "
            "les vues de référence.", styles["body"]
        ),
        para("Stockage et choix écartés", styles["h2"]),
        para(
            "Les fichiers CSV suffisent à un lot ponctuel et facilitent l'inspection. SQLite apporterait "
            "transactions, contraintes et requêtes SQL, mais demanderait migrations et maintenance sans "
            "bénéfice nécessaire à ce volume. Warehouse, Lake séparé et streaming sont écartés faute "
            "d'intégrations durables ou d'exigence de latence. L'ADR 001 détaille les compromis et les "
            "conditions de réexamen.", styles["body"]
        ),
        para(
            "Les snapshots raw permettent le rejeu; curated et rejected sont remplacés à chaque run. "
            "Les observations écologiques restent séparées et les distances sont interprétées comme "
            "candidatures géographiques, jamais comme identification de l'espèce responsable.", styles["small"]
        ),
        PageBreak(),
    ])

    story.extend([
        para("3 · Qualité, robustesse et observabilité", styles["h1"]),
        para("Le contrat versionné fixe le grain, le schéma et cinq règles automatisées :", styles["body"]),
        table([
            ["Règle", "Dimension / action"],
            ["completude_pays", "Complétude : rejeter pays absent"],
            ["validite_annee", "Validité : rejeter année hors plage"],
            ["coherence_type", "Cohérence : rejeter catégorie inconnue"],
            ["domaine_age", "Domaine : corriger l'âge suspect à NULL"],
            ["unicite", "Unicité : supprimer les doublons stricts et compter"],
        ], [50 * mm, 116 * mm], styles),
        Spacer(1, 8),
        para("Dernière exécution réelle vérifiée", styles["h2"]),
        table([
            ["Métrique", "Valeur"],
            ["État", str(report.get("status", report.get("quality_status", "inconnu")))],
            ["Entrées / acceptées / rejetées", f"{report.get('input_rows', 0)} / {report.get('accepted_rows', 0)} / {report.get('rejected_rows', 0)}"],
            ["Doublons retirés", str(report.get("duplicates_removed", 0))],
            ["Date source la plus récente", str(report.get("newest_record_date", "non calculée"))],
            ["Âge de cette observation (jours)", str(report.get("data_age_days", "non calculé"))],
            ["Durée", f"{report.get('duration_seconds', 'n/a')} s"],
            ["Run ID", str(report.get("run_id", "n/a"))],
        ], [63 * mm, 103 * mm], styles),
        Spacer(1, 7),
        para("Incident et reprise", styles["h2"]),
        para(
            "Un test simule une source absente : le processus échoue, conserve le rapport FAIL avec run_id, "
            "type et message, puis une source valide est fournie et une nouvelle exécution passe. Un CSV "
            "vide ou un schéma privé des champs requis est refusé avant publication. Le snapshot brut déjà "
            "créé est gardé pour diagnostic. Les logs décrivent début, collecte, qualité, fin ou exception.",
            styles["body"]
        ),
        para(
            "La métrique de fraîcheur est calculée à partir de la date d'incident maximale; elle ne mesure "
            "pas le délai de publication de Kaggle. L'export source est ponctuel et ne permet pas d'affirmer "
            "une fraîcheur de collecte amont.", styles["small"]
        ),
        PageBreak(),
    ])

    story.extend([
        para("4 · Produit de données et décision", styles["h1"]),
        para(
            "Le produit final sert à explorer les incidents déclarés par année, pays, localité et mois. "
            "Le dashboard présente la tendance temporelle, la saisonnalité et les principaux lieux; les "
            "CSV de hotspots et de saisonnalité permettent une réutilisation directe. Le curated expose "
            "des dates, lieux, activités, catégories, sexe et classes d'âge nettoyés.", styles["body"]
        ),
        table([
            ["Artefact", "Usage"],
            ["data/curated/shark_attacks_curated.csv", "Table analytique propre; sans nom de victime"],
            ["data/rejected/rejected_rows.csv", "Audit des lignes rejetées et raison"],
            ["reports/images/dashboard_incidents.png", "Restitution visuelle synthétique"],
            ["reports/data/hotspots_incidents_declares.csv", "Comptes par lieux déclarés"],
            ["reports/data/saisonnalite_incidents_declares.csv", "Comptes mensuels déclarés"],
            ["reports/interpretation/run_report.json", "Provenance, état, mesures et sorties du run"],
        ], [80 * mm, 86 * mm], styles),
        Spacer(1, 7),
        para("Décisions permises et limites d'interprétation", styles["h2"]),
        para(
            "Les tableaux aident à prioriser des zones/périodes pour une étude complémentaire. Ils ne "
            "mesurent pas un risque individuel ou une dangerosité intrinsèque : fréquentation humaine, "
            "couverture et sous-déclaration ne sont pas contrôlées. Les proximités GBIF ne prouvent ni "
            "l'espèce attaquante ni une causalité écologique.", styles["body"]
        ),
        para(
            "Les fichiers synthétiques livrés couvrent 121 lignes source, dont des cas invalides et un "
            "doublon; ils servent au test de bout en bout, pas à tirer des conclusions biologiques. "
            "L'export réel est conservé localement et son partage doit respecter licence et minimisation.",
            styles["body"]
        ),
        para("Résultat reproductible", styles["h2"]),
        para(
            "Un nouvel utilisateur crée un environnement Python 3.11+, installe requirements.txt puis lance "
            "python -m src.pipeline et python -m pytest tests/. Le pipeline sélectionne l'export réel local "
            "s'il est présent, sinon l'exemple synthétique. Le script scripts/build_demo_data.py régénère "
            "les exemples raw, curated et rejected.", styles["body"]
        ),
        PageBreak(),
    ])

    story.extend([
        para("5 · Gouvernance, risques et perspectives", styles["h1"]),
        para("Données personnelles et conservation", styles["h2"]),
        para(
            "Le champ name est identifiant et inutile aux indicateurs : il est exclu du curated et des "
            "visualisations. Le CSV réel et les snapshots raw sont ignorés par Git. Les âges et lieux "
            "peuvent encore être réidentifiants par recoupement; l'accès reste local et la finalité est "
            "descriptive. Le raw doit être supprimé ou anonymisé à la fin du projet, sous réserve des "
            "conditions du producteur. La base légale et la licence de redistribution doivent être "
            "confirmées par l'étudiant avec l'enseignant.", styles["body"]
        ),
        para("Compromis et améliorations", styles["h2"]),
        para(
            "Une clé naturelle absente impose une déduplication stricte imparfaite. Les sorties fichiers "
            "n'offrent pas de transaction commune; une interruption en publication peut demander un "
            "rejeu complet. Les pistes utiles sont une publication atomique, SQLite si l'usage SQL croît, "
            "et une deuxième source officielle dont la complémentarité est démontrée. Streaming et "
            "orchestration sont différés tant qu'aucune cadence ne les justifie.", styles["body"]
        ),
        para("Usage d'outils d'IA", styles["h2"]),
        para(
            "GitHub Copilot a assisté l'implémentation, la rédaction documentaire et la revue des tests. "
            "Les changements ont été vérifiés par exécution du pipeline et des tests automatisés. Avant "
            "remise, l'étudiant doit compléter le README en indiquant les parties qu'il a personnellement "
            "relues, comprises et adaptées; cette déclaration ne peut être inventée par l'outil.", styles["body"]
        ),
        para("Livraison", styles["h2"]),
        para(
            "Le dépôt contient le code, les tests, le contrat, le dictionnaire, les architectures SVG, "
            "l'ADR, le test d'incident, les données d'exemple et cette synthèse PDF. Avant dépôt sur Moodle, "
            "vérifier l'accès au dépôt, confirmer les droits sur l'export réel, compléter la déclaration "
            "personnelle d'usage de l'IA et rejouer les commandes depuis un environnement propre.", styles["body"]
        ),
        Spacer(1, 8),
        para(
            "Références de travail : README.md · docs/ADR_001.md · docs/architecture.md · "
            "docs/incident_test.md · config/data_contract.yaml · docs/rgpd_audit.md",
            styles["small"]
        ),
    ])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT_PATH), pagesize=A4, rightMargin=22 * mm, leftMargin=22 * mm,
        topMargin=19 * mm, bottomMargin=22 * mm, title="Synthèse Shark Attacks Collector",
        author="Projet personnel ESEO",
    )
    document.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return OUTPUT_PATH


if __name__ == "__main__":
    print(build_pdf().relative_to(ROOT))