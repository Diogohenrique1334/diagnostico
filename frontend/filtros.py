"""Sidebar de filtros do Dashboard.

Renderiza os widgets de filtro e devolve o DataFrame já filtrado.
"""

import datetime as dt

import pandas as pd
import streamlit as st

from backend.models import SkillProjeto

# Mapeia cada status para uma dimensão simplificada (Ativo/Inativo).
STATUS_TRATADO = {
    "Levantamento de Requisitos": "Ativo",
    "Recebimento de Bases": "Ativo",
    "Análise exploratória da base de dados": "Ativo",
    "Construção da Pipeline": "Ativo",
    "Criação da Primeira Versão": "Ativo",
    "Ajustes no Projeto": "Ativo",
    "Criação da Documentação": "Ativo",
    "Ajustes Finos": "Ativo",
    "Cancelado": "Inativo",
    "Projeto Finalizado": "Inativo",
}


def render_filtros(df_projetos: pd.DataFrame, publico: bool = False) -> pd.DataFrame:
    """Desenha os filtros na sidebar e retorna o DataFrame filtrado.

    `publico=True` (Dashboard sem login) oculta os filtros que listam dados
    sensíveis em dropdown — Projeto e Empresa. O nome do Cliente permanece.
    """
    st.sidebar.title("Filtros do Dashboard")
    vazio = df_projetos.empty

    if publico:
        projetos_filtro: list = []
    else:
        projetos_filtro = st.sidebar.multiselect(
            "Projeto",
            options=sorted(df_projetos["nome_projeto"].unique()) if not vazio else [],
        )
    clientes_filtro = st.sidebar.multiselect(
        "Cliente",
        options=sorted(df_projetos["nome_cliente"].unique()) if not vazio else [],
    )
    if publico:
        empresa_clientes_filtro: list = []
    else:
        empresa_clientes_filtro = st.sidebar.multiselect(
            "Empresa",
            options=sorted(df_projetos["empresa_cliente"].unique()) if not vazio else [],
        )
    if publico:
        area_clientes_filtro: list = []
    else:   
        area_clientes_filtro = st.sidebar.multiselect(
            "Area do cliente",
            options=sorted(df_projetos["Area_cliente"].dropna().unique()) if not vazio else [],
        )
    status_filtro = st.sidebar.multiselect(
        "Status do Projeto",
        options=sorted(df_projetos["status_projeto"].map(STATUS_TRATADO).unique()) if not vazio else [],
    )
    etapa_filtro = st.sidebar.multiselect(
        "Etapa do Projeto",
        options=sorted(df_projetos["status_projeto"].unique()) if not vazio else [],
    )
    tipos_filtro = st.sidebar.multiselect(
        "Tipo de Projeto",
        options=sorted(df_projetos["tipo_projeto"].unique()) if not vazio else [],
    )
    skills_filtro = st.sidebar.multiselect(
        "Habilidades", options=sorted([s.value for s in SkillProjeto])
    )

    if not vazio and "data_criacao" in df_projetos.columns and not df_projetos["data_criacao"].isnull().all():
        min_date = df_projetos["data_criacao"].min().date()
        max_date = df_projetos["data_criacao"].max().date() + dt.timedelta(days=1)
        data_filtro = st.sidebar.date_input(
            "Período de Criação do Projeto",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
    else:
        data_filtro = st.sidebar.date_input(
            "Período de Criação do Projeto", value=(dt.date.today(), dt.date.today())
        )

    # --- Aplicação dos filtros ---
    df = df_projetos.copy()
    if projetos_filtro:
        df = df[df["nome_projeto"].isin(projetos_filtro)]
    if clientes_filtro:
        df = df[df["nome_cliente"].isin(clientes_filtro)]
    if empresa_clientes_filtro:
        df = df[df["empresa_cliente"].isin(empresa_clientes_filtro)]
    if area_clientes_filtro:
        df = df[df["Area_cliente"].isin(area_clientes_filtro)]
    if status_filtro:
        df = df[df["status_projeto"].map(STATUS_TRATADO).isin(status_filtro)]
    if etapa_filtro:
        df = df[df["status_projeto"].isin(etapa_filtro)]
    if tipos_filtro:
        df = df[df["tipo_projeto"].isin(tipos_filtro)]
    if skills_filtro:
        for skill in skills_filtro:
            df = df[df["skills"].str.contains(skill, na=False)]
    if data_filtro and len(data_filtro) == 2 and "data_criacao" in df.columns:
        start_date, end_date = pd.to_datetime(data_filtro[0]), pd.to_datetime(data_filtro[1])
        df = df[(df["data_criacao"] >= start_date) & (df["data_criacao"] <= end_date)]

    return df
