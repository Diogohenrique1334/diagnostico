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
from frontend.utils import tema, auth  # noqa: E402
from frontend.paginas import (  # noqa: E402
    dashboard,
    diagnostico,
    gerenciar_projetos,
    gerenciar_clientes,
    gerenciar_produtos,
)

st.set_page_config(page_title="Gestão de Projetos", layout="wide", page_icon="📊")
tema.inject_css()  # tema escuro + cards + foto redonda (global em todas as páginas)

# Mapa de navegação: rótulo -> função render(ctx) da página.
PAGINAS = {
    "🏠 Dashboard": dashboard.render,
    "🎙️ Diagnóstico": diagnostico.render,
    "📂 Gerenciar Projetos": gerenciar_projetos.render,
    "👤 Gerenciar Clientes": gerenciar_clientes.render,
    "💼 Gerenciar Produtos": gerenciar_produtos.render,
}

# Páginas liberadas sem login. As demais (escrita + e-mails de clientes) pedem senha.
PAGINAS_PUBLICAS = {"🏠 Dashboard"}

# --- Contexto (repos + dados) ---
ctx = carregar_contexto()

# --- Sidebar: imagem + navegação ---
try:
    st.sidebar.image(Image.open("foto_diogo.jpg"))
except FileNotFoundError:
    st.sidebar.info("Imagem 'foto_diogo.jpg' não encontrada.")

st.sidebar.title("Navegação")
# Rótulo com 🔒 nas páginas protegidas (a chave de dispatch continua a original).
_rotulo = lambda p: p if p in PAGINAS_PUBLICAS or auth.esta_logado() else f"{p} 🔒"  # noqa: E731
pagina = st.sidebar.radio(
    "Escolha uma seção:", list(PAGINAS.keys()), format_func=_rotulo
)
auth.botao_logout()

# --- Gate de autenticação para páginas não-públicas ---
publico = pagina in PAGINAS_PUBLICAS
if not publico:
    auth.exigir_login()  # interrompe (st.stop) se não estiver logado

# --- Filtros (sidebar) → df_filtrado no contexto ---
# No modo público, esconde filtros sensíveis (Empresa, Projeto).
ctx.df_filtrado = render_filtros(ctx.df_projetos, publico=publico)

# --- Dispatch ---
PAGINAS[pagina](ctx)
