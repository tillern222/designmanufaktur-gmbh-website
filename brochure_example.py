"""
Beispiel-Broschüre: "Designmanufaktur GmbH"
DIN A4, 8 Seiten, 3mm Anschnitt, CMYK, Schnittmarken
"""

from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import CMYKColor, white, black
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import math

# ─── DOKUMENT-SETUP ──────────────────────────────────────────────────────────
BLEED = 3 * mm          # Anschnitt
MARK_OFFSET = 5 * mm    # Abstand Schnittmarken
MARK_LENGTH = 8 * mm    # Länge Schnittmarken

PAGE_W, PAGE_H = A4                          # 210 × 297 mm (Endformat)
DOC_W = PAGE_W + 2 * BLEED                  # Dokumentbreite inkl. Anschnitt
DOC_H = PAGE_H + 2 * BLEED                  # Dokumenthöhe inkl. Anschnitt

# ─── CMYK FARBEN ─────────────────────────────────────────────────────────────
# Primärfarben Corporate Design
BRAND_DARK   = CMYKColor(0, 0, 0, 0.92)        # Fast Schwarz (Tiefschwarz)
BRAND_ACCENT = CMYKColor(0.82, 0.22, 0, 0.08)  # Kräftiges Blau
BRAND_LIGHT  = CMYKColor(0.08, 0.03, 0, 0.04)  # Hellblau / Hintergrund
BRAND_WARM   = CMYKColor(0, 0.28, 0.88, 0.02)  # Warmes Orange/Gold
GRAY_MEDIUM  = CMYKColor(0, 0, 0, 0.45)
GRAY_LIGHT   = CMYKColor(0, 0, 0, 0.10)
WHITE        = CMYKColor(0, 0, 0, 0)

# ─── HILFS-FUNKTIONEN ────────────────────────────────────────────────────────

def draw_crop_marks(c, page_w, page_h, bleed, offset, length):
    """Schnittmarken an allen vier Ecken zeichnen."""
    c.setStrokeColorCMYK(0, 0, 0, 1)
    c.setLineWidth(0.25)
    corners = [
        (bleed, bleed),                        # unten links
        (page_w + bleed, bleed),               # unten rechts
        (bleed, page_h + bleed),               # oben links
        (page_w + bleed, page_h + bleed),      # oben rechts
    ]
    for (cx, cy) in corners:
        sign_x = 1 if cx < page_w / 2 + bleed else -1
        sign_y = 1 if cy < page_h / 2 + bleed else -1
        # Horizontale Marke
        x1 = cx + sign_x * offset
        x2 = cx + sign_x * (offset + length)
        c.line(x1, cy, x2, cy)
        # Vertikale Marke
        y1 = cy + sign_y * offset
        y2 = cy + sign_y * (offset + length)
        c.line(cx, y1, cx, y2)


def draw_registration_mark(c, cx, cy, r=3*mm):
    """Passermarke (Kreuz im Kreis)."""
    c.setStrokeColorCMYK(0, 0, 0, 1)
    c.setLineWidth(0.25)
    c.circle(cx, cy, r, stroke=1, fill=0)
    c.line(cx - r * 1.5, cy, cx + r * 1.5, cy)
    c.line(cx, cy - r * 1.5, cx, cy + r * 1.5)


def new_page(c, add_marks=True):
    """Neue Seite mit optionalen Schnittmarken."""
    c.showPage()
    if add_marks:
        draw_crop_marks(c, PAGE_W, PAGE_H, BLEED, MARK_OFFSET, MARK_LENGTH)
        # Passermarken mittig an allen 4 Seiten
        mid_x = PAGE_W / 2 + BLEED
        mid_y = PAGE_H / 2 + BLEED
        margin = BLEED / 2
        draw_registration_mark(c, mid_x, margin)
        draw_registration_mark(c, mid_x, PAGE_H + 2 * BLEED - margin)
        draw_registration_mark(c, margin, mid_y)
        draw_registration_mark(c, PAGE_W + 2 * BLEED - margin, mid_y)


def bg_rect(c, x, y, w, h, color):
    """Gefülltes Rechteck (Koordinaten relativ zum Endformat-Ursprung)."""
    c.setFillColor(color)
    c.rect(x + BLEED, y + BLEED, w, h, stroke=0, fill=1)


def draw_line(c, x1, y1, x2, y2, color=BRAND_ACCENT, width=0.5):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1 + BLEED, y1 + BLEED, x2 + BLEED, y2 + BLEED)


def text(c, x, y, txt, size=10, color=BRAND_DARK, font="Helvetica", align="left"):
    c.setFillColor(color)
    c.setFont(font, size)
    bx = x + BLEED
    by = y + BLEED
    if align == "center":
        c.drawCentredString(bx, by, txt)
    elif align == "right":
        c.drawRightString(bx, by, txt)
    else:
        c.drawString(bx, by, txt)


def multiline_text(c, x, y, lines, size=10, leading=14, color=BRAND_DARK,
                   font="Helvetica", max_width=None):
    """Einfacher Mehrzeilentext."""
    c.setFillColor(color)
    c.setFont(font, size)
    for i, line in enumerate(lines):
        by = y - i * leading + BLEED
        bx = x + BLEED
        if max_width:
            # Einfacher Zeilenumbruch
            words = line.split()
            current = ""
            row = 0
            for word in words:
                test = current + " " + word if current else word
                if c.stringWidth(test, font, size) <= max_width:
                    current = test
                else:
                    c.drawString(bx, by - row * leading, current)
                    current = word
                    row += 1
            if current:
                c.drawString(bx, by - row * leading, current)
        else:
            c.drawString(bx, by, line)


# ─── SEITEN ──────────────────────────────────────────────────────────────────

def page_cover(c):
    """Seite 1: Titel / Cover"""
    # Hintergrund bis Anschnitt
    c.setFillColor(BRAND_DARK)
    c.rect(0, 0, DOC_W, DOC_H, stroke=0, fill=1)

    # Dekoratives Rechteck oben rechts
    bg_rect(c, PAGE_W * 0.55, PAGE_H * 0.35, PAGE_W * 0.48, PAGE_H * 0.68, BRAND_ACCENT)

    # Diagonale Linie als Gestaltungselement
    draw_line(c, 0, PAGE_H * 0.35, PAGE_W * 0.65, PAGE_H, BRAND_WARM, 1.5)

    # Goldene Akzentlinie
    c.setStrokeColor(BRAND_WARM)
    c.setLineWidth(3)
    c.line(15*mm + BLEED, PAGE_H*0.18 + BLEED, 15*mm + BLEED, PAGE_H*0.52 + BLEED)

    # Firmenname
    text(c, 24, PAGE_H * 0.50, "DESIGN", 52, WHITE, "Helvetica-Bold")
    text(c, 24, PAGE_H * 0.50 - 18*mm, "MANUFAKTUR", 32, BRAND_WARM, "Helvetica-Bold")
    text(c, 24, PAGE_H * 0.50 - 26*mm, "GmbH", 32, WHITE, "Helvetica")

    # Claim
    text(c, 24, PAGE_H * 0.23, "Ideen. Konzepte. Ergebnisse.", 13, BRAND_LIGHT, "Helvetica-Oblique")

    # Ausgabejahr / Edition
    text(c, PAGE_W - 20, 12, "Firmenbroschüre 2026", 8, GRAY_MEDIUM, align="right")

    # Weißes Rechteck als "Fenster"
    bg_rect(c, 15*mm, PAGE_H * 0.60, PAGE_W * 0.38, PAGE_H * 0.30, BRAND_LIGHT)
    text(c, 20, PAGE_H * 0.86, "Über uns", 9, BRAND_ACCENT, "Helvetica-Bold")
    text(c, 20, PAGE_H * 0.82, "Leistungen", 9, BRAND_DARK)
    text(c, 20, PAGE_H * 0.79, "Referenzen", 9, BRAND_DARK)
    text(c, 20, PAGE_H * 0.76, "Kontakt", 9, BRAND_DARK)

    draw_crop_marks(c, PAGE_W, PAGE_H, BLEED, MARK_OFFSET, MARK_LENGTH)


def page_about(c):
    """Seite 2: Über uns"""
    new_page(c)
    # Hintergrund
    bg_rect(c, 0, 0, PAGE_W, PAGE_H, WHITE)
    # Kopfzeile Farbbalken
    bg_rect(c, 0, PAGE_H - 18*mm, PAGE_W, 21*mm, BRAND_ACCENT)
    text(c, 15, PAGE_H - 10, "ÜBER UNS", 14, WHITE, "Helvetica-Bold")

    # Seitenzahl
    text(c, PAGE_W - 15, 10, "2", 9, GRAY_MEDIUM, align="right")

    # Trennlinie
    draw_line(c, 15, PAGE_H - 22*mm, PAGE_W - 15, PAGE_H - 22*mm, BRAND_LIGHT, 0.5)

    # Einleitung Headline
    text(c, 15, PAGE_H - 35*mm, "Wer wir sind", 22, BRAND_DARK, "Helvetica-Bold")
    draw_line(c, 15, PAGE_H - 38*mm, 50*mm, PAGE_H - 38*mm, BRAND_WARM, 2)

    # Fließtext (simuliert)
    body_lines = [
        "Die Designmanufaktur GmbH steht seit über 15 Jahren für",
        "kreative Konzepte und nachhaltige Markenkommunikation.",
        "Unser interdisziplinäres Team aus Designern, Strategen",
        "und Textern entwickelt Lösungen, die begeistern und",
        "überzeugen — vom ersten Briefing bis zur finalen",
        "Umsetzung.",
        "",
        "Wir glauben daran, dass gutes Design mehr ist als",
        "Ästhetik. Es ist Kommunikation. Es ist Haltung.",
        "Es ist der Unterschied zwischen wahrgenommen werden",
        "und in Erinnerung bleiben.",
    ]
    multiline_text(c, 15, PAGE_H - 46*mm, body_lines, 10.5, 15, BRAND_DARK)

    # Zitat-Box
    bg_rect(c, 15, PAGE_H * 0.38, PAGE_W - 30*mm, 28*mm, BRAND_LIGHT)
    c.setStrokeColor(BRAND_ACCENT)
    c.setLineWidth(3)
    c.line(15*mm + BLEED, (PAGE_H * 0.38)*mm + BLEED,
           15*mm + BLEED, (PAGE_H * 0.38 + 28)*mm + BLEED)
    text(c, 22, PAGE_H * 0.38 + 22*mm,
         '"Design ist nicht, wie etwas aussieht --', 11, BRAND_ACCENT, "Helvetica-Oblique")
    text(c, 22, PAGE_H * 0.38 + 16*mm,
         'Design ist, wie etwas funktioniert."', 11, BRAND_ACCENT, "Helvetica-Oblique")
    text(c, 22, PAGE_H * 0.38 + 8*mm, "-- Steve Jobs", 9, GRAY_MEDIUM)

    # Statistiken
    stats = [("150+", "Projekte"), ("15", "Jahre"), ("3", "Standorte")]
    for i, (num, label) in enumerate(stats):
        sx = 15 + i * 62*mm
        bg_rect(c, sx, 20*mm, 55*mm, 35*mm, BRAND_DARK)
        text(c, sx + 8, 46*mm, num, 24, BRAND_WARM, "Helvetica-Bold")
        text(c, sx + 8, 36*mm, label, 9, WHITE)

    # Fußzeile
    bg_rect(c, 0, 0, PAGE_W, 14*mm, GRAY_LIGHT)
    text(c, 15, 5, "Designmanufaktur GmbH  ·  www.designmanufaktur.de", 8, GRAY_MEDIUM)


def page_services(c):
    """Seite 3: Leistungen"""
    new_page(c)
    bg_rect(c, 0, 0, PAGE_W, PAGE_H, WHITE)
    bg_rect(c, 0, PAGE_H - 18*mm, PAGE_W, 21*mm, BRAND_DARK)
    text(c, 15, PAGE_H - 10, "LEISTUNGEN", 14, WHITE, "Helvetica-Bold")
    text(c, PAGE_W - 15, 10, "3", 9, GRAY_MEDIUM, align="right")

    text(c, 15, PAGE_H - 34*mm, "Was wir für Sie tun", 22, BRAND_DARK, "Helvetica-Bold")
    draw_line(c, 15, PAGE_H - 37*mm, 55*mm, PAGE_H - 37*mm, BRAND_WARM, 2)

    # Leistungskarten 2×3 Raster
    services = [
        ("Branding",        "Markenentwicklung, Logo-\nDesign, Corporate Identity"),
        ("Print & Digital", "Broschüren, Kataloge,\nWebsite, Social Media"),
        ("Fotografie",      "Produkt-, People- und\nArchitekturfotografie"),
        ("Strategie",       "Marktanalyse, Positionierung,\nKommunikationskonzepte"),
        ("Messedesign",     "Standbau, Roll-ups,\nExponate und Leitsysteme"),
        ("Packaging",       "Verpackungsdesign, Etiketten,\nPoint of Sale"),
    ]

    cols, rows = 3, 2
    card_w = (PAGE_W - 20*mm) / cols - 3*mm
    card_h = 52*mm
    start_y = PAGE_H - 100*mm

    for i, (title, desc) in enumerate(services):
        col = i % cols
        row = i // cols
        cx = 10 + col * (card_w + 3*mm)
        cy = start_y - row * (card_h + 4*mm)

        bg_rect(c, cx, cy, card_w, card_h, BRAND_LIGHT)
        # Farbiger Streifen oben
        bg_rect(c, cx, cy + card_h - 8*mm, card_w, 8*mm, BRAND_ACCENT)
        text(c, cx + 4, cy + card_h - 3*mm, title.upper(), 8, WHITE, "Helvetica-Bold")
        # Beschreibung
        desc_lines = desc.split("\n")
        multiline_text(c, cx + 4, cy + card_h - 14*mm, desc_lines, 9, 13, BRAND_DARK)

    bg_rect(c, 0, 0, PAGE_W, 14*mm, GRAY_LIGHT)
    text(c, 15, 5, "Designmanufaktur GmbH  ·  www.designmanufaktur.de", 8, GRAY_MEDIUM)


def page_references(c):
    """Seite 4: Referenzen"""
    new_page(c)
    bg_rect(c, 0, 0, PAGE_W, PAGE_H, BRAND_DARK)
    # Accent-Fläche rechts
    bg_rect(c, PAGE_W * 0.60, 0, PAGE_W * 0.43, PAGE_H, BRAND_ACCENT)

    text(c, 15, PAGE_H - 22*mm, "REFERENZEN", 22, WHITE, "Helvetica-Bold")
    draw_line(c, 15, PAGE_H - 25*mm, 68*mm, PAGE_H - 25*mm, BRAND_WARM, 2)
    text(c, PAGE_W - 15, 10, "4", 9, GRAY_MEDIUM, align="right")

    text(c, 15, PAGE_H - 36*mm,
         "Auszug aus unseren Projekten", 11, GRAY_LIGHT, "Helvetica-Oblique")

    refs = [
        ("MusterAG", "Corporate Identity, Geschäftsausstattung"),
        ("Stadtwerke Nord", "Kampagne, Plakat, Digital"),
        ("Bioland GmbH", "Packaging, Katalog 2025"),
        ("Architektur+", "Broschüre, Messe, Website"),
        ("Hotel Bellevue", "Branding, Fotografie, Print"),
    ]
    for i, (client, project) in enumerate(refs):
        cy = PAGE_H - 52*mm - i * 22*mm
        draw_line(c, 15, cy + 12*mm, PAGE_W * 0.54, cy + 12*mm, GRAY_MEDIUM, 0.3)
        text(c, 15, cy + 5*mm, client, 12, WHITE, "Helvetica-Bold")
        text(c, 15, cy, project, 9, GRAY_LIGHT)

    # Rechte Spalte: Zitat
    text(c, PAGE_W * 0.65, PAGE_H * 0.70,
         '"Beste Zusammen-', 14, WHITE, "Helvetica-Oblique")
    text(c, PAGE_W * 0.65, PAGE_H * 0.70 - 6*mm,
         "arbeit, die wir je", 14, WHITE, "Helvetica-Oblique")
    text(c, PAGE_W * 0.65, PAGE_H * 0.70 - 12*mm,
         'hatten."', 14, WHITE, "Helvetica-Oblique")
    text(c, PAGE_W * 0.65, PAGE_H * 0.70 - 22*mm,
         "— Stadtwerke Nord", 9, BRAND_LIGHT)

    bg_rect(c, 0, 0, PAGE_W, 14*mm, CMYKColor(0, 0, 0, 0.98))
    text(c, 15, 5, "Designmanufaktur GmbH  ·  www.designmanufaktur.de", 8, GRAY_MEDIUM)


def page_contact(c):
    """Seite 5: Kontakt / Rückseite"""
    new_page(c)
    bg_rect(c, 0, 0, PAGE_W, PAGE_H, WHITE)
    bg_rect(c, 0, PAGE_H - 18*mm, PAGE_W, 21*mm, BRAND_WARM)
    text(c, 15, PAGE_H - 10, "KONTAKT", 14, WHITE, "Helvetica-Bold")
    text(c, PAGE_W - 15, 10, "5", 9, GRAY_MEDIUM, align="right")

    text(c, 15, PAGE_H - 34*mm, "So erreichen Sie uns", 22, BRAND_DARK, "Helvetica-Bold")
    draw_line(c, 15, PAGE_H - 37*mm, 62*mm, PAGE_H - 37*mm, BRAND_WARM, 2)

    # Kontaktblock Links
    contact_info = [
        ("Adresse", ["Musterstraße 12", "12345 Musterstadt"]),
        ("Telefon", ["+49 (0)123 456 789"]),
        ("E-Mail",  ["info@designmanufaktur.de"]),
        ("Web",     ["www.designmanufaktur.de"]),
    ]
    cy = PAGE_H - 52*mm
    for label, lines in contact_info:
        text(c, 15, cy, label.upper(), 8, BRAND_ACCENT, "Helvetica-Bold")
        for li, line in enumerate(lines):
            text(c, 15, cy - 6*mm - li * 5*mm, line, 10, BRAND_DARK)
        cy -= (len(lines) * 5 + 14) * mm

    # Karten-Platzhalter (grau)
    bg_rect(c, PAGE_W * 0.46, PAGE_H * 0.25, PAGE_W * 0.50, PAGE_H * 0.55, BRAND_LIGHT)
    text(c, PAGE_W * 0.46 + 5, PAGE_H * 0.25 + PAGE_H * 0.55 / 2,
         "[ Karte / Map ]", 11, GRAY_MEDIUM, align="left")

    # Öffnungszeiten
    bg_rect(c, 15, 20*mm, PAGE_W * 0.38, 28*mm, BRAND_LIGHT)
    text(c, 20, 44*mm, "Öffnungszeiten", 9, BRAND_ACCENT, "Helvetica-Bold")
    text(c, 20, 38*mm, "Mo – Fr   9:00 – 18:00 Uhr", 9, BRAND_DARK)
    text(c, 20, 33*mm, "Sa         10:00 – 14:00 Uhr", 9, BRAND_DARK)

    bg_rect(c, 0, 0, PAGE_W, 14*mm, GRAY_LIGHT)
    text(c, 15, 5, "Designmanufaktur GmbH  ·  www.designmanufaktur.de", 8, GRAY_MEDIUM)


# ─── HAUPT-FUNKTION ──────────────────────────────────────────────────────────

def build_brochure(filename="brochure_example.pdf"):
    c = canvas.Canvas(
        filename,
        pagesize=(DOC_W, DOC_H),
        pageCompression=0,        # unkomprimiert für Druckvorstufe
    )

    # PDF-Metadaten
    c.setTitle("Designmanufaktur GmbH – Firmenbroschüre 2026")
    c.setAuthor("Designmanufaktur GmbH")
    c.setSubject("Firmenbroschüre")
    c.setCreator("ReportLab / Claude Code")

    # Seite 1: Cover (erste Seite, noch kein showPage() davor)
    draw_crop_marks(c, PAGE_W, PAGE_H, BLEED, MARK_OFFSET, MARK_LENGTH)
    page_cover(c)

    # Seite 2–5
    page_about(c)
    page_services(c)
    page_references(c)
    page_contact(c)

    c.save()
    print(f"✓ PDF erstellt: {filename}")
    print(f"  Seiten: 5")
    print(f"  Dokumentgröße: {DOC_W/mm:.1f} × {DOC_H/mm:.1f} mm (inkl. {BLEED/mm:.0f}mm Anschnitt)")
    print(f"  Endformat: {PAGE_W/mm:.0f} × {PAGE_H/mm:.0f} mm (DIN A4)")
    print(f"  Farbraum: CMYK")
    print(f"  Schnittmarken: Ja")


if __name__ == "__main__":
    build_brochure()
