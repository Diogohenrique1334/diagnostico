"""Página: Dashboard de Projetos (tema escuro + cards, identidade verde)."""

import pandas as pd
import streamlit as st

from backend.models import StatusProjeto
from frontend.servicos import AppContext
from frontend.utils import tema
from baltazar.funcoes_data_frames.transformacoes import colunas_por_delimitadores
from baltazar.graficos.graficos_streamlit.transformadores import (
    dados_mapa_calor,
    lista_categorica_complexa,
)
from baltazar.ML.supervisionado.series_temporais.transformacoes_temporais import (
    contagem_ativos_por_dia,
)
from baltazar.graficos.graficos_streamlit.graficos import (
    grefico_calendario,
    mapa_palavras,
    funil,
    velocimetro,
    mapa_calor,
    barras_empilhadas_horizontais,
)

_INATIVOS = ["Projeto Finalizado", "CANCELADO"]
_CORES_VERDE = ["#0E5E07", "#18990b", "#37C72B", "#7BD66F"]   # gradiente p/ funil
_ESCALA_VERDE = ["#15311b", "#18990b"]                        # heatmap
_ESCALA_VERMELHA = ["#E23B2E", "#3a1a1a"]                     # calendário (oscilação)


def _calcular_kpis(base: pd.DataFrame) -> dict:
    hoje = pd.Timestamp.today()

    def _do_mes(serie) -> int:
        if serie.empty:
            return 0
        return int(((serie.dt.year == hoje.year) & (serie.dt.month == hoje.month)).sum())

    total = len(base)
    finalizados = base[base["status_projeto"] == "Projeto Finalizado"]
    concluidos = len(finalizados)
    abertos = int((~base["status_projeto"].isin(_INATIVOS)).sum())
    taxa = (concluidos / total * 100) if total else 0
    clientes = base["nome_cliente"].nunique()

    tempo_medio = None
    if not finalizados.empty:
        ciclos = (finalizados["Data_status_atual"] - finalizados["data_criacao"]).dt.days
        ciclos = ciclos[ciclos >= 0]
        tempo_medio = int(round(ciclos.mean())) if not ciclos.empty else None

    novos_proj = _do_mes(base["data_criacao"])
    concl_mes = _do_mes(finalizados["data_criacao"])

    return {
        "total": total, "concluidos": concluidos, "abertos": abertos,
        "taxa": taxa, "clientes": clientes, "tempo_medio": tempo_medio,
        "novos_proj": novos_proj, "concl_mes": concl_mes,
    }


def _kpis(base: pd.DataFrame) -> None:
    k = _calcular_kpis(base)
    mes = lambda n: f"+{n} este mês" if n and n > 0 else ""  # noqa: E731
    tempo = f"{k['tempo_medio']} dias" if k["tempo_medio"] is not None else "—"
    tema.kpis(
        [
            ("Total de Projetos", f"{k['total']:,}", mes(k["novos_proj"])),
            ("Taxa de Conclusão", f"{k['taxa']:.0f}%", f"{k['concluidos']} de {k['total']}"),
            ("Tempo Médio de Entrega", tempo, "cycle time"),
            ("Projetos Concluídos", f"{k['concluidos']:,}", mes(k["concl_mes"])),
            ("Projetos Abertos", f"{k['abertos']:,}", ""),
            ("Clientes Atendidos", f"{k['clientes']:,}", ""),
        ],
        destaque=1,
    )


def _pipeline(df: pd.DataFrame) -> None:
    tema.secao("Pipeline & Conclusão")
    c1, c2 = st.columns([2, 3])

    with c1.container(border=True, height=400):
        tema.card_titulo("Taxa de conclusão")
        total = len(df)
        concluidos = int(df["status_projeto"].eq("Projeto Finalizado").sum())
        taxa = round((concluidos / total) * 100, 1) if total else 0.0
        velocimetro(taxa, titulo="Concluídos", cor=tema.COR, tamanho="300px")

    with c2.container(border=True, height=400):
        tema.card_titulo("Funil do pipeline", "projetos ativos por etapa")
        ordem = [s.value for s in StatusProjeto if s.value not in _INATIVOS]
        ativos = df[~df["status_projeto"].isin(_INATIVOS)]
        cont = ativos["status_projeto"].value_counts()
        dados = [{"value": int(cont.get(s, 0)), "name": s} for s in ordem if cont.get(s, 0) > 0]
        if dados:
            funil(dados, cores=_CORES_VERDE, tamanho="300px")
        else:
            st.info("Sem projetos ativos para exibir o funil.")


def _distribuicao(df: pd.DataFrame) -> None:
    tema.secao("Distribuição")
    c1, c2 = st.columns(2)

    with c1.container(border=True, height=450):
        tema.card_titulo("Projetos feitos por tipo de projeto", "empilhado por status de projeto")
        barras_empilhadas_horizontais(
            *lista_categorica_complexa(df, "tipo_projeto", "id", "status_projeto", _agg="count"),
            tamanho="360px",
        )

    with c2.container(border=True, height=450):
        tema.card_titulo("Nuvem de habilidades", "frequência de uso das habilidades")
        skills = colunas_por_delimitadores(df, "skills", ";")
        cont = skills["value"].value_counts() if not skills.empty else pd.Series(dtype=int)
        nuvem = [{"name": k, "value": int(v)} for k, v in cont.items()
                 if k and str(k).strip() and str(k) != "None"]
        if nuvem:
            mapa_palavras(nuvem)
        else:
            st.info("Sem habilidades registradas nos projetos filtrados.")


def _habilidades_tempo(df: pd.DataFrame) -> None:
    tema.secao("Habilidades por Tipo de Projeto")
    with st.container(border=True):
        tema.card_titulo("Mapa de calor", "% das skills usadas por tipo de projeto ")
        skills = colunas_por_delimitadores(df, "skills", ";")
        if not skills.empty:
            dados, eixo_x, eixo_y = dados_mapa_calor(
                skills, "tipo_projeto", "value", "id", _agg="count", top_y=15, percentual=True
            )
            mapa_calor(dados, eixo_x, eixo_y, cores=_ESCALA_VERDE, sufixo="%")
        else:
            st.info("Sem habilidades registradas nos projetos filtrados.")

    tema.secao("Atividade ao Longo do Tempo")
    with st.container(border=True):
        tema.card_titulo("Tarefas em andamento por dia")
        df_tarefas = contagem_ativos_por_dia(
            df, "data_criacao", "Data_status_atual"
        ).rename(columns={"data": "Data", "ativos": "value"})
        grefico_calendario(df_tarefas, anos=[2025, 2026], cores=_ESCALA_VERMELHA, tamanho="450px")


def render(ctx: AppContext) -> None:
    tema.hero("Gerenciador de projetos", "Painel de gestão de projetos de dados", icone="📊")

    df_projetos, df_filtrado = ctx.df_projetos, ctx.df_filtrado

    if df_projetos.empty:
        st.info("Nenhum projeto cadastrado ainda. Comece pela seção 'Diagnóstico'.")
        return
    if df_filtrado.empty:
        st.warning("Nenhum projeto encontrado com os filtros atuais. "
                   "Altere os filtros na barra lateral para visualizar os dados.")
        return

    _kpis(df_filtrado)
    _pipeline(df_filtrado)
    _distribuicao(df_filtrado)
    _habilidades_tempo(df_filtrado)
