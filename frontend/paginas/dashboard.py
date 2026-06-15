"""Página: Dashboard de Projetos."""

import pandas as pd
import streamlit as st

from backend.models import StatusProjeto
from frontend.servicos import AppContext
from frontend.utils.transformadores import (
    Serie_tempo_relativo,
    df_para_lista_dict,
    dados_grafico_barras,
    colunas_por_delimitadores,
    dados_mapa_calor,
)
from frontend.utils.graficos import grafico_rosca, barras_empilhadas_horizontais
from baltazar.ML.supervisionado.series_temporais.transformacoes_temporais import (
    contagem_ativos_por_dia,
)
from baltazar.graficos.graficos_streamlit.graficos import (
    grefico_calendario,
    mapa_palavras,
    funil,
    velocimetro,
    mapa_calor,
)

_INATIVOS = ["Projeto Finalizado", "CANCELADO"]


def _delta_mes(n: int):
    """Delta absoluto e honesto para totais que só crescem: '+N este mês'."""
    return f"+{n} este mês" if n and n > 0 else None


def _metricas(df_projetos: pd.DataFrame, df_filtrado: pd.DataFrame) -> None:
    base = df_filtrado
    hoje = pd.Timestamp.today()

    def _do_mes_corrente(serie_datas) -> int:
        if serie_datas.empty:
            return 0
        return int(((serie_datas.dt.year == hoje.year) & (serie_datas.dt.month == hoje.month)).sum())

    total = len(base)
    finalizados = base[base["status_projeto"] == "Projeto Finalizado"]
    concluidos = len(finalizados)
    abertos = int((~base["status_projeto"].isin(_INATIVOS)).sum())
    taxa = (concluidos / total * 100) if total else 0
    clientes = base["nome_cliente"].nunique()

    # Tempo médio de entrega (cycle time): do início à finalização, em dias.
    tempo_medio = None
    if not finalizados.empty:
        ciclos = (finalizados["Data_status_atual"] - finalizados["data_criacao"]).dt.days
        ciclos = ciclos[ciclos >= 0]
        tempo_medio = int(round(ciclos.mean())) if not ciclos.empty else None

    # Novidades do mês corrente (deltas absolutos honestos).
    novos_proj = _do_mes_corrente(base["data_criacao"])
    concl_mes = _do_mes_corrente(finalizados["Data_status_atual"])
    proj_mes = base[(base["data_criacao"].dt.year == hoje.year) & (base["data_criacao"].dt.month == hoje.month)]
    novos_clientes = proj_mes["nome_cliente"].nunique()

    spark_proj = Serie_tempo_relativo(base, "data_criacao", valores="nome_projeto", _agg="count").nome_projeto.tolist()
    spark_concl = (
        Serie_tempo_relativo(finalizados, "data_criacao", valores="nome_projeto", epocas=6, _agg="count").nome_projeto.tolist()
        if not finalizados.empty else []
    )

    # --- Linha 1: KPIs de impacto ---
    r1 = st.columns(3)
    with r1[0]:
        st.metric("Total de Projetos", f"{total:,}", delta=_delta_mes(novos_proj),
                  border=True, chart_data=spark_proj, chart_type="area")
    with r1[1]:
        st.metric("Taxa de Conclusão", f"{taxa:.0f}%",
                  delta=f"{concluidos} de {total}", delta_color="off", border=True)
    with r1[2]:
        st.metric(
            "Tempo Médio de Entrega",
            f"{tempo_medio} dias" if tempo_medio is not None else "—",
            delta=f"{concluidos} entregues", delta_color="off", border=True,
            help="Dias médios do início do projeto até a finalização (cycle time).",
        )

    # --- Linha 2: volumes ---
    r2 = st.columns(3)
    with r2[0]:
        st.metric("Projetos Concluídos", f"{concluidos:,}", delta=_delta_mes(concl_mes),
                  border=True, chart_data=spark_concl, chart_type="area")
    with r2[1]:
        st.metric("Projetos Abertos", f"{abertos:,}", delta=None, delta_color="off", border=True)
    with r2[2]:
        st.metric("Clientes Atendidos", f"{clientes:,}", delta=_delta_mes(novos_clientes), border=True)


def _graficos_principais(df_filtrado: pd.DataFrame) -> None:

    #with st.container(border=True, height=550):
    #    col_graf1, col_graf2 = st.columns([3, 6])
    #    with col_graf1.container(border=True, height=520):
    #        mask = ~df_filtrado["status_projeto"].isin(_INATIVOS)
    #        grafico_rosca(df_para_lista_dict(df_filtrado[mask], "status_projeto", "id", _agg="count"))
    #    with col_graf2.container(border=True, height=520):
    #        st.subheader("Projetos por Tipo")
    #        barras_empilhadas_horizontais(
    #           *dados_grafico_barras(df_filtrado, "tipo_projeto", "id", "status_projeto", _agg="count"),
    #            tamanho="400px",
    #        )

    with st.container(border=True):
        st.subheader("Habilidades por Tipo de Projeto (% dos projetos do tipo)")
        skills_exp = colunas_por_delimitadores(df_filtrado, "skills", ";")
        if not skills_exp.empty:
            # Heatmap: X = tipo de projeto, Y = skill (top 15).
            # cor/valor = % dos projetos daquele tipo que usaram a skill.
            dados, eixo_x, eixo_y = dados_mapa_calor(
                skills_exp, "tipo_projeto", "value", "id", _agg="count", top_y=15, percentual=True
            )
            mapa_calor(dados, eixo_x, eixo_y, sufixo="%")
        else:
            st.info("Sem habilidades registradas nos projetos filtrados.")

    with st.container(border=True, height=500):
        st.subheader("Tarefas em andamento por data")
        df_tarefas = contagem_ativos_por_dia(
            df_filtrado, "data_criacao", "Data_status_atual"
        ).rename(columns={"data": "Data", "ativos": "value"})
        grefico_calendario(df_tarefas, anos=[2025, 2026], tamanho="450px")


def _analises_adicionais(df_filtrado: pd.DataFrame) -> None:
    with st.container(border=True, height=510):
        st.subheader("Análises de projetos")
        g1, g2 = st.columns([2, 3])

        with g1.container(border=True, height=420):
            st.markdown("**Taxa de Conclusão de projetos**")
            total_proj = len(df_filtrado)
            concluidos = int(df_filtrado["status_projeto"].eq("Projeto Finalizado").sum())
            taxa_pct = round((concluidos / total_proj) * 100, 1) if total_proj else 0.0
            velocimetro(taxa_pct, titulo="Concluídos", tamanho="350px")

        with g2.container(border=True, height=420):
            st.markdown("**Funil do Pipeline (projetos ativos)**")
            ordem_status = [s.value for s in StatusProjeto if s.value not in _INATIVOS]
            ativos = df_filtrado[~df_filtrado["status_projeto"].isin(_INATIVOS)]
            contagem_status = ativos["status_projeto"].value_counts()
            funil_data = [
                {"value": int(contagem_status.get(s, 0)), "name": s}
                for s in ordem_status if contagem_status.get(s, 0) > 0
            ]
            if funil_data:
                funil(funil_data, tamanho="350px")
            else:
                st.info("Sem projetos ativos para exibir o funil.")

        with st.container(border=True, height=420):
            st.subheader("Projetos por Tipo")
            barras_empilhadas_horizontais(
                *dados_grafico_barras(df_filtrado, "tipo_projeto", "id", "status_projeto", _agg="count"),
                tamanho="350px",
            )

        with st.container(border=True, height=420):

                st.subheader("☁️ Nuvem de Habilidades")
                skills_exp = colunas_por_delimitadores(df_filtrado, "skills", ";")
                contagem_skills = skills_exp["value"].value_counts() if not skills_exp.empty else pd.Series(dtype=int)
                nuvem = [
                    {"name": k, "value": int(v)}
                    for k, v in contagem_skills.items()
                    if k and str(k).strip() and str(k) != "None"
                ]
                if nuvem:
                    mapa_palavras(nuvem)
                else:
                    st.info("Sem habilidades registradas nos projetos filtrados.")


def render(ctx: AppContext) -> None:
    st.title("📊 Dashboard de Projetos")
    st.markdown("Visão geral dos projetos")

    df_projetos, df_filtrado = ctx.df_projetos, ctx.df_filtrado

    if df_filtrado.empty and not df_projetos.empty:
        st.warning("Nenhum projeto encontrado com os filtros atuais. Altere os filtros na barra lateral para visualizar os dados.")
        return
    if df_projetos.empty:
        st.info("Nenhum projeto cadastrado ainda. Comece pela seção 'Diagnóstico'.")
        return

    _metricas(df_projetos, df_filtrado)
    _analises_adicionais(df_filtrado)
    _graficos_principais(df_filtrado)
    
