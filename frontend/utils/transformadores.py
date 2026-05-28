import pandas as pd
import numpy as np
import datetime as dt


def Crar_df_projetos(todos_projetos):

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
                "skills": p.skills,
                "Status_atual":[ x.status_novo.value for x in p.historico_status ],
                "Data_status_atual":[ pd.to_datetime(x.data_mudanca) for x in p.historico_status],
                "nivel_cliente": p.cliente.nivel_estatistico.value if p.cliente.nivel_estatistico else "N/A",
                "nome_cliente": p.cliente.nome,
                "Area_cliente":p.cliente.area,
                "empresa_cliente":p.cliente.empresa,
                "emails_adicionais": p.emails_adicionais,
                "data_criacao": data_criacao,
                "objetivo": p.objetivo,
                "desempenho_atual": p.desempenho_atual,
                "metrica_avaliacao": p.metrica_avaliacao,
                "como_melhorar_desempenho": p.como_melhorar_desempenho,
                "o_que_prejudica_objetivo": p.o_que_prejudica_objetivo,
                "como_e_cobrado": p.como_e_cobrado
            })
        df_projetos = pd.DataFrame(projetos_data)
        if 'data_criacao' in df_projetos.columns:
            df_projetos['data_criacao'] = pd.to_datetime(df_projetos['data_criacao'])

    df_projetos['Data_status_atual'] = df_projetos.apply(lambda x: pd.Series(x['Data_status_atual']).max() if x['status_projeto'] == 'Projeto Finalizado' or x['status_projeto'] == 'CANCELADO'  else dt.datetime.today(), axis = 1)
    
    return df_projetos

def colunas_por_delimitadores(df,coluna,delimitador):
    
        novas_colunas = df[coluna].map(lambda x: str(x).split(delimitador)).apply(pd.Series)

        df_novo = pd.merge(df,novas_colunas, left_index=True, right_index=True)

        df_novo_expandido = pd.melt(df_novo, id_vars = [x for x in df_novo.columns if not isinstance(x, int)]).reset_index(drop='index')
        
        return df_novo_expandido.dropna(axis=0, how='any')

def df_para_lista_dict(df_filtrado,categoria = 'categoria', somatorio = 'amount', controle = "name", _agg = 'sum'):

    dados = df_filtrado.groupby(categoria)[somatorio].agg(_agg).sort_values(ascending = False).reset_index()

    return [{"value": y, controle: x} for x,y in dados.values ]

def df_para_lista(df_filtrado, categoria = 'categoria', somatorio = 'amount', _agg = ['sum','count'] ):

    dados = df_filtrado.groupby(categoria)[somatorio].agg(_agg).reset_index().rename(columns = {categoria:'product','sum':'amount','count':'score'})[['score','amount','product']]

    mylist = dados.values.tolist()

    mylist.sort(key=lambda x: x[1])

    mylist.reverse()

    mylist.append(list(dados))

    mylist.reverse()

    return mylist

def Serie_simples(df_filtrado, col_data, col_values):

    serie_gastos = df_filtrado.pivot_table(index=col_data,
                        values = col_values,
                        aggfunc = 'sum')
    
    return serie_gastos.reset_index().rename(columns = {"date":'Data', 'amount':'value'})

def serei_dia_semana(df,col_data,valores,colunas,agg):

    serie_gastos = df.pivot_table(index=colunas,
                        values = valores,
                        columns = df[col_data].dt.dayofweek,
                        aggfunc = agg)
    
    eixo = [ x for x in serie_gastos.columns.map({0:'Domingo',1:'Segunda',2:'Terça',3:'Quarta',4:'Quinta',5:'Sexta',6:'Sábado',7:'Domingo'})]

    categorias = [ x for x in serie_gastos.index]

    valores_series = serie_gastos.values.tolist()
    
    return valores_series, categorias, eixo

def serei_dia_semana_complexo(df,col_data,valores,colunas,agg):

    def config_data(lista_valores,categorias):

        add_dic = list()
        for x in range(len(lista_valores)):
            
            add_dic.append( {
            "name": categorias[x],
            "type": "bar",
            "stack": "total",
            "label": {"show": True},
            "emphasis": {"focus": "series"},
            "data": [ int(l) for l in lista_valores[x] ],
            })

        return add_dic

    serie_gastos = df.pivot_table(index=colunas,
                        values = valores,
                        columns = df[col_data].dt.dayofweek,
                        aggfunc = agg)
    
    eixo = [ x for x in serie_gastos.columns.map({6:'Domingo',0:'Segunda',1:'Terça',2:'Quarta',3:'Quinta',4:'Sexta',5:'Sábado'})]
    #eixo = [ x for x in serie_gastos.columns]

    categorias = [ x for x in serie_gastos.index]

    valores_series = serie_gastos.values.tolist()

    return config_data(valores_series,categorias), categorias, eixo

def serei_semana_mes_complexo_2(df, col_data, valores, colunas, agg):

    def config_data(lista_valores, categorias):
        add_dic = []
        for x in range(len(lista_valores)):
            add_dic.append({
                "name": categorias[x],
                "type": "bar",
                "stack": "total",
                "label": {"show": True},
                "emphasis": {"focus": "series"},
                "data": [int(l) for l in lista_valores[x]],
            })
        return add_dic

    # Calcula a semana do mês (1ª semana, 2ª semana, etc.)
    semanas_mes = ((df[col_data].dt.day - 1) // 7) + 1

    serie_gastos = df.pivot_table(
        index=colunas,
        values=valores,
        columns=semanas_mes,
        aggfunc=agg
    )

    # Nomeando os eixos como "Semana 1", "Semana 2", etc.
    eixo = [f"Semana {x}" for x in serie_gastos.columns]

    categorias = [x for x in serie_gastos.index]
    valores_series = serie_gastos.values.tolist()

    return config_data(valores_series, categorias), categorias, eixo

def dados_grafico_barras(df, coluna, valores, colunas, _agg):

    def config_data(lista_valores, categorias):
        add_dic = []
        for x in range(len(lista_valores)):
            add_dic.append({
                "name": categorias[x],
                "type": "bar",
                "stack": "total",
                "label": {"show": False},
                "emphasis": {"focus": "series"},
                "data": [int(l) for l in lista_valores[x]],
            })
        return add_dic

    # Calcula a semana do mês (1ª semana, 2ª semana, etc.)
    #semanas_mes = ((df[col_data].dt.day - 1) // 7) + 1

    serie_gastos = df.pivot_table(
        index=colunas,
        values=valores,
        columns=coluna,
        aggfunc=_agg
    ).fillna(0)

    serie_gastos = serie_gastos[serie_gastos.sum().sort_values(ascending = False).index]

    # Nomeando os eixos como "Semana 1", "Semana 2", etc.
    eixo = [x for x in serie_gastos.columns]

    categorias = [x for x in serie_gastos.index]
    valores_series = serie_gastos.values.tolist()

    return config_data(valores_series, categorias), categorias, eixo

def dias_sem_gastos(df_filtrado):

    dias_mês =  pd.DataFrame({"mês":df_filtrado.date.dt.strftime('%Y%m'),"Dias do mês":df_filtrado.date.dt.daysinmonth}).drop_duplicates().set_index('mês').to_dict()['Dias do mês']

    dias_com_gastos = df_filtrado.pivot_table(index = df_filtrado.date.dt.strftime('%Y%m'),
                        values = 'date',
                        aggfunc = lambda x: len(x.unique())).rename(columns = {"date":"dias com gastos"}).reset_index()
    
    dias_com_gastos['Dias do mês'] = dias_com_gastos.date.map(dias_mês)

    dias_com_gastos['dias_sem_gastar'] = dias_com_gastos['Dias do mês'] - dias_com_gastos['dias com gastos']

    gastos_utilizacoes = df_filtrado.groupby(df_filtrado.date.dt.strftime('%Y%m'))['amount'].agg(['sum','count'])

    return dias_com_gastos.merge(gastos_utilizacoes, left_on = 'date', right_index = True, how = 'left')

def top_10_categorias(df_filtrado):

    categorias = [ x for x in df_filtrado.groupby('categoria')['amount'].sum().sort_values(ascending = False).reset_index().categoria ] 

    op = dict()

    for a in categorias:

        t = df_filtrado[df_filtrado.categoria == a].pivot_table(index = 'descricao',
                                                                values = 'amount',
                                                                aggfunc = 'sum').sort_values(by = 'amount', ascending = False).head(15).reset_index()
        
        t = t.values.tolist()

        op.update({a:t})

    return op,categorias,df_para_lista_dict(df_filtrado,controle='groupId')

def get_delta(curr, prev, is_pct=False):
    if prev is None or prev == 0:
        return None
    if is_pct:
        return f"{curr - prev:+.1f}%"
    return f"{(curr - prev) / prev * 100:+.1f}%"

def dados_grafico_cachoeira(df_filtrado):

    gastos_mes = df_filtrado.groupby(df_filtrado["date"].dt.strftime('%Y%m'))['amount'].sum()

    aumento = [ '-' if x < 0 else int(x) for x in gastos_mes.diff().fillna(gastos_mes[0]) ]

    queda = [ '-' if x < 0 else int(x) for x in (gastos_mes.diff() * -1).fillna(-1) ]

    valores = [int(x) for x in gastos_mes.values ]

    categorias = [ x for x in gastos_mes.index ]

    return categorias, valores, aumento, queda

def Serie_tempo_relativo(df: pd.DataFrame,
                        coluna_data: str,
                        valores:str, 
                        epocas: int = 6, 
                        _agg: str = "sum", 
                        forma_data: str = '%Y%m'):
    
    """Retorna uma série com os valores dos ultimos x meses"""

    df_f = df.pivot_table(index = df[coluna_data].dt.strftime(forma_data),
                   values = valores,
                   aggfunc = _agg)
    
    date_completo = pd.DataFrame({'Date':pd.date_range(start = df[coluna_data].min(),end=dt.datetime.now()).strftime(forma_data).unique()})

    return df_f.merge(date_completo,
                   left_index=True,
                   right_on="Date",
                   how='right').set_index('Date').fillna(0).tail(epocas)