"""Tema visual do dashboard do Diagnóstico (verde/escuro).

Mesma linguagem dos cards do portfólio e do BDC (fundo escuro, cards com borda,
headings com barra lateral, KPI boxes, hover com elevação), na identidade verde
`#18990b`. Só CSS + helpers de markup — os gráficos continuam vindo do Baltazar.
"""

from __future__ import annotations

import streamlit as st

COR = "#18990b"          # verde de identidade (portfólio)
COR_CLARO = "#37C72B"    # verde claro p/ destaques
COR_DESTAQUE = COR

_CSS = """
<style>
/* ===== DASHBOARD DIAGNÓSTICO ===== */
.block-container { max-width: 1280px; padding-top: 2.6rem; }

/* Hero */
.dg-hero {
    display: flex; align-items: center; gap: 14px;
    border-bottom: 2px solid rgba(24,153,11,0.30);
    padding: 2px 4px 14px 4px; margin-bottom: 14px;
}
.dg-hero .ico { font-size: 2.0rem; line-height: 1; }
.dg-hero .txt { font-size: 1.85rem; font-weight: 800; color: #f0f0f0; line-height: 1.2; }
.dg-hero .txt span { color: #18990b; }
.dg-hero .sub { color: #8b8b9e; font-size: 0.95rem; font-weight: 500; margin-top: 2px; }

/* Heading de seção (barra lateral verde) */
.dg-sec {
    font-size: 1.12rem; font-weight: 700; color: #f0f0f0;
    padding-left: 12px; border-left: 4px solid #18990b;
    margin: 18px 0 12px; line-height: 1.3;
}

/* Linha de KPIs */
.dg-kpi-row {
    display: grid; gap: 12px; margin: 4px 0 8px;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
}
.dg-kpi {
    background: #161B22; border: 1px solid #2a2f3a; border-radius: 12px;
    padding: 16px 14px; text-align: center; transition: all 0.2s ease;
}
.dg-kpi:hover {
    border-color: #18990b; transform: translateY(-3px);
    box-shadow: 0 10px 26px rgba(24,153,11,0.14);
}
.dg-kpi .val { font-size: 1.7rem; font-weight: 800; color: #f0f0f0; line-height: 1; }
.dg-kpi .lbl { color: #8b8b9e; font-size: 0.72rem; margin-top: 7px;
               font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }
.dg-kpi .sub { color: #37C72B; font-size: 0.74rem; margin-top: 4px; font-weight: 600; }
.dg-kpi.destaque .val { color: #37C72B; }

/* Título de cada gráfico/card */
.dg-card-title { font-size: 0.95rem; font-weight: 700; color: #e2e2e8; margin: 2px 0; }
.dg-card-sub { color: #6b6b7e; font-size: 0.78rem; margin-bottom: 2px; }

/* Foto de perfil redonda na sidebar (como no portfólio) */
[data-testid="stSidebar"] [data-testid="stImage"] { text-align: center; }
[data-testid="stSidebar"] [data-testid="stImage"] img {
    width: 150px !important; height: 150px !important;
    border-radius: 50%; object-fit: cover;
    border: 3px solid #18990b; box-shadow: 0 6px 18px rgba(0,0,0,0.35);
    margin: 0 auto; display: block;
}
[data-testid="stSidebar"] [data-testid="stImageCaption"] { display: none; }

/* Containers com borda viram cards escuros */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #161B22; border-radius: 12px;
}

footer { visibility: hidden; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(titulo: str, subtitulo: str = "", icone: str = "📊") -> None:
    sub = f'<div class="sub">{subtitulo}</div>' if subtitulo else ""
    st.markdown(
        f'<div class="dg-hero"><span class="ico">{icone}</span>'
        f'<div><span class="txt"><span>{titulo}</span></span>{sub}</div></div>',
        unsafe_allow_html=True,
    )


def secao(texto: str) -> None:
    st.markdown(f'<div class="dg-sec">{texto}</div>', unsafe_allow_html=True)


def card_titulo(titulo: str, sub: str = "") -> None:
    html = f'<div class="dg-card-title">{titulo}</div>'
    if sub:
        html += f'<div class="dg-card-sub">{sub}</div>'
    st.markdown(html, unsafe_allow_html=True)


def kpis(itens, destaque: int = -1) -> None:
    """Linha de KPIs estilizados.

    `itens`: lista de (label, valor) ou (label, valor, sub). `destaque`: índice
    a pintar de verde (ex.: taxa de conclusão). -1 = nenhum.
    """
    blocos = []
    for i, item in enumerate(itens):
        lbl, val = item[0], item[1]
        sub = item[2] if len(item) > 2 else ""
        classe = "dg-kpi destaque" if i == destaque else "dg-kpi"
        sub_html = f'<div class="sub">{sub}</div>' if sub else ""
        blocos.append(
            f'<div class="{classe}"><div class="val">{val}</div>'
            f'<div class="lbl">{lbl}</div>{sub_html}</div>'
        )
    st.markdown(f'<div class="dg-kpi-row">{"".join(blocos)}</div>',
                unsafe_allow_html=True)
