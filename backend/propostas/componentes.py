"""Componentes visuais compartilhados das propostas (ReportLab).

Fonte única de estilo dos 3 modelos de PDF: paleta verde de identidade,
estilos de parágrafo, flowables (seção com barra lateral, etapa numerada, box
de destaque, tabela de investimento) e o montador de documento com capa,
cabeçalho e rodapé. Os builders compõem o `flow` e chamam `gerar_documento`.
"""

from __future__ import annotations

import io
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# --- Paleta (azul-marinho + dourado sóbrio) ---
NAVY = colors.HexColor("#14304F")        # banda, headings, números
ACCENT = colors.HexColor("#C9A227")      # dourado: barras, linhas, anel da foto
ACCENT_DARK = NAVY                        # alias retrocompatível (headings/total)
INK = colors.HexColor("#1F2933")         # texto principal (ardósia)
MUTED = colors.HexColor("#5A6B7B")       # texto secundário
LIGHT_BG = colors.HexColor("#EFF2F6")    # fundo de boxes/cards
BORDER = colors.HexColor("#D5DCE4")      # bordas suaves
BAND_EYEBROW = colors.HexColor("#D9C68A")  # dourado claro (eyebrow na banda)
BAND_SUB = colors.HexColor("#C7D2DE")      # cinza-azulado (texto claro na banda)
WHITE = colors.white

# --- Geometria ---
PAGE_W, PAGE_H = A4
MARGIN_X = 2.3 * cm
MARGIN_B = 2.0 * cm
BAND_H = 4.8 * cm
HEADER_H = 1.4 * cm
LARGURA = PAGE_W - 2 * MARGIN_X


def build_styles() -> dict:
    """Estilos de parágrafo usados pelos componentes e builders."""
    base = getSampleStyleSheet()
    estilos = {
        "corpo": ParagraphStyle(
            "corpo", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10.5, leading=16, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "lead": ParagraphStyle(
            "lead", parent=base["BodyText"], fontName="Helvetica",
            fontSize=11.5, leading=17, textColor=MUTED, alignment=TA_JUSTIFY, spaceAfter=10,
        ),
        "secao": ParagraphStyle(
            "secao", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=13.5, leading=16, textColor=ACCENT_DARK, spaceBefore=0, spaceAfter=0,
        ),
        "subsecao": ParagraphStyle(
            "subsecao", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=10.5, leading=14, textColor=NAVY, spaceBefore=2, spaceAfter=2,
        ),
        "etapa_titulo": ParagraphStyle(
            "etapa_titulo", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=10.5, leading=13, textColor=INK,
        ),
        "etapa_desc": ParagraphStyle(
            "etapa_desc", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10, leading=14, textColor=MUTED,
        ),
        "badge": ParagraphStyle(
            "badge", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=13, leading=15, textColor=WHITE, alignment=TA_CENTER,
        ),
        "meta_label": ParagraphStyle(
            "meta_label", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=9, leading=12, textColor=MUTED,
        ),
        "meta_valor": ParagraphStyle(
            "meta_valor", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10, leading=13, textColor=INK,
        ),
        "total": ParagraphStyle(
            "total", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=12, leading=15, textColor=ACCENT_DARK,
        ),
        "kpi_valor": ParagraphStyle(
            "kpi_valor", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=15, leading=18, textColor=ACCENT_DARK, alignment=TA_CENTER,
        ),
        "kpi_rotulo": ParagraphStyle(
            "kpi_rotulo", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=7.5, leading=10, textColor=MUTED, alignment=TA_CENTER,
        ),
    }
    return estilos


# --------------------------------------------------------------------------- #
# Flowables
# --------------------------------------------------------------------------- #
def secao(titulo: str, estilos: dict) -> Table:
    """Cabeçalho de seção com barra lateral colorida."""
    barra = 0.14 * cm  # ~4px, padrão de heading do Diogo
    tabela = Table(
        [["", Paragraph(titulo, estilos["secao"])]],
        colWidths=[barra, LARGURA - barra],
    )
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return tabela


def etapa(numero: int, titulo: str, descricao: str, estilos: dict) -> Table:
    """Linha do fluxo de trabalho: badge numerado + título e descrição."""
    conteudo = [
        Paragraph(titulo, estilos["etapa_titulo"]),
        Paragraph(descricao, estilos["etapa_desc"]),
    ]
    tabela = Table(
        [[Paragraph(str(numero), estilos["badge"]), conteudo]],
        colWidths=[0.95 * cm, LARGURA - 0.95 * cm],
    )
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), ACCENT),
        ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
        ("VALIGN", (1, 0), (1, 0), "TOP"),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
    ]))
    return tabela


def destaque(paragrafos: list) -> Table:
    """Box de destaque: fundo claro + barra lateral de acento."""
    tabela = Table([[paragrafos]], colWidths=[LARGURA])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return tabela


def tabela_meta(linhas: list[tuple[str, str]], estilos: dict) -> Table:
    """Caixa com pares rótulo/valor (Cliente, Projeto, Data, Validade...)."""
    dados = [
        [Paragraph(lbl.upper(), estilos["meta_label"]), Paragraph(val, estilos["meta_valor"])]
        for lbl, val in linhas
    ]
    tabela = Table(dados, colWidths=[3.2 * cm, LARGURA - 3.2 * cm])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tabela


def tabela_investimento(linhas: list[tuple[str, str]], total_label: str,
                        total_valor: str, estilos: dict) -> Table:
    """Tabela de investimento com linha de total destacada."""
    corpo = estilos["meta_valor"]
    dados = [[Paragraph(desc, corpo), Paragraph(val, corpo)] for desc, val in linhas]
    dados.append([Paragraph(total_label, estilos["total"]),
                  Paragraph(total_valor, estilos["total"])])
    tabela = Table(dados, colWidths=[LARGURA - 5 * cm, 5 * cm])
    n = len(dados) - 1
    tabela.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBELOW", (0, 0), (-1, n - 1), 0.4, BORDER),
        ("BACKGROUND", (0, n), (-1, n), LIGHT_BG),
        ("LINEABOVE", (0, n), (-1, n), 1, ACCENT),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return tabela


def bullets(itens: list[str], estilos: dict) -> list:
    """Lista de bullets como parágrafos (para escopo/entregáveis)."""
    return [
        Paragraph(f"•&nbsp;&nbsp;{item}", estilos["corpo"]) for item in itens
    ]


def faixa_kpis(items: list[tuple[str, str]], estilos: dict) -> Table:
    """Linha de KPIs em boxes estilizados (valor grande + rótulo).

    `items`: lista de (valor, rótulo). Cada box tem fundo claro, borda e uma
    linha de acento no topo — padrão visual de KPI do Diogo.
    """
    gap = 0.3 * cm
    n = len(items)
    box_w = (LARGURA - (n - 1) * gap) / n

    linha, col_widths, style = [], [], [("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    ci = 0
    for i, (valor, rotulo) in enumerate(items):
        linha.append([Paragraph(valor, estilos["kpi_valor"]),
                      Paragraph(rotulo.upper(), estilos["kpi_rotulo"])])
        col_widths.append(box_w)
        style += [
            ("BACKGROUND", (ci, 0), (ci, 0), LIGHT_BG),
            ("BOX", (ci, 0), (ci, 0), 0.5, BORDER),
            ("LINEABOVE", (ci, 0), (ci, 0), 2, ACCENT),
            ("TOPPADDING", (ci, 0), (ci, 0), 9),
            ("BOTTOMPADDING", (ci, 0), (ci, 0), 9),
        ]
        ci += 1
        if i < n - 1:
            linha.append("")
            col_widths.append(gap)
            ci += 1

    tabela = Table([linha], colWidths=col_widths)
    tabela.setStyle(TableStyle(style))
    return tabela


def subsecao(titulo: str, estilos: dict) -> Paragraph:
    """Mini-título de subseção (ex.: 'Premissas', 'Não incluso')."""
    return Paragraph(titulo, estilos["subsecao"])


def premissas_exclusoes(premissas: list[str], exclusoes: list[str], estilos: dict):
    """Seção 'Premissas e Exclusões' com dois grupos de bullets (mantida junta)."""
    from reportlab.platypus import KeepTogether  # import local: evita ciclo no topo
    bloco = [secao("Premissas e Exclusões", estilos), Spacer(1, 8),
             subsecao("Premissas", estilos)]
    bloco += bullets(premissas, estilos)
    bloco += [Spacer(1, 6), subsecao("Não incluso", estilos)]
    bloco += bullets(exclusoes, estilos)
    return KeepTogether(bloco)


def _assinatura_img(path: str, max_w: float):
    """Imagem de assinatura redimensionada (altura ~1.1cm), ou '' se inválida."""
    try:
        iw, ih = ImageReader(path).getSize()
    except Exception:
        return ""
    h = 1.1 * cm
    w = iw * (h / ih)
    if w > max_w:
        w = max_w
        h = ih * (w / iw)
    img = Image(path, width=w, height=h)
    img.hAlign = "CENTER"
    return img


def bloco_aceite(estilos: dict, profissional: str, cargo: str,
                 assinatura_path: str | None = None) -> Table:
    """Área de aceite: duas colunas com linha de assinatura e rótulos.

    Se `assinatura_path` existir, desenha a assinatura acima da linha do prestador.
    """
    col = (LARGURA - 1.2 * cm) / 2
    rot = ParagraphStyle("aceite_rot", parent=estilos["etapa_desc"], alignment=TA_CENTER)

    assinatura = ""
    if assinatura_path and os.path.exists(assinatura_path):
        assinatura = _assinatura_img(assinatura_path, col - 12)

    assinada = assinatura != ""
    dados = [
        ["", "", assinatura],
        [Paragraph("Contratante<br/>Data: ___/___/______", rot), "",
         Paragraph(f"{profissional}<br/>{cargo}", rot)],
    ]
    tabela = Table(dados, colWidths=[col, 1.2 * cm, col])
    tabela.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (0, 0), 0.7, INK),
        ("LINEBELOW", (2, 0), (2, 0), 0.7, INK),
        # Com assinatura, a imagem provê a altura; sem, deixa espaço p/ assinar à mão.
        ("TOPPADDING", (0, 0), (-1, 0), 12 if assinada else 40),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
        ("TOPPADDING", (0, 1), (-1, 1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 0),
        ("VALIGN", (0, 0), (-1, 0), "BOTTOM"),
        ("VALIGN", (0, 1), (-1, 1), "TOP"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
    ]))
    return tabela


# --------------------------------------------------------------------------- #
# Montagem do documento (capa + cabeçalho + rodapé)
# --------------------------------------------------------------------------- #
def _foto_circular(canvas, path: str, cx: float, cy: float, r: float) -> None:
    """Desenha a imagem `path` recortada num círculo de raio r centrado em (cx, cy)."""
    try:
        img = ImageReader(path)
        iw, ih = img.getSize()
    except Exception:
        return
    canvas.saveState()
    p = canvas.beginPath()
    p.circle(cx, cy, r)
    canvas.clipPath(p, stroke=0, fill=0)
    lado = 2 * r
    escala = max(lado / iw, lado / ih)  # cover: preenche o círculo, corta o excesso
    w, h = iw * escala, ih * escala
    canvas.drawImage(img, cx - w / 2, cy - h / 2, width=w, height=h, mask="auto")
    canvas.restoreState()
    canvas.setStrokeColor(WHITE)
    canvas.setLineWidth(1.5)
    canvas.circle(cx, cy, r, stroke=1, fill=0)


def _wrap_linhas(canvas, texto: str, font: str, size: float, max_w: float) -> list[str]:
    """Quebra `texto` em linhas que cabem em `max_w` na fonte/tamanho dados."""
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if canvas.stringWidth(teste, font, size) <= max_w or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def gerar_documento(flow: list, *, eyebrow: str, titulo: str,
                    profissional: str, cargo: str, contato: str, titulo_pdf: str,
                    foto_path: str | None = None, numero: str | None = None) -> bytes:
    """Monta o PDF na memória e devolve os bytes.

    Capa: bloco pessoal à esquerda (foto + nome + cargo) e título-herói à
    direita. `titulo` costuma ser o nome do projeto; `eyebrow` é o tipo de doc.
    """
    def _capa(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, PAGE_H - BAND_H, PAGE_W, BAND_H, stroke=0, fill=1)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, PAGE_H - BAND_H, PAGE_W, 0.16 * cm, stroke=0, fill=1)

        # --- Bloco pessoal à esquerda: foto + nome + cargo ---
        r = 0.95 * cm
        cx = MARGIN_X + r
        cy_foto = PAGE_H - 1.55 * cm
        x_texto = MARGIN_X
        if foto_path:
            _foto_circular(canvas, foto_path, cx, cy_foto, r)
            y_nome = cy_foto - r - 0.55 * cm
        else:
            y_nome = PAGE_H - 1.7 * cm
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(x_texto, y_nome, profissional)
        canvas.setFillColor(BAND_SUB)
        canvas.setFont("Helvetica", 8.5)
        canvas.drawString(x_texto, y_nome - 0.42 * cm, cargo)

        # --- Título-herói à direita ---
        x_tit = MARGIN_X + 4.3 * cm
        max_w = PAGE_W - MARGIN_X - x_tit
        canvas.setFillColor(BAND_EYEBROW)
        canvas.setFont("Helvetica-Bold", 8.5)
        canvas.drawString(x_tit, PAGE_H - 1.5 * cm, eyebrow.upper())

        size = 20
        linhas = _wrap_linhas(canvas, titulo, "Helvetica-Bold", size, max_w)
        if len(linhas) > 2:
            size = 15
            linhas = _wrap_linhas(canvas, titulo, "Helvetica-Bold", size, max_w)
        linhas = linhas[:3]
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", size)
        lh = size * 1.18
        # Centraliza o bloco de título na área entre o eyebrow e a base da banda.
        area_top = PAGE_H - 2.2 * cm
        area_bot = PAGE_H - BAND_H + 0.5 * cm
        centro = (area_top + area_bot) / 2
        y = centro + (lh * len(linhas)) / 2 - size * 0.8
        for ln in linhas:
            canvas.drawString(x_tit, y, ln)
            y -= lh

        if numero:
            canvas.setFillColor(BAND_SUB)
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - BAND_H + 0.45 * cm, numero)

        _rodape(canvas, doc)
        canvas.restoreState()

    def _interna(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica-Bold", 8.5)
        esq = eyebrow.upper() + (f"  ·  {numero}" if numero else "")
        canvas.drawString(MARGIN_X, PAGE_H - 1.25 * cm, esq)
        canvas.setFont("Helvetica", 8.5)
        canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 1.25 * cm, profissional)
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN_X, PAGE_H - 1.45 * cm, PAGE_W - MARGIN_X, PAGE_H - 1.45 * cm)
        _rodape(canvas, doc)
        canvas.restoreState()

    def _rodape(canvas, doc):
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN_X, MARGIN_B - 0.45 * cm, PAGE_W - MARGIN_X, MARGIN_B - 0.45 * cm)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(MARGIN_X, MARGIN_B - 0.85 * cm, contato)
        canvas.drawRightString(PAGE_W - MARGIN_X, MARGIN_B - 0.85 * cm, f"Página {doc.page}")

    buffer = io.BytesIO()
    doc = BaseDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_B, bottomMargin=MARGIN_B,
        title=titulo_pdf, author=profissional,
    )
    frame_capa = Frame(
        MARGIN_X, MARGIN_B, LARGURA, PAGE_H - BAND_H - 0.8 * cm - MARGIN_B,
        id="capa", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    frame_int = Frame(
        MARGIN_X, MARGIN_B, LARGURA, PAGE_H - HEADER_H - MARGIN_B - 0.4 * cm,
        id="interna", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates([
        PageTemplate(id="Capa", frames=[frame_capa], onPage=_capa),
        PageTemplate(id="Interna", frames=[frame_int], onPage=_interna),
    ])
    doc.build([NextPageTemplate("Interna")] + flow)
    return buffer.getvalue()
