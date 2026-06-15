"""App de Gestão de Diagnósticos — orquestrador fino.

Cada seção é um módulo em frontend/paginas/. Este arquivo só monta o contexto,
desenha a navegação/filtros na sidebar e despacha para a página selecionada.
"""

import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path (backend/frontend importáveis).
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402
from PIL import Image  # noqa: E402

from frontend.servicos import carregar_contexto  # noqa: E402
from frontend.filtros import render_filtros  # noqa: E402
from frontend.paginas import (  # noqa: E402
    dashboard,
    diagnostico,
    gerenciar_projetos,
    gerenciar_clientes,
    gerenciar_produtos,
)

st.set_page_config(page_title="Gestão de Projetos", layout="wide", page_icon="📊")

# Mapa de navegação: rótulo -> função render(ctx) da página.
PAGINAS = {
    "🏠 Dashboard": dashboard.render,
    "🎙️ Diagnóstico": diagnostico.render,
    "📂 Gerenciar Projetos": gerenciar_projetos.render,
    "👤 Gerenciar Clientes": gerenciar_clientes.render,
    "💼 Gerenciar Produtos": gerenciar_produtos.render,
}

# --- Contexto (repos + dados) ---
ctx = carregar_contexto()

# --- Sidebar: imagem + navegação ---
try:
    st.sidebar.image(Image.open("foto_diogo.jpg"), caption="-------------------------------------")
except FileNotFoundError:
    st.sidebar.info("Imagem 'foto_diogo.jpg' não encontrada.")

st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Escolha uma seção:", list(PAGINAS.keys()))

# --- Filtros (sidebar) → df_filtrado no contexto ---
ctx.df_filtrado = render_filtros(ctx.df_projetos)

# --- Dispatch ---
PAGINAS[pagina](ctx)
