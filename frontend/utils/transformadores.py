"""Transformadores específicos do domínio do Diagnóstico.

Só mora aqui o que é específico do projeto (conhece os models SQLAlchemy).
Transformadores genéricos vêm do Baltazar:
- `colunas_por_delimitadores`  -> baltazar.funcoes_data_frames.transformacoes
- `dados_mapa_calor`, `lista_categorica_complexa`
      -> baltazar.graficos.graficos_streamlit.transformadores
"""

import datetime as dt

import pandas as pd


def criar_df_projetos(todos_projetos):

    if todos_projetos:
        projetos_data = []
        for p in todos_projetos:
            data_criacao = min([h.data_mudanca for h in p.historico_status]) if p.historico_status else None
            projetos_data.append({
                "id": p.id,
                "nome_projeto": p.nome_projeto,
                "tipo_projeto": p.tipo_projeto.value,
                "produto_projeto": p.produto.nome_produto,
                "status_projeto": p.status_projeto.value,
                "skills": ";".join(s.skill for s in p.skills) if p.skills else None,
                "Status_atual":[ x.status_novo.value for x in p.historico_status ],
                "Data_status_atual":[ pd.to_datetime(x.data_mudanca).tz_localize(None) for x in p.historico_status],
                "nivel_cliente": p.cliente.nivel_estatistico.value if p.cliente.nivel_estatistico else "N/A",
                "nome_cliente": p.cliente.nome,
                "Area_cliente": p.cliente.area.nome if p.cliente.area else None,
                "empresa_cliente":p.cliente.empresa,
                "emails_adicionais": ";".join(e.email for e in p.emails_adicionais) if p.emails_adicionais else None,
                "data_criacao": data_criacao,
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
        df_projetos = pd.DataFrame(projetos_data)
        if 'data_criacao' in df_projetos.columns:
            # data_mudanca é tz-aware (Brasília); converte para naive (wall-time)
            # para permitir comparação com os Timestamps naive dos filtros.
            df_projetos['data_criacao'] = pd.to_datetime(
                df_projetos['data_criacao'], utc=True
            ).dt.tz_convert('America/Sao_Paulo').dt.tz_localize(None)

    df_projetos['Data_status_atual'] = df_projetos.apply(lambda x: pd.Series(x['Data_status_atual']).max() if x['status_projeto'] == 'Projeto Finalizado' or x['status_projeto'] == 'CANCELADO'  else dt.datetime.today(), axis = 1)

    return df_projetos
