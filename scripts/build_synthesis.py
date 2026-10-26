"""Build the six-page French project synthesis PDF."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.visualize import CURATED_PATH, plot_incident_dashboard
from src.viz.environment_charts import write_environment_charts

OUTPUT_PATH = ROOT / "docs" / "Synthese_Sharks_Collector.pdf"
HYPOTHESES_PATH = ROOT / "reports" / "data" / "environment_hypotheses.csv"
IMAGE_DIR = ROOT / "reports" / "images"
INK = colors.HexColor("#18323f")
TEAL = colors.HexColor("#31708e")
PALE = colors.HexColor("#edf3f5")
MUTED = colors.HexColor("#52616b")
FACT = colors.HexColor("#69764a")
CAUTION = colors.HexColor("#b87935")
WHITE = colors.white


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "kicker": ParagraphStyle(
            "Kicker", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8, leading=10, textColor=TEAL, spaceAfter=4,
        ),
        "title": ParagraphStyle(
            "CoverTitle", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=22, leading=25, textColor=INK, alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "SectionTitle", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=15, leading=18, textColor=INK, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "SubTitle", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=10, leading=12, textColor=TEAL, spaceBefore=5, spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Helvetica",
            fontSize=8.2, leading=10.6, textColor=INK, spaceAfter=4,
        ),
        "compact": ParagraphStyle(
            "Compact", parent=base["BodyText"], fontName="Helvetica",
            fontSize=7.4, leading=9.1, textColor=INK, spaceAfter=2,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["BodyText"], fontName="Helvetica",
            fontSize=6.8, leading=8.3, textColor=MUTED, spaceAfter=2,
        ),
        "table": ParagraphStyle(
            "Table", parent=base["BodyText"], fontName="Helvetica",
            fontSize=7.1, leading=8.6, textColor=INK,
        ),
        "table_head": ParagraphStyle(
            "TableHead", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=7.1, leading=8.6, textColor=WHITE,
        ),
        "question": ParagraphStyle(
            "Question", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=10, leading=13, textColor=INK, spaceAfter=4,
        ),
        "center": ParagraphStyle(
            "Center", parent=base["BodyText"], fontName="Helvetica",
            fontSize=7.2, leading=9, textColor=MUTED, alignment=TA_CENTER,
        ),
    }


def para(text: str, styles: dict[str, ParagraphStyle], style: str = "body") -> Paragraph:
    return Paragraph(text, styles[style])


def make_table(
    rows: list[list[str]],
    widths: list[float],
    styles: dict[str, ParagraphStyle],
    *,
    header: bool = True,
    padding: int = 4,
) -> Table:
    cells = []
    for row_index, row in enumerate(rows):
        cells.append([para(str(value), styles, "table_head" if header and row_index == 0 else "table")
                      for value in row])
    result = Table(cells, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#c9d4d9")),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE]),
        ])
    result.setStyle(TableStyle(commands))
    return result


def callout(label: str, text: str, styles: dict[str, ParagraphStyle], color: colors.Color) -> Table:
    color_html = f"#{int(color.red * 255):02x}{int(color.green * 255):02x}{int(color.blue * 255):02x}"
    content = Paragraph(
        f'<font color="{color_html}"><b>{label}</b></font><br/>{text}',
        styles["body"],
    )
    result = Table([[content]], colWidths=[170 * mm], hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f7f5")),
        ("BOX", (0, 0), (-1, -1), 0.8, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return result


def fitted_image(path: Path, width: float, height: float) -> Image:
    return Image(str(path), width=width, height=height, kind="proportional")


def on_page(canvas, document) -> None:
    canvas.saveState()
    page_width, page_height = A4
    canvas.setFillColor(TEAL)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.drawString(18 * mm, page_height - 11 * mm, "SHARK ATTACKS COLLECTOR  /  ESEO 2026-2027")
    canvas.setStrokeColor(colors.HexColor("#d4dee2"))
    canvas.line(18 * mm, 15 * mm, page_width - 18 * mm, 15 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 10 * mm, "Synthèse du projet · faits observés et hypothèses distingués")
    canvas.drawRightString(page_width - 18 * mm, 10 * mm, f"{document.page:02d} / 06")
    canvas.restoreState()


def hypothesis_rows() -> list[list[str]]:
    definitions = [
        ("H1 · Température de l'eau", "SST jour de l'incident vs témoins"),
        ("H2 · Anomalie", "SST vs climatologie locale"),
        ("H3 · Exposition humaine", "Air, pluie, vent vs témoins"),
        ("H4 · Présence de l'espèce", "Piste GBIF 2025-2026, exploratoire"),
        ("H5 · Pluie antérieure", "Pluie des 3 jours précédents"),
    ]
    observed: dict[str, dict[str, str]] = {}
    if HYPOTHESES_PATH.exists():
        with HYPOTHESES_PATH.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                hypothesis_id = row.get("hypothesis_id", "")
                if hypothesis_id:
                    observed[hypothesis_id] = row

    rows = [["Hypothèse / test", "Résultat chiffré", "Statut final", "n"]]
    for hypothesis_id, description in definitions:
        key = hypothesis_id.split(" · ", 1)[0]
        result = observed.get(key, {})
        status = result.get(
            "status",
            "Non concluante (échantillon ou données insuffisants)",
        )
        count = result.get("n_incident", "0") or "0"
        numeric_result = result.get("result", "n=0; données non calculées")
        rows.append([
            f"{hypothesis_id}<br/><font color='#52616b'>{description}</font>",
            numeric_result,
            status,
            count,
        ])
    return rows


def build_pdf() -> Path:
    styles = make_styles()
    story = []

    # Page 1: quick start first, followed by the project's question and scope.
    story.extend([
        para("Shark Attacks Collector", styles, "title"),
        Table([[para(
            '<font color="#31708e"><b>LANCER LE PROJET EN 5 MINUTES</b></font><br/>'
            "1. Installer Python 3.11+ et les dépendances de <b>requirements.txt</b>.<br/>"
            "2. Télécharger l'export GSAF depuis "
            '<link href="https://www.kaggle.com/datasets/teajay/global-shark-attacks">'
            '<font color="#31708e"><u>Kaggle</u></font></link>, le renommer '
            "<b>global_shark_attacks_raw.csv</b> et le placer dans <b>data/raw/</b>.<br/>"
            "3. Depuis la racine : <b>python -m src.pipeline</b>, puis "
            "<b>python -m pytest -q</b>.<br/>"
            "Sans export réel, le jeu synthétique de 121 lignes valide le parcours local.",
            styles,
        )]], colWidths=[170 * mm], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALE),
            ("BOX", (0, 0), (-1, -1), 0.8, TEAL),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])),
        Spacer(1, 7),
        para("01 · Question et périmètre", styles, "h1"),
        para(
            "Où et quand les incidents de requins sont-ils déclarés ?<br/>"
            "Dans quelles conditions environnementales les signalements surviennent-ils ?<br/>"
            "Que peut-on tester sans confondre association, cause et risque individuel ?",
            styles, "question",
        ),
        callout(
            "FAIT OBSERVÉ · dernier run réel de référence",
            "<b>6 890 entrées -> 6 687 acceptées, 194 rejetées et 9 doublons retirés (PASS).</b> "
            "Ces nombres décrivent un export ponctuel, pas le risque de morsure ni l'ensemble "
            "des incidents réels.",
            styles, FACT,
        ),
        Spacer(1, 6),
        para("Ce que je cherche à produire", styles, "h2"),
        para(
            "Je construis un pipeline reproductible qui transforme les déclarations GSAF en "
            "fichiers contrôlés et indicateurs descriptifs, puis teste avec prudence des pistes "
            "environnementales. Aucune API ne fournit la cause d'une attaque.",
            styles,
        ),
        make_table([
            ["Besoin", "Indicateur livré"],
            ["Choisir des lieux ou périodes à examiner", "Comptes par pays, localité, année et mois"],
            ["Comparer une saisonnalité", "Mois, avec sensibilité aux dates du 1er janvier"],
            ["Formuler des pistes environnementales", "H1-H5, tests et statuts explicites"],
        ], [69 * mm, 101 * mm], styles),
        Spacer(1, 5),
        para(
            "Je traite chaque ligne comme un incident déclaré. La couverture, la fréquentation "
            "humaine et la sous-déclaration ne sont pas contrôlées.",
            styles, "small",
        ),
        PageBreak(),
    ])

    # Page 2: business need, use cases, sources and collection decisions.
    story.extend([
        para("02 · Besoin, usages et sources", styles, "h1"),
        callout(
            "FAIT OBSERVÉ",
            "Le GSAF est un export déclaré et ponctuel. Les compteurs décrivent son contenu "
            "et dépendent aussi de la couverture et des pratiques de signalement.",
            styles, FACT,
        ),
        Spacer(1, 5),
        make_table([
            ["Usage", "Question explorée", "Indicateur"],
            ["Localiser", "Où les déclarations sont-elles nombreuses ?", "Comptes par lieu et pays"],
            ["Comparer les périodes", "Comment les déclarations varient-elles ?", "Comptes par année et mois"],
            ["Tester l'environnement", "Quelles conditions coïncident avec les dates ?", "SST, anomalie, météo et témoins"],
        ], [34 * mm, 68 * mm, 68 * mm], styles),
        Spacer(1, 6),
        para("Sources retenues", styles, "h2"),
        make_table([
            ["Source", "Usage et précaution"],
            ["Global Shark Attack File (Kaggle)", "CSV source pour les incidents; accès ponctuel, licence et redistribution à vérifier."],
            ["NOAA OISST v2.1 / ERDDAP", "Jeu ncdcOisst21Agg_LonPM180; une requête par cellule unique sur 1982-2023, grille 0,25°. Climatologie locale 1982-2011, fenêtre de 31 jours; repli côtier si cellule terrestre."],
            ["Open-Meteo Archive (ERA5)", "Température max, pluie et vent; données météo indirectes, attribution CC BY 4.0."],
            ["GBIF", "Occurrences 2025-2026 conservées comme piste exploratoire, sans attribution d'espèce responsable."],
        ], [56 * mm, 114 * mm], styles),
        Spacer(1, 6),
        callout(
            "HYPOTHÈSES, NON ÉTABLIES",
            "H1-H5 sont des tests d'associations à partir de données disponibles. Aucun résultat "
            "ne démontre une cause biologique ou un risque individuel.",
            styles, CAUTION,
        ),
        Spacer(1, 5),
        para(
            "Je ne scrape pas le site GSAF et ne contourne pas son authentification. Le CSV réel "
            "et les champs identifiants restent locaux et hors Git; l'échantillon synthétique "
            "permet de tester le pipeline sans réseau.",
            styles, "compact",
        ),
        PageBreak(),
    ])

    # Page 3: architecture, quality rules, run traceability and recovery.
    story.extend([
        para("03 · Architecture, qualité et reprise", styles, "h1"),
        para("Un batch local, lisible et rejouable", styles, "h2"),
        make_table([
            ["Source CSV", "Snapshot raw UTC", "Validation", "Curated + rejets", "Rapports"],
            ["GSAF local ou sample", "Copie + SHA-256", "5 règles + compteurs", "Séparation des lignes", "CSV, PNG, JSON"],
        ], [31 * mm, 35 * mm, 35 * mm, 36 * mm, 33 * mm], styles, padding=3),
        Spacer(1, 6),
        callout(
            "FAIT OBSERVÉ · dernier run réel de référence",
            "<b>PASS opérationnel</b>; le statut qualité est assorti d'avertissements parce que "
            "les rejets sont conservés et comptabilisés.",
            styles, FACT,
        ),
        Spacer(1, 5),
        make_table([
            ["Contrôle", "Résultat", "Traitement"],
            ["Pays", "51", "Rejet si absent"],
            ["Année", "133", "Rejet si hors plage"],
            ["Type", "20", "Rejet si catégorie inconnue"],
            ["Âge", "0", "Valeur suspecte corrigée à NULL"],
            ["Unicité", "9", "Doublons stricts supprimés et comptés"],
        ], [42 * mm, 26 * mm, 102 * mm], styles, padding=3),
        Spacer(1, 5),
        make_table([
            ["Entrées", "Acceptées", "Rejetées", "Doublons", "Dernière date"],
            ["6 890", "6 687", "194", "9", "2023-08-16"],
        ], [34 * mm, 34 * mm, 34 * mm, 34 * mm, 34 * mm], styles, padding=3),
        Spacer(1, 6),
        para("Traçabilité et reprise", styles, "h2"),
        para(
            "Chaque run journalise un identifiant, l'empreinte et la taille de la source, les "
            "compteurs, la durée et les sorties. Un test de source absente vérifie le rapport FAIL "
            "et le code d'échec; après correction, le pipeline peut être relancé. Les CSV curated "
            "et rejected sont remplacés à chaque exécution, tandis que les snapshots raw servent au rejeu.",
            styles,
        ),
        para(
            "Le CSV suffit à un export ponctuel de cette taille. Je n'introduis ni entrepôt ni "
            "streaming sans besoin mesurable; SQLite reste une option si les usages SQL augmentent. "
            "Les caches NOAA et météo sont locaux; une API indisponible produit un statut WARN.",
            styles, "compact",
        ),
        para(
            "Le snapshot raw conserve les données source : il reste local, ignoré par Git et à "
            "supprimer ou anonymiser selon les conditions du producteur.",
            styles, "small",
        ),
        PageBreak(),
    ])

    # Page 4: observed results; explanatory notes sit directly beside their charts.
    story.extend([
        para("04 · Ce que montrent les données", styles, "h1"),
        callout(
            "FAIT OBSERVÉ · incidents déclarés",
            "Le tableau de bord résume des comptes contenus dans le fichier. Les évolutions "
            "peuvent aussi refléter la fréquentation humaine, la couverture et la déclaration.",
            styles, FACT,
        ),
        Spacer(1, 4),
    ])
    dashboard = IMAGE_DIR / "dashboard_incidents.png"
    if CURATED_PATH.exists():
        plot_incident_dashboard()
    if dashboard.exists():
        story.append(fitted_image(dashboard, 170 * mm, 91 * mm))
    story.extend([
        para(
            "<b>Lecture du graphique annuel :</b> les signalements culminent autour des années "
            "2010; la baisse récente ne prouve pas une baisse des événements réels. "
            "<b>Lecture du graphique mensuel :</b> janvier est le mois le plus représenté toutes "
            "dates confondues; en excluant les 1ers janvier, juillet devient le plus représenté.",
            styles, "compact",
        ),
        Spacer(1, 4),
    ])
    gbif_chart = IMAGE_DIR / "synthese_especes_gbif.png"
    if gbif_chart.exists():
        gbif_text = Paragraph(
            '<font color="#69764a"><b>FAIT OBSERVÉ · rapprochement GBIF</b></font><br/>'
            "1 011 lieux d'attaque géocodés comparés; occurrences dans un rayon de 100 km :"
            "<br/><b>Carcharhinus leucas :</b> 642 · <b>Galeocerdo cuvier :</b> 526"
            "<br/><b>Carcharodon carcharias :</b> 116 · <b>Rhincodon typus :</b> 37"
            "<br/><font color=\"#b87935\"><b>Limite :</b></font> une attaque peut être proche "
            "de plusieurs espèces; l'effort d'observation varie. Ces proximités ne prouvent ni "
            "la présence le jour de l'incident ni l'espèce responsable.",
            styles["compact"],
        )
        gbif_panel = Table(
            [[fitted_image(gbif_chart, 72 * mm, 48 * mm), gbif_text]],
            colWidths=[74 * mm, 96 * mm],
            hAlign="LEFT",
        )
        gbif_panel.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.extend([gbif_panel, PageBreak()])
    else:
        story.extend([
            callout(
                "FAIT OBSERVÉ · rapprochement géographique GBIF",
                "1 011 lieux d'attaque géocodés; comptes à <= 100 km : Carcharhinus leucas 642, "
                "Galeocerdo cuvier 526, Carcharodon carcharias 116, Rhincodon typus 37. "
                "Les proximités ne prouvent pas l'espèce responsable.",
                styles, CAUTION,
            ),
            PageBreak(),
        ])

    # Page 5: environmental plots, hypothesis status table and cautious reading.
    chart_paths = write_environment_charts()
    story.extend([
        para("05 · Hypothèses environnementales", styles, "h1"),
        callout(
            "HYPOTHÈSES, NON ÉTABLIES",
            "Les graphiques portent la taille d'échantillon et la source. Sans données enrichies "
            "disponibles, ils affichent n=0 et les statuts restent non concluants; aucune donnée "
            "n'est inventée pour remplir les figures.",
            styles, CAUTION,
        ),
        Spacer(1, 4),
        Table([
            [fitted_image(chart_paths["sst_controls"], 83 * mm, 43 * mm),
             fitted_image(chart_paths["sst_anomaly"], 83 * mm, 43 * mm)],
            [fitted_image(chart_paths["monthly_sst"], 83 * mm, 43 * mm),
             fitted_image(chart_paths["air_controls"], 83 * mm, 43 * mm)],
            [fitted_image(chart_paths["hypotheses"], 83 * mm, 39 * mm), ""],
        ], colWidths=[85 * mm, 85 * mm], style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("SPAN", (0, 2), (1, 2)),
            ("LEFTPADDING", (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ])),
        Spacer(1, 3),
        make_table(
            hypothesis_rows(),
            [44 * mm, 64 * mm, 48 * mm, 14 * mm],
            styles,
            padding=2,
        ),
        Spacer(1, 3),
        para(
            "<b>Lecture prudente :</b> H1 compare la SST aux témoins du même lieu et de la même "
            "année; H2 compare la SST à une climatologie locale (1982-2011, fenêtre de 31 jours); "
            "H3 compare météo et témoins, avec saison calculée par hémisphère; H4 reste "
            "exploratoire (GBIF 2025-2026); H5 teste la pluie des trois jours précédents comme "
            "indicateur indirect de turbidité. "
            "Une association n'est pas une cause.",
            styles, "small",
        ),
        PageBreak(),
    ])

    # Page 6: caveats, governance, AI disclosure and reproducible links.
    story.extend([
        para("06 · Limites, gouvernance et suite", styles, "h1"),
        callout(
            "HYPOTHÈSES, NON ÉTABLIES",
            "Aucune source environnementale ne permet d'établir la cause d'un incident. Les "
            "conditions météorologiques et océaniques sont des indicateurs indirects, sensibles "
            "à la qualité des dates, coordonnées et témoins.",
            styles, CAUTION,
        ),
        Spacer(1, 5),
        para("Limites d'interprétation", styles, "h2"),
        para(
            "Le jeu source est ponctuel, comporte des dates et lieux de précision variable et "
            "ne mesure pas l'exposition humaine. Une coordonnée peut représenter un centre de "
            "localité. Les témoins et seuils statistiques ne corrigent pas les biais de couverture. "
            "Les résultats H1-H5 sont exploratoires et ne permettent pas d'inférer causalité ou risque.",
            styles,
        ),
        para("Vie privée et gouvernance", styles, "h2"),
        para(
            "Le champ <b>name</b> est exclu des échantillons, du curated et des indicateurs. "
            "Le CSV réel et les snapshots raw ne sont pas versionnés. Les âges et lieux peuvent "
            "rester réidentifiants par recoupement; je limite donc l'usage au descriptif et conserve "
            "les données source localement, sous réserve de licence et de conditions de conservation.",
            styles,
        ),
        para("Pistes de suite", styles, "h2"),
        para(
            "La vérification directe des métadonnées ERDDAP NOAA (.html et .das) reste à faire "
            "car le serveur n'était pas joignable lors de la génération; enrichir uniquement les "
            "incidents géocodés; évaluer les analyses quand les données environnementales sont "
            "présentes; conserver les statuts WARN et les limites visibles dans chaque restitution.",
            styles,
        ),
        para("Reproductibilité et transparence", styles, "h2"),
        para(
            "Les tests utilisent des fixtures et mocks, sans appels réseau. L'échantillon synthétique "
            "de 121 lignes permet une exécution locale. GitHub Copilot a aidé à l'implémentation, "
            "à la documentation et aux tests; les choix, vérifications et déclarations personnelles "
            "restent à la charge de l'étudiant.",
            styles,
        ),
        make_table([
            ["Pour approfondir", "Fichier ou commande"],
            ["Installer et relancer", "README.md · python -m src.pipeline · python -m pytest -q"],
            ["Architecture et règles", "docs/architecture.md · config/data_contract.yaml"],
            ["Sources et méthodes environnementales", "docs/source_assessment.md · docs/ADR_002.md"],
            ["Dictionnaire et limites", "docs/data_dictionary.md · docs/rgpd_audit.md"],
            ["Code du dépôt", '<link href="https://github.com/noahgog25/shark-attacks-collector">'
             '<font color="#31708e"><u>github.com/noahgog25/shark-attacks-collector</u></font></link>'],
        ], [61 * mm, 109 * mm], styles, padding=3),
        Spacer(1, 5),
        para(
            "Je ne versionne ni le CSV réel ni la colonne name. Les graphiques environnementaux "
            "seront mis à jour uniquement à partir de données enrichies effectivement disponibles.",
            styles, "small",
        ),
    ])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title="Synthèse Shark Attacks Collector",
        author="Projet Shark Attacks Collector",
    )
    document.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return OUTPUT_PATH


if __name__ == "__main__":
    print(f"Synthèse générée -> {build_pdf()}")
