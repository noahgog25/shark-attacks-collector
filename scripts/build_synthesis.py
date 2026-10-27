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

OUTPUT_PATH = ROOT / "docs" / "Synthese_Sharks_Collector.pdf"
ARCHITECTURE_V2_IMAGE = ROOT / "docs" / "architecture_v2.png"
HYPOTHESES_PATH = ROOT / "reports" / "data" / "environment_hypotheses.csv"
IMAGE_DIR = ROOT / "reports" / "images"
INK = colors.HexColor("#152b36")
TEAL = colors.HexColor("#245f78")
PALE = colors.HexColor("#edf3f5")
MUTED = colors.HexColor("#37474f")
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
            fontSize=8.6, leading=11.2, textColor=INK, spaceAfter=4,
        ),
        "compact": ParagraphStyle(
            "Compact", parent=base["BodyText"], fontName="Helvetica",
            fontSize=8.0, leading=10, textColor=INK, spaceAfter=2,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["BodyText"], fontName="Helvetica",
            fontSize=7.6, leading=9.4, textColor=INK, spaceAfter=2,
        ),
        "table": ParagraphStyle(
            "Table", parent=base["BodyText"], fontName="Helvetica",
            fontSize=7.6, leading=9.2, textColor=INK,
        ),
        "table_head": ParagraphStyle(
            "TableHead", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=7.6, leading=9.2, textColor=WHITE,
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
    canvas.setFillColor(WHITE)
    canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(
        18 * mm,
        page_height - 11 * mm,
        "SHARK ATTACKS COLLECTOR  /  GOGEON Noah  /  ESEO 2026-2027",
    )
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
            '1. Ouvrir ou cloner le <link href="https://github.com/noahgog25/shark-attacks-collector">'
            '<font color="#31708e"><u>dépôt GitHub Shark Attacks Collector</u></font></link>.<br/>'
            "2. Installer Python 3.11+ et les dépendances de <b>requirements.txt</b>.<br/>"
            "3. Télécharger le dataset Kaggle <b>« Sharks Attack collector »</b> "
            "(Global Shark Attack File / GSAF) depuis "
            '<link href="https://www.kaggle.com/datasets/gauravkumar2525/shark-attacks">'
            '<font color="#31708e"><u>la page Kaggle utilisée</u></font></link>, le renommer '
            "<b>global_shark_attacks_raw.csv</b> et le placer dans <b>data/raw/</b>.<br/>"
            "4. Depuis la racine : <b>python -m src.pipeline</b>, puis "
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
        para("Utilisateurs et indicateurs", styles, "h2"),
        para(
            "Je vise un étudiant, un enseignant ou un analyste qui veut choisir des lieux et des "
            "périodes à examiner, pas calculer un risque individuel. Je fournis au moins trois "
            "indicateurs : comptes par pays/localité/année, saisonnalité mensuelle, et tests "
            "environnementaux exploratoires avec leur statut.",
            styles, "compact",
        ),
        make_table([
            ["Besoin", "Indicateur livré"],
            ["Choisir des lieux ou périodes à examiner", "Comptes par pays, localité, année et mois"],
            ["Comparer une saisonnalité", "Mois, avec sensibilité aux dates du 1er janvier"],
            ["Formuler des pistes environnementales", "H1-H5, tests et statuts explicites"],
        ], [69 * mm, 101 * mm], styles),
        Spacer(1, 6),
        para("Sources et précautions", styles, "h2"),
        make_table([
            ["Source", "Apport", "Précaution"],
            ["« Sharks Attack collector » (GSAF via Kaggle)", "Incidents déclarés", "Export ponctuel; droits de redistribution à vérifier."],
            ["GBIF", "Occurrences géographiques", "Présence observée, pas abondance ni identification d'attaque."],
            ["Nominatim / OSM", "Géocodage de lieux", "Centre-ville possible; pas une position GPS d'incident."],
            ["NOAA OISST / ERDDAP", "SST quotidienne et anomalie", "Grille 0,25°; vérifier les métadonnées avant collecte complète."],
            ["Open-Meteo Archive", "Air, pluie et vent", "Indicateurs indirects; indisponibilité signalée WARN."],
        ], [43 * mm, 48 * mm, 79 * mm], styles, padding=3),
        Spacer(1, 5),
        para(
            "Je traite chaque ligne comme un incident déclaré. La couverture, la fréquentation "
            "humaine et la sous-déclaration ne sont pas contrôlées.",
            styles, "small",
        ),
        Spacer(1, 4),
        callout(
            "CE QUE JE NE MESURE PAS",
            "Je ne calcule ni taux d'attaque par personne exposée, ni dangerosité biologique, "
            "ni cause d'un incident. Je décris des déclarations et teste des associations.",
            styles, CAUTION,
        ),
        PageBreak(),
    ])

    # Page 2: business need, use cases, sources and collection decisions.
    story.extend([
        para("02 · Architecture et décisions", styles, "h1"),
        callout(
            "QUESTION D'ARCHITECTURE",
            "Je construis une chaîne utile, fiable et proportionnée au besoin : l'export source "
            "est ponctuel et le volume observé (6 890 lignes) ne justifie pas une plateforme distribuée.",
            styles, FACT,
        ),
        Spacer(1, 5),
        make_table([
            ["Couche", "Rôle dans mon pipeline"],
            ["Source", "CSV GSAF local ou échantillon synthétique"],
            ["Raw", "Copie horodatée UTC, conservée pour diagnostiquer et rejouer"],
            ["Validation", "Profilage, contrat versionné, règles et motifs de rejet"],
            ["Curated / rejected", "Je sépare les lignes acceptées et rejetées; sorties remplaçables"],
            ["Produit", "Rapport JSON, tableaux CSV et visualisations descriptives"],
        ], [43 * mm, 127 * mm], styles),
        Spacer(1, 6),
        para("Pourquoi batch, fichiers et ce grain ?", styles, "h2"),
        para(
            "Je collecte par batch car la source n'est ni un flux continu ni mise à jour à cadence "
            "garantie. Un snapshot raw UTC avec SHA-256 garde la preuve d'entrée. À cette taille, "
            "les CSV sont faciles à inspecter; SQLite ajouterait migrations et maintenance sans "
            "besoin démontré, tandis que streaming, Warehouse et Mart n'ont pas d'usage mesurable. "
            "Le grain est un incident déclaré; sans clé naturelle, je déduplique strictement sur les "
            "champs disponibles, avec le risque de fusionner deux événements identiques.",
            styles, "compact",
        ),
        Spacer(1, 4),
        make_table([
            ["Option", "Décision et compromis"],
            ["CSV batch", "Retenu : simple, inspectable, rejouable pour un export ponctuel."],
            ["SQLite", "Écarté pour l'instant : transactions utiles, mais migrations/maintenance en plus."],
            ["Streaming / entrepôt", "Écartés : aucune cadence ni intégration ne les justifie."],
        ], [43 * mm, 127 * mm], styles, padding=3),
        Spacer(1, 4),
        para(
            "Je ne conserve pas le CSV réel dans le dépôt : il peut contenir des noms et reste "
            "soumis aux conditions du producteur. J'utilise l'échantillon synthétique pour "
            "permettre une démonstration reproductible sans divulguer ces données.",
            styles, "compact",
        ),
        para(
            "La décision est détaillée dans l'ADR 001; les architectures V1 et V2 sont livrées en SVG.",
            styles, "small",
        ),
        make_table([
            ["Version", "Évolution montrée"],
            ["V1", "Flux source → raw → contrôles → curated / rejets → indicateurs."],
            ["V2", "Entrée configurable, profilage, schéma, logs, rapport de run et reprise."],
        ], [31 * mm, 139 * mm], styles, padding=3),
        Spacer(1, 4),
        callout(
            "HYPOTHÈSES, NON ÉTABLIES",
            "H1-H5 sont des tests d'associations à partir de données disponibles. Aucun résultat "
            "ne démontre une cause biologique ou un risque individuel.",
            styles, CAUTION,
        ),
        Spacer(1, 4),
        para(
            "Je ne scrape pas le site GSAF et ne contourne pas son authentification. Pour l'analyse "
            "réelle, je télécharge l'export Kaggle; sinon, les 121 lignes synthétiques valident "
            "le pipeline sans données personnelles et sans accès réseau.",
            styles, "compact",
        ),
        PageBreak(),
    ])

    # Page 3: architecture, quality rules, run traceability and recovery.
    story.extend([
        para("03 · Architecture, qualité et reprise", styles, "h1"),
        para("Architecture V2 · cible proportionnée et observable", styles, "h2"),
        fitted_image(ARCHITECTURE_V2_IMAGE, 170 * mm, 79 * mm),
        Spacer(1, 3),
        callout(
            "CONTRÔLES ET COMPTEURS DU RUN DE RÉFÉRENCE (18/10/2026)",
            "Le traitement s'est terminé normalement : <b>PASS</b>. Le contrôle qualité reste "
            "<b>PASS_WITH_WARNINGS</b>, car 194 lignes ont été rejetées. Ce n'est pas un échec "
            "du lancement : le rapport détaille chaque règle et conserve les rejets pour examen.",
            styles, FACT,
        ),
        Spacer(1, 4),
        make_table([
            ["Run", "Entrées", "Acceptées", "Rejetées", "Doublons", "État"],
            ["20261018T122103101173Z", "6 890", "6 687", "194", "9", "PASS"],
        ], [53 * mm, 23 * mm, 25 * mm, 23 * mm, 23 * mm, 23 * mm], styles, padding=3),
        Spacer(1, 4),
        make_table([
            ["Contrôle", "Échecs / action"],
            ["Pays", "51 · rejet"],
            ["Année", "133 · rejet"],
            ["Type", "20 · rejet"],
            ["Âge", "0 · corrigé à NULL"],
            ["Unicité", "9 · doublons supprimés"],
        ], [46 * mm, 124 * mm], styles, padding=3),
        Spacer(1, 4),
        para("Observabilité et reprise", styles, "h2"),
        para(
            "Pour ce run : durée 0,27 s · dernière date d'incident 2023-08-16 · âge de cette date "
            "1 159 jours. La fraîcheur porte sur la date de l'événement, pas celle de publication "
            "du fichier. Le rapport conserve run_id, empreinte, compteurs et sorties. J'ai testé "
            "une source absente : le pipeline écrit un rapport FAIL et retourne un code d'erreur; "
            "après correction de la source, je relance le même point d'entrée.",
            styles, "small",
        ),
        Spacer(1, 3),
        para(
            "Je remplace les sorties curated/rejected à chaque run; le snapshot raw local sert au "
            "rejeu et reste exclu de Git. Le batch CSV est proportionné à l'export (ADR 001); "
            "une API météo/NOAA indisponible produit WARN et le cache est réutilisé s'il existe.",
            styles, "compact",
        ),
        Spacer(1, 2),
        para("Usage d'outils d'IA", styles, "h2"),
        para(
            "J'ai utilisé GitHub Copilot comme aide pour certaines tâches d'implémentation, de "
            "documentation et de tests. Je reste responsable des choix initiaux et d'implémentation "
            "du projet, de la mise en place de la documentation, ainsi que de la compréhension et "
            "des choix présentés pour ce projet. Le pipeline et les tests ont été exécutés.",
            styles, "small",
        ),
        PageBreak(),
    ])

    # Page 4: descriptive results and the data-to-map workflow.
    story.extend([
        para("04 · Ce que montrent les données et la carte GBIF", styles, "h1"),
        para(
            "Dans l'export traité, les déclarations culminent autour des années 2010 et "
            "<b>New Smyrna Beach</b> est la localité connue la plus représentée. Ce sont des "
            "comptes de déclarations, sensibles à la fréquentation, à la couverture et aux pratiques "
            "de signalement; ils ne mesurent pas un risque.",
            styles, "compact",
        ),
        Spacer(1, 2),
    ])
    dashboard = IMAGE_DIR / "dashboard_incidents.png"
    if CURATED_PATH.exists():
        plot_incident_dashboard()
    if dashboard.exists():
        story.append(fitted_image(dashboard, 144 * mm, 84 * mm))
    story.extend([
        para(
            "<b>Sensibilité des dates :</b> 347 dates (5,3 %) sont au 1er janvier. Le mois le "
            "plus représenté passe de janvier à juillet quand je les exclue; faute de champ de "
            "précision, c'est un test de sensibilité, pas une correction. Sur 6 516 incidents datés, "
            "5 990 ont une activité connue. L'association mois-activité est faible "
            "(V de Cramer = 0,083; 5 activités + « Autres »); la rosace normalise chaque activité "
            "séparément et ne compare pas leurs volumes ni ne démontre une cause.",
            styles, "small",
        ),
    ])
    story.extend([
        Spacer(1, 3),
        para("Carte des occurrences GBIF : de quelles données suis-je parti ?", styles, "h2"),
    ])
    occurrence_map = IMAGE_DIR / "species_occurrences.png"
    if occurrence_map.exists():
        map_explanation = Paragraph(
            "<b>1 · Données d'entrée.</b> Pour chacune des quatre espèces, je résous le nom "
            "taxonomique puis interroge GBIF pour les occurrences avec coordonnées (limite de "
            "100 par espèce). J'obtiens quatre CSV locaux, soit 400 lignes (31/01/2025-22/08/2026), "
            "avec dates, coordonnées et stades de vie. "
            "<br/><b>2 · Préparation.</b> Je concatène les CSV, convertis les coordonnées en "
            "nombres et écarte les lignes sans latitude, longitude ou espèce. "
            "<br/><b>3 · Fond de carte.</b> J'utilise les polygones de pays Natural Earth déjà "
            "conservés dans <i>data/reference/ne_110m_admin_0_countries.geojson</i>. "
            "<br/><b>4 · Tracé.</b> Avec <i>python -m src.species_visualize</i>, Matplotlib colore "
            "les points par espèce : nuage longitude/latitude et histogrammes de latitude en haut, "
            "carte avec frontières en bas. La figure est "
            "<i>reports/images/species_occurrences.png</i>."
            "<br/><font color=\"#b87935\"><b>Limite :</b></font> le nombre de points n'est pas "
            "une mesure d'abondance; il dépend des signalements GBIF et de leur effort "
            "d'observation. Ces occurrences récentes ne couvrent pas l'historique des incidents.",
            styles["small"],
        )
        map_panel = Table(
            [[fitted_image(occurrence_map, 111 * mm, 88 * mm), map_explanation]],
            colWidths=[113 * mm, 57 * mm],
            hAlign="LEFT",
        )
        map_panel.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        story.append(map_panel)
    else:
        story.append(para(
            "Je pars des quatre CSV GBIF normalisés (un par espèce) et d'un fond Natural Earth "
            "GeoJSON local. La figure n'est pas disponible dans ce clone; aucun réseau n'est "
            "appelé par la génération du PDF.",
            styles, "compact",
        ))
    story.extend([
        Spacer(1, 2),
        make_table([
            ["Candidate géographique", "<= 25 km", "<= 100 km / 1 011", "Juvéniles <= 100 km"],
            ["Carcharhinus leucas", "469", "642 (63,5 %)", "534"],
            ["Carcharodon carcharias", "54", "116 (11,5 %)", "26"],
            ["Galeocerdo cuvier", "53", "526 (52,0 %)", "24"],
            ["Rhincodon typus", "0", "37 (3,7 %)", "0"],
        ], [56 * mm, 27 * mm, 46 * mm, 41 * mm], styles, padding=2),
        Spacer(1, 2),
        para(
            "Les rapprochements sont des paires non exclusives : une attaque peut compter pour "
            "plusieurs espèces. Une coordonnée d'attaque peut être un centre de localité; une "
            "occurrence juvénile ne prouve pas une nurserie. Je parle donc de présence régionale "
            "documentée, jamais de l'espèce responsable ou d'une relation temporelle.",
            styles, "small",
        ),
        PageBreak(),
    ])

    # Page 5: observed seasonal analysis and environmental tests without data.
    story.extend([
        para("05 · Activités, saisonnalité et hypothèses", styles, "h1"),
        callout(
            "FAIT OBSERVÉ · SAISONNALITÉ DES ACTIVITÉS",
            "Sur 5 990 incidents datés avec activité connue, l'association mois-activité est faible "
            "(V de Cramer = 0,083; cinq activités principales + « Autres »). La rosace montre, "
            "pour chaque activité, sa répartition mensuelle normalisée.",
            styles, FACT,
        ),
        Spacer(1, 5),
        fitted_image(IMAGE_DIR / "seasonal_activity_rose.png", 144 * mm, 83 * mm),
        Spacer(1, 3),
        para(
            "Je lis chaque anneau séparément : la couleur compare les mois au sein d'une activité, "
            "pas le volume entre activités. L'analyse ne contrôle ni le pays, ni l'année, ni la "
            "fréquentation; cette association descriptive ne prouve pas une cause.",
            styles, "compact",
        ),
        Spacer(1, 5),
        para("Hypothèses environnementales : résultats disponibles", styles, "h2"),
        callout(
            "DONNÉES INSUFFISANTES POUR CONCLURE",
            "Aucun résultat d'enrichissement SST/météo/témoins n'est disponible localement pour ce "
            "rendu. Je n'affiche donc aucun graphique environnemental vide : les cinq tests restent "
            "non concluants, avec n=0. Les occurrences GBIF sont présentées séparément comme "
            "chevauchements géographiques récents.",
            styles, CAUTION,
        ),
        Spacer(1, 4),
        make_table(
            hypothesis_rows(),
            [43 * mm, 62 * mm, 51 * mm, 14 * mm],
            styles,
            padding=2,
        ),
        Spacer(1, 3),
        para(
            "H1 : SST le jour de l'incident vs témoins du même lieu et de la même année. "
            "H2 : SST vs climatologie locale 1982-2011 (fenêtre de 31 jours). "
            "H3 : température max de l'air plus élevée, pluie et vent plus faibles que les témoins; "
            "je calcule la saison par hémisphère (décalage de six mois au sud). "
            "H4 : piste exploratoire GBIF (occurrences 2025-2026). "
            "H5 : pluie des trois jours précédents, indicateur indirect de turbidité. "
            "Les tests d'association ne démontrent jamais une cause.",
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
            "les données source localement, sous réserve de licence et de conditions de conservation. "
            "Je garde le raw pour le rejeu pendant le projet, puis le supprime ou l'anonymise selon "
            "les règles du producteur.",
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
            "Les tests utilisent des fixtures et mocks, sans appels réseau; l'échantillon "
            "synthétique de 121 lignes permet de rejouer le pipeline localement. Je vérifie les "
            "sorties avant de les interpréter et documente les limites des sources.",
            styles,
        ),
        make_table([
            ["Pour approfondir", "Fichier ou commande"],
            ["Installer et relancer", "README.md (macOS, Linux, PowerShell, cmd) · python -m src.pipeline · python -m pytest -q"],
            ["Architecture", "docs/architecture.md · docs/architecture_v1.svg · docs/architecture_v2.svg"],
            ["Règles et champs", "config/data_contract.yaml · docs/data_dictionary.md"],
            ["Sources et méthodes environnementales", "docs/source_assessment.md · docs/ADR_002.md"],
            ["Choix de stockage", "docs/ADR_001.md"],
            ["Test d'incident et gouvernance", "docs/incident_test.md · docs/rgpd_audit.md"],
            ["Code du dépôt", '<link href="https://github.com/noahgog25/shark-attacks-collector">'
             '<font color="#31708e"><u>github.com/noahgog25/shark-attacks-collector</u></font></link>'],
        ], [61 * mm, 109 * mm], styles, padding=2),
        Spacer(1, 4),
        para("Ce que je livre", styles, "h2"),
        para(
            "Je produis un CSV curated sans nom, les lignes rejetées avec leur motif, un profil "
            "source, un rapport de run, des tableaux de hotspots et de saisonnalité, des visualisations "
            "et cette synthèse. Une autre personne peut reprendre les commandes depuis le README "
            "dans un environnement propre; la démonstration tient dans le pipeline et ses sorties. "
            "Le raw réel reste exclu de Git; je vérifie les droits de redistribution et les règles "
            "de conservation avant toute remise.",
            styles, "compact",
        ),
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
