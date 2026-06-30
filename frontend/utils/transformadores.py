"""Transformadores específicos do domínio do Diagnóstico.

Só mora aqui o que é específico do projeto (conhece os models SQLAlchemy).
Transformadores genéricos vêm do Baltazar:
- `colunas_por_delimitadores`  -> baltazar.funcoes_data_frames.transformacoes
- `dados_mapa_calor`, `lista_categorica_complexa`
      -> baltazar.graficos.graficos_streamlit.transformadores
"""

import pandas as pd

_FUSO = "America/Sao_Paulo"
# Status que encerram o projeto: a janela ativa termina na data dessa mudança,
# não em "hoje". OBS: usar o .value EXATO do enum (era 'CANCELADO', que nunca
# casava com o valor real 'Cancelado' — projetos cancelados viravam falso-ativos).
_STATUS_INATIVOS = {"Projeto Finalizado", "Cancelado"}


def _para_naive_brasilia(ts) -> pd.Timestamp:
    """Converte um timestamp (possivelmente tz-aware) para naive em horário de
    parede de Brasília, para comparar com os Timestamps naive dos filtros."""
    t = pd.Timestamp(ts)
    if t.tz is not None:
        t = t.tz_convert(_FUSO).tz_localize(None)
    return t


def _data_inicio_projeto(p) -> pd.Timestamp:
    """Início efetivo do projeto.

    Prioriza `data_inicio` (informada manualmente, ex.: cadastro retroativo);
    na ausência dela, usa a 1ª mudança de status registrada.
    """
    if getattr(p, "data_inicio", None):
        return pd.Timestamp(p.data_inicio)
    if p.historico_status:
        return _para_naive_brasilia(min(h.data_mudanca for h in p.historico_status))
    return pd.NaT


def _data_fim_projeto(p) -> pd.Timestamp:
    """Fim efetivo da janela ativa.

    Se o projeto já encerrou (finalizado/cancelado), é a data da última mudança
    de status. Caso contrário, o projeto ainda está ativo → "hoje".
    """
    if p.status_projeto.value in _STATUS_INATIVOS and p.historico_status:
        return _para_naive_brasilia(max(h.data_mudanca for h in p.historico_status))
    return pd.Timestamp.today().normalize()


def criar_df_projetos(todos_projetos):
    if not todos_projetos:
        return pd.DataFrame()

    linhas = []
    for p in todos_projetos:
        linhas.append({
            "id": p.id,
            "nome_projeto": p.nome_projeto,
            "tipo_projeto": p.tipo_projeto.value,
            "produto_projeto": p.produto.nome_produto,
            "status_projeto": p.status_projeto.value,
            "skills": ";".join(s.skill for s in p.skills) if p.skills else None,
            "Status_atual": [x.status_novo.value for x in p.historico_status],
            "nivel_cliente": p.cliente.nivel_estatistico.value if p.cliente.nivel_estatistico else "N/A",
            "nome_cliente": p.cliente.nome,
            "Area_cliente": p.cliente.area.nome if p.cliente.area else None,
            "empresa_cliente": p.cliente.empresa,
            "emails_adicionais": ";".join(e.email for e in p.emails_adicionais) if p.emails_adicionais else None,
            "data_criacao": _data_inicio_projeto(p),
            "Data_status_atual": _data_fim_projeto(p),
            "objetivo": p.objetivo,
            "desempenho_atual": p.desempenho_atual,
            "metrica_avaliacao": p.metrica_avaliacao,
            "como_melhorar_desempenho": p.como_melhorar_desempenho,
            "o_que_prejudica_objetivo": p.o_que_prejudica_objetivo,
            "como_e_cobrado": p.como_e_cobrado,
            "valor_baseline": p.valor_baseline,
            "meta_desejada": p.meta_desejada,
            "prazo_desejado": p.prazo_desejado,
        })

    df_projetos = pd.DataFrame(linhas)
    df_projetos["data_criacao"] = pd.to_datetime(df_projetos["data_criacao"])
    df_projetos["Data_status_atual"] = pd.to_datetime(df_projetos["Data_status_atual"])
    return df_projetos
