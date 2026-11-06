#!/usr/bin/env python3
"""Genera REGOLAMENTO.pdf (formato federale) a partire da REGOLAMENTO.md.

Requisiti: pandoc, google-chrome (>= 131, per i margin box @page), pdftotext.
Uso: python3 tools/build-pdf.py
"""
import html
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "REGOLAMENTO.md"
OUT = ROOT / "REGOLAMENTO.pdf"
LOGO = ROOT / "assets" / "logo-delegazione-trapani.jpeg"

ENTE = "Delegazione Provinciale di Trapani"
TITOLO = "Regolamento tecnico della manifestazione Formula 6"
FOOTER = "Regolamento Formula 6 – Delegazione Provinciale di Trapani"
REVISIONI = [("00", "Delegazione Provinciale di Trapani", "06/11/2026")]

# ---------------------------------------------------------------- moduli
def righe(n, celle):
    return "".join(
        "<tr><td class='c'>%d</td>%s</tr>" % (i, "<td></td>" * celle) for i in range(1, n + 1)
    )

MODULO_C = f"""
<div class="modulo">
<p class="mod-titolo">TORNEO FORMULA 6 – Modulo di iscrizione e lista</p>
<table class="campi">
<tr><td>Torneo</td><td class="riga"></td><td>Data</td><td class="riga"></td></tr>
<tr><td>Squadra (nome)</td><td class="riga" colspan="3"></td></tr>
<tr><td>Circolo / Associazione / Scuola</td><td class="riga" colspan="3"></td></tr>
<tr><td>Squadra mista</td><td colspan="3">&#9744; sì &nbsp;&nbsp; &#9744; no</td></tr>
<tr><td>Responsabile (nome, e-mail, telefono)</td><td class="riga" colspan="3"></td></tr>
<tr><td>Capitano</td><td class="riga"></td><td>Accompagnatore dei minori</td><td class="riga"></td></tr>
</table>
<table class="griglia">
<thead><tr><th>N°</th><th style="width:30%">Cognome e nome</th><th>Data di nascita</th><th>Sesso</th>
<th>ID FSI / FIDE</th><th>Elo</th><th>F</th><th>U18</th><th>U12</th></tr></thead>
<tbody>{righe(10, 8)}</tbody>
</table>
<p>&#9744; La lista contiene almeno una giocatrice (F), un Under 18 e un Under 12 (art. 3.5).<br>
&#9744; Per ogni minorenne è stato raccolto il consenso di chi esercita la responsabilità genitoriale (art. 12.2).</p>
<p class="nota">Il numero d'ordine stabilisce l'ordine di forza sulle scacchiere libere (art. 6.4).</p>
<table class="firme"><tr>
<td>Luogo e data<br><br>______________________________</td>
<td>Firma del responsabile<br><br>______________________________</td>
</tr></table>
</div>
"""

MODULO_D = """
<div class="modulo">
<p class="mod-titolo">TORNEO FORMULA 6 – Modulo di formazione</p>
<table class="campi">
<tr><td>Turno</td><td class="riga"></td><td>Incontro</td><td class="riga"></td></tr>
<tr><td>Squadra</td><td class="riga" colspan="3"></td></tr>
</table>
<table class="griglia">
<thead><tr><th>Scacchiera</th><th>Categoria</th><th>N° lista</th><th style="width:50%">Cognome e nome</th></tr></thead>
<tbody>
<tr><td class="c">1ª</td><td>Femminile</td><td></td><td></td></tr>
<tr><td class="c">2ª</td><td>Under 18</td><td></td><td></td></tr>
<tr><td class="c">3ª</td><td>Under 12</td><td></td><td></td></tr>
<tr><td class="c">4ª</td><td>Libera</td><td></td><td></td></tr>
<tr><td class="c">5ª</td><td>Libera</td><td></td><td></td></tr>
<tr><td class="c">6ª</td><td>Libera</td><td></td><td></td></tr>
</tbody></table>
<p class="nota">Sulle scacchiere 4ª, 5ª e 6ª i numeri di lista devono essere in ordine crescente (art. 6.4).</p>
<table class="firme"><tr>
<td>Ora di consegna<br><br>______________________________</td>
<td>Firma del capitano<br><br>______________________________</td>
</tr></table>
</div>
"""

def riga_e(sc, cat, ca, cb):
    return f"<tr><td class='c'>{sc}</td><td class='c'>{cat}</td><td class='c'>{ca}</td><td></td><td></td><td></td><td></td><td class='c'>{cb}</td></tr>"

MODULO_E = f"""
<div class="modulo">
<p class="mod-titolo">TORNEO FORMULA 6 – Modulo di fine incontro</p>
<table class="campi">
<tr><td>Torneo</td><td class="riga" colspan="3"></td></tr>
<tr><td>Turno</td><td class="riga"></td><td>Data</td><td class="riga"></td></tr>
</table>
<table class="campi">
<tr><td class="riga c" style="width:45%"></td><td class="c">vs</td><td class="riga c" style="width:45%"></td></tr>
<tr><td class="c nota">(squadra A – prima nominata)</td><td></td><td class="c nota">(squadra B)</td></tr>
</table>
<table class="griglia">
<thead><tr><th>Sc.</th><th>Cat.</th><th>Col. A</th><th style="width:28%">Giocatore A</th><th>Ris. A</th>
<th>Ris. B</th><th style="width:28%">Giocatore B</th><th>Col. B</th></tr></thead>
<tbody>
{riga_e(1, "F", "B", "N")}{riga_e(2, "U18", "N", "B")}{riga_e(3, "U12", "B", "N")}
{riga_e(4, "L", "N", "B")}{riga_e(5, "L", "B", "N")}{riga_e(6, "L", "N", "B")}
<tr><td colspan="4" class="r"><b>Totale punti individuali</b></td><td></td><td></td><td colspan="2"></td></tr>
<tr><td colspan="4" class="r"><b>Punti squadra</b></td><td></td><td></td><td colspan="2"></td></tr>
</tbody></table>
<p>Si attesta che i giocatori schierati sono in regola con quanto previsto dal regolamento della manifestazione.</p>
<p>Contestazioni: &nbsp; &#9744; No &nbsp;&nbsp; &#9744; Sì (allegare i motivi del reclamo)</p>
<table class="firme"><tr>
<td>Il Capitano A (stampatello e firma)<br><br>__________________________</td>
<td>Il Capitano B (stampatello e firma)<br><br>__________________________</td>
</tr><tr>
<td colspan="2" class="c"><br>L'Arbitro<br><br>__________________________</td>
</tr></table>
</div>
"""

# ---------------------------------------------------------------- markdown
src = MD.read_text(encoding="utf-8")
body_md = src[src.index("## 1 Oggetto"):]
blocks = iter([MODULO_C, MODULO_D, MODULO_E])
body_md = re.sub(r"```\n.*?```", lambda m: next(blocks), body_md, flags=re.S)
body_md = re.sub(r"^---\s*$", "", body_md, flags=re.M)
body_md = body_md.replace("# Allegati", '<h1 class="allegati">Allegati</h1>', 1)

body_html = subprocess.run(
    ["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none"], input=body_md, capture_output=True,
    text=True, check=True,
).stdout
# Elenchi "a) b) c)": niente pallino davanti alla lettera
body_html = re.sub(r"<li>([a-z]\)) ", r'<li class="nob">\1 ', body_html)
# Ogni allegato su una nuova pagina
body_html = body_html.replace('<h2 id="allegato-', '<h2 class="nuova" id="allegato-')

# Voci del sommario: (testo, id)
voci = re.findall(r'<h2[^>]*id="([^"]+)"[^>]*>(.*?)</h2>', body_html)
voci = [(i, re.sub("<[^>]+>", "", t)) for i, t in voci]


def sommario(pagine):
    out = []
    for ident, testo in voci:
        num = pagine.get(ident, "")
        out.append(
            f'<div class="voce"><a href="#{ident}"><span class="t">{html.escape(html.unescape(testo))}</span>'
            f'<span class="dots"></span><span class="n">{num}</span></a></div>'
        )
    return "\n".join(out)


CSS = f"""
@page {{
  size: A4; margin: 22mm 22mm 24mm 22mm;
  @top-left {{ content: "{ENTE} – Scacchi"; font: 8.5pt Carlito, Calibri, sans-serif; color:#1f3a6b;
    vertical-align: bottom; padding-bottom: 3mm; border-bottom: .5pt solid #1f3a6b; }}
  @top-right {{ content: "Formula 6"; font: italic 8.5pt Carlito, Calibri, sans-serif; color:#1f3a6b;
    vertical-align: bottom; padding-bottom: 3mm; border-bottom: .5pt solid #1f3a6b; }}
  @top-center {{ content: ""; border-bottom: .5pt solid #1f3a6b; }}
  @bottom-center {{ content: ""; border-top: .5pt solid #000; }}
  @bottom-left {{ content: "{FOOTER}"; font: 9pt 'Liberation Serif', Tinos, 'Times New Roman', serif;
    vertical-align: top; padding-top: 2mm; border-top: .5pt solid #000; }}
  @bottom-right {{ content: "Pagina " counter(page) " di " counter(pages);
    font: 9pt 'Liberation Serif', Tinos, 'Times New Roman', serif; vertical-align: top; padding-top: 2mm;
    border-top: .5pt solid #000; }}
}}
@page copertina {{ margin: 20mm;
  @top-left {{ content: none; border: 0 }} @top-right {{ content: none; border: 0 }}
  @bottom-left {{ content: none; border: 0 }} @top-center {{ content: none; border: 0 }}
  @bottom-center {{ content: none; border: 0 }} @bottom-right {{ content: none; border: 0 }} }}
html {{ font-family: 'Liberation Serif', Tinos, 'Times New Roman', serif; font-size: 11pt; line-height: 1.28; color:#000; }}
body {{ margin: 0; }}
.copertina {{ page: copertina; height: 257mm; position: relative; text-align: center; break-after: page; }}
.copertina img {{ width: 62mm; margin-top: 8mm; }}
.copertina .ente {{ font: bold 13pt Carlito, Calibri, sans-serif; color:#1f3a6b; letter-spacing:.5pt; margin-top: 4mm; }}
.copertina h1 {{ font-size: 17pt; margin-top: 52mm; margin-bottom: 3mm; }}
.copertina .sotto {{ font-size: 12pt; }}
.copertina .motto {{ font-style: italic; margin-top: 6mm; }}
.copertina table.rev {{ position: absolute; bottom: 22mm; left: 50%; transform: translateX(-50%); width: 140mm;
  border-collapse: collapse; font: 10pt Carlito, Calibri, sans-serif; }}
table.rev th, table.rev td {{ border: .75pt solid #000; padding: 1pt 4pt; text-align:center; font-weight: normal; }}
.sommario {{ break-after: page; }}
.sommario h2 {{ font-size: 12pt; }}
.voce a {{ display:flex; color:#000; text-decoration:none; margin: 3pt 0; }}
.voce .dots {{ flex:1; border-bottom: 1pt dotted #000; margin: 0 3pt 3pt; }}
.intest {{ text-align:center; margin-bottom: 8mm; padding-top: 3mm; }}
.intest img {{ width: 22mm; }}
.intest p {{ margin: 1pt 0; font-size: 12pt; text-align: center; }}
h2 {{ font-size: 11.5pt; font-weight: bold; margin: 14pt 0 6pt; break-after: avoid; }}
h3 {{ font-size: 11pt; margin: 10pt 0 4pt; }}
h1.allegati {{ break-before: page; text-align:center; font-size: 14pt; }}
h2.nuova {{ break-before: page; }}
h1.allegati + h2.nuova {{ break-before: auto; }}
p, li {{ text-align: justify; hyphens: auto; }}
p {{ margin: 0 0 6pt; }}
ul, ol {{ margin: 0 0 6pt; padding-left: 7mm; }}
li {{ margin: 1pt 0; }}
blockquote {{ margin: 4pt 8mm; font-style: italic; }}
a {{ color: inherit; text-decoration: none; }}
table {{ border-collapse: collapse; margin: 4pt 0 8pt; }}
table th, table td {{ border: .75pt solid #000; padding: 2pt 5pt; vertical-align: top; font-size: 10pt; }}
table th {{ background: #e8edf5; font-weight: bold; }}
table, tr {{ break-inside: avoid; }}
.modulo {{ border: 1pt solid #000; padding: 6mm; }}
.mod-titolo {{ text-align:center; font-weight:bold; font-size: 12pt; margin-bottom: 6mm; }}
.modulo table {{ width: 100%; }}
table.campi td, table.firme td {{ border: 0; font-size: 10.5pt; padding: 4pt 4pt; }}
table.campi td.riga {{ border-bottom: .75pt solid #000; }}
table.griglia td {{ height: 17pt; }}
table.firme td {{ text-align: center; padding-top: 8mm; }}
.c {{ text-align:center; }} .r {{ text-align:right; }}
.nota {{ font-size: 9.5pt; font-style: italic; }}
ul.task-list, ul:has(> li > input[type=checkbox]) {{ list-style: none; padding-left: 2mm; }}
li.nob {{ list-style: none; margin-left: -4mm; }}
input[type=checkbox] {{ margin-right: 4pt; }}
"""

logo_uri = LOGO.as_uri()


def documento(pagine):
    rev = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in REVISIONI)
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<title>{TITOLO}</title><style>{CSS}</style></head><body>
<section class="copertina">
  <img src="{logo_uri}" alt="Logo {ENTE}">
  <div class="ente">{ENTE.upper()} – SCACCHI</div>
  <h1>Regolamento tecnico della manifestazione<br>FORMULA 6</h1>
  <div class="sotto">Scacchi a squadre misti e intergenerazionali</div>
  <div class="motto">Sei scacchiere. Più generazioni. Una squadra.</div>
  <table class="rev"><thead><tr><th># revisione</th><th colspan="2">Approvazione</th></tr></thead>
  <tbody>{rev}</tbody></table>
</section>
<section class="sommario"><h2>Sommario</h2>{sommario(pagine)}</section>
<section class="testo">
  <div class="intest"><img src="{logo_uri}" alt="">
    <p>{ENTE} – Scacchi</p>
    <p>Formula 6 – Scacchi a squadre misti e intergenerazionali</p>
    <p><b>Regolamento tecnico della manifestazione</b></p></div>
  {body_html}
</section></body></html>"""


def stampa(html_text, pdf):
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=ROOT, delete=False, encoding="utf-8") as f:
        f.write(html_text)
        tmp = Path(f.name)
    try:
        subprocess.run(
            ["google-chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             "--allow-file-access-from-files", f"--print-to-pdf={pdf}", tmp.as_uri()],
            check=True, capture_output=True,
        )
    finally:
        tmp.unlink()


def numeri_pagina(pdf):
    """Trova la pagina in cui compare ciascun titolo (dalla 3ª in poi)."""
    testo = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True,
                           check=True).stdout
    pagine = testo.split("\f")
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    risultato = {}
    for ident, titolo in voci:
        t = norm(html.unescape(titolo))
        for n, p in enumerate(pagine[2:], start=3):
            if t in norm(p):
                risultato[ident] = n
                break
    return risultato


# Due passaggi: il primo serve a calcolare i numeri di pagina del sommario.
stampa(documento({}), OUT)
stampa(documento(numeri_pagina(OUT)), OUT)
print(f"Creato {OUT}")
