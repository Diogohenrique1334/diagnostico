"""Serviços compartilhados do app: runner async, repositories e contexto.

Centraliza o setup que antes vivia no topo do main.py, expondo um AppContext
que é passado para cada página (módulo em frontend/paginas/).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd
import streamlit as st

from backend.async_runner import AsyncRunner
from backend.repositories import (
    ClienteRepository,
    ProdutoRepository,
    ProjetoRepository,
    ValidacaoRepository,
)
from frontend.utils.transformadores import criar_df_projetos


# --- Recursos cacheados (criados uma vez e reusados entre reruns) ---
@st.cache_resource
def _get_runner() -> AsyncRunner:
    return AsyncRunner()


def run_async(coro):
    """Executa uma coroutine no event loop dedicado do AsyncRunner."""
    return _get_runner().run(coro)


@st.cache_resource
def _init_repos():
    return (
        ClienteRepository(),
        ProdutoRepository(),
        ProjetoRepository(),
        ValidacaoRepository(),
    )


@dataclass
class AppContext:
    """Estado compartilhado entre as páginas do app."""

    run_async: Callable
    cliente_repo: ClienteRepository
    produto_repo: ProdutoRepository
    projeto_repo: ProjetoRepository
    validacao_repo: ValidacaoRepository
    todos_projetos: list
    todos_clientes: list
    todos_produtos: list
    df_projetos: pd.DataFrame
    df_filtrado: pd.DataFrame | None = None


def carregar_contexto() -> AppContext:
    """Inicializa repositories, carrega os dados e monta o AppContext."""
    cliente_repo, produto_repo, projeto_repo, validacao_repo = _init_repos()

    todos_projetos = run_async(projeto_repo.get_all())
    todos_clientes = run_async(cliente_repo.get_all())
    todos_produtos = run_async(produto_repo.get_all())

    return AppContext(
        run_async=run_async,
        cliente_repo=cliente_repo,
        produto_repo=produto_repo,
        projeto_repo=projeto_repo,
        validacao_repo=validacao_repo,
        todos_projetos=todos_projetos,
        todos_clientes=todos_clientes,
        todos_produtos=todos_produtos,
        df_projetos=criar_df_projetos(todos_projetos),
    )
