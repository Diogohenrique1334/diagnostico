import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
from PIL import Image
import datetime as dt
import pytz  # Importa a biblioteca para timezones
from streamlit_echarts import st_echarts
import baltazar as btz
from frontend.utils.transformadores import Crar_df_projetos, get_delta, Serie_tempo_relativo,df_para_lista_dict,dados_grafico_barras,colunas_por_delimitadores
from frontend.utils.graficos import grafico_rosca,barras_empilhadas_horizontais


import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Importações dos seus módulos
from backend.database import get_db_session
from backend.models import (
    Cliente, Produto, Projeto, NivelConhecimento, TipoProjeto,
    StatusProjeto, ValidacaoProjeto, HistoricoStatusProjeto, SkillProjeto
)
from backend.repositories import (
    ClienteRepository, ProdutoRepository, ProjetoRepository, ValidacaoRepository
)

# --- CONFIGURAÇÃO DA PÁGINA E SESSÃO ---
st.set_page_config(page_title="Gestão de Projetos", layout="wide", page_icon="📊")

# --- SETUP DO BANCO DE DADOS E REPOSITÓRIOS ---
db_session = next(get_db_session())
cliente_repo = ClienteRepository(db_session)
produto_repo = ProdutoRepository(db_session)
projeto_repo = ProjetoRepository(db_session)
validacao_repo = ValidacaoRepository(db_session)

# --- FUNÇÕES DE CACHE PARA BUSCAR DADOS ---
@st.cache_data(ttl=60)
def get_all_projects_cached():
    return projeto_repo.get_all()

@st.cache_data(ttl=60)
def get_all_clients_cached():
    return cliente_repo.get_all()

@st.cache_data(ttl=60)
def get_all_products_cached():
    return produto_repo.get_all()

# --- CARREGAMENTO E PREPARAÇÃO DOS DADOS ---
todos_projetos = get_all_projects_cached()
todos_clientes = get_all_clients_cached()
todos_produtos = get_all_products_cached()

df_projetos = Crar_df_projetos(todos_projetos)

# --- SIDEBAR E FILTROS ---
try:
    imagem = Image.open("foto_diogo.jpg")
    st.sidebar.image(imagem, caption='-------------------------------------')
except FileNotFoundError:
    st.sidebar.info("Imagem 'foto_diogo.jpg' não encontrada.")

st.sidebar.title("Navegação")
pagina = st.sidebar.radio(
    "Escolha uma seção:",
    ["🏠 Dashboard", "🎙️ Diagnóstico", "📂 Gerenciar Projetos", "👤 Gerenciar Clientes", "💼 Gerenciar Produtos"]
)

#Dimensoes:
Status_tratado = {
    "Levantamento de Requisitos":"Ativo",
    "Recebimento de Bases":"Ativo",
    "Análise exploratória da base de dados":"Ativo",
    "Construção da Pipeline":"Ativo",
    "Criação da Primeira Versão":"Ativo",
    "Ajustes no Projeto":"Ativo",
    "Criação da Documentação":"Ativo",
    "Ajustes Finos":"Ativo",
    "CANCELADO":"Inativo",
    "Projeto Finalizado":"Inativo"}

st.sidebar.title("Filtros do Dashboard")

projetos_disponiveis = sorted(df_projetos['nome_projeto'].unique()) if not df_projetos.empty else []
projetos_filtro = st.sidebar.multiselect('Projeto', options=projetos_disponiveis)

clientes_disponiveis = sorted(df_projetos['nome_cliente'].unique()) if not df_projetos.empty else []
clientes_filtro = st.sidebar.multiselect('Cliente', options=clientes_disponiveis)

empresa_cliente = sorted(df_projetos['empresa_cliente'].unique()) if not df_projetos.empty else []
empresa_clientes_filtro = st.sidebar.multiselect('Empresa', options=empresa_cliente)

Area_cliente = sorted(df_projetos['Area_cliente'].unique()) if not df_projetos.empty else []
area_clientes_filtro = st.sidebar.multiselect('Area do cliente', options=Area_cliente)

status_disponiveis = sorted(df_projetos['status_projeto'].map(Status_tratado).unique()) if not df_projetos.empty else []
status_filtro = st.sidebar.multiselect('Status do Projeto', options=status_disponiveis)

etapa_projeto = sorted(df_projetos['status_projeto'].unique()) if not df_projetos.empty else []
etapa_filtro = st.sidebar.multiselect('Etapa do Projeto', options=etapa_projeto)

tipos_disponiveis = sorted(df_projetos['tipo_projeto'].unique()) if not df_projetos.empty else []
tipos_filtro = st.sidebar.multiselect('Tipo de Projeto', options=tipos_disponiveis)

skills_disponiveis = sorted([s.value for s in SkillProjeto])
skills_filtro = st.sidebar.multiselect('Habilidades', options=skills_disponiveis)

if not df_projetos.empty and 'data_criacao' in df_projetos.columns and not df_projetos['data_criacao'].isnull().all():
    min_date = df_projetos['data_criacao'].min().date()
    max_date = df_projetos['data_criacao'].max().date() + dt.timedelta(days=1)
    data_filtro = st.sidebar.date_input(
        "Período de Criação do Projeto",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    data_filtro = st.sidebar.date_input("Período de Criação do Projeto", value=(datetime.date.today(), datetime.date.today()))

# --- LÓGICA DE FILTRAGEM ---
df_filtrado = df_projetos.copy()

if projetos_filtro:
    df_filtrado = df_filtrado[df_filtrado['nome_projeto'].isin(projetos_filtro)]

if clientes_filtro:
    df_filtrado = df_filtrado[df_filtrado['nome_cliente'].isin(clientes_filtro)]

if empresa_clientes_filtro:
    df_filtrado = df_filtrado[df_filtrado['empresa_cliente'].isin(empresa_clientes_filtro)]

if area_clientes_filtro:
    df_filtrado = df_filtrado[df_filtrado['Area_cliente'].isin(area_clientes_filtro)]

if status_filtro:
    df_filtrado = df_filtrado[df_filtrado['status_projeto'].map(Status_tratado).isin(status_filtro)]

if etapa_filtro:
    df_filtrado = df_filtrado[df_filtrado['status_projeto'].isin(etapa_filtro)]

if tipos_filtro:
    df_filtrado = df_filtrado[df_filtrado['tipo_projeto'].isin(tipos_filtro)]

if skills_filtro:
    for skill in skills_filtro:
        df_filtrado = df_filtrado[df_filtrado['skills'].str.contains(skill, na=False)]

if data_filtro and len(data_filtro) == 2 and 'data_criacao' in df_filtrado.columns:
    start_date, end_date = pd.to_datetime(data_filtro[0]), pd.to_datetime(data_filtro[1])
    df_filtrado = df_filtrado[(df_filtrado['data_criacao'] >= start_date) & (df_filtrado['data_criacao'] <= end_date)]


# --- PÁGINA INICIAL (DASHBOARD) ---
if pagina == "🏠 Dashboard":
    st.title("📊 Dashboard de Projetos")
    st.markdown("Visão geral dos projetos")

    if df_filtrado.empty and not df_projetos.empty:
        st.warning("Nenhum projeto encontrado com os filtros atuais. Altere os filtros na barra lateral para visualizar os dados.")
    elif df_projetos.empty:
        st.info("Nenhum projeto cadastrado ainda. Comece pela seção 'Diagnóstico'.")
    else:

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            projetos_mes = Serie_tempo_relativo(df_projetos,'data_criacao',valores = 'nome_projeto',_agg = "count")

            val = df_filtrado.shape[0] or 0

            delta = (
                get_delta(int(projetos_mes.tail(1).values), projetos_mes.values.mean())
            )
            st.metric(
                "Total de Projetos",
                f"{val:,.0f}",
                delta=delta,
                border=True,
                chart_data=projetos_mes.nome_projeto.tolist(),
                chart_type="area",
            )

        with col2:

            mask = df_projetos['status_projeto'].isin(['Projeto Finalizado','CANCELADO'])

            pj_finalizados = Serie_tempo_relativo(df_projetos[mask],
                                                  'data_criacao',
                                                  valores = 'nome_projeto',
                                                  epocas=5,
                                                  _agg = "count")
            
            val = df_projetos.loc[mask].shape[0] or 0

            delta = (
                get_delta(int(pj_finalizados.tail(1).values), pj_finalizados.values.mean())
            )
            st.metric(
                "Total de Projetos concluídos",
                f"{val:,.0f}",
                delta=delta,
                border=True,
                chart_data=pj_finalizados.nome_projeto.tolist(),
                chart_type="area",
            )

        with col3:

            mask = ~df_projetos['status_projeto'].isin(['Projeto Finalizado','CANCELADO'])
            
            pj_abertor = Serie_tempo_relativo(df_projetos[mask],
                                                  'data_criacao',
                                                  valores = 'nome_projeto',
                                                  epocas=20,
                                                  _agg = "count")
            
            val = df_projetos.loc[mask].shape[0] or 0

            delta = (
                get_delta(int(pj_abertor.tail(1).values), pj_abertor.values.mean())
            )

            st.metric(
                "Total projetos abertos",
                f"{val:,.0f}",
                delta=delta,
                border=True,
                chart_data=pj_abertor.nome_projeto.tolist(),
                chart_type="area",
            )

        with col4:

            clientes_atendidos = df_projetos.pivot_table(index = df_projetos.data_criacao.dt.strftime('%Y%m'),
                        values = 'nome_cliente',
                        aggfunc = lambda x: len(x.unique()))[2:]
            
            val = clientes_atendidos.nome_cliente.sum() or 0    
            delta = (
                get_delta(int(clientes_atendidos.tail(1).values), clientes_atendidos.values.mean())
            )
            st.metric(
                "Total clientes atendidos",
                f"{val:,}",
                delta=delta,
                border=True,
                chart_data=clientes_atendidos.nome_cliente.tolist(),
                chart_type="bar",
            )

        with st.container(border=True, height = 550):
            
            col_graf1, col_graf2 = st.columns([3,6])

            with col_graf1.container(border=True,height=520):

                mask = ~df_filtrado['status_projeto'].isin(['Projeto Finalizado','CANCELADO'])

                grafico_rosca(df_para_lista_dict(df_filtrado[mask],'status_projeto','id',_agg = 'count'))

            with col_graf2.container(border=True,height=520):
                st.subheader("Projetos por Tipo")

                barras_empilhadas_horizontais(*dados_grafico_barras(df_filtrado,'tipo_projeto','id', 'status_projeto',_agg = 'count'),tamanho="400px")
        
        with st.container(border=True, height=500):

            st.subheader("Ranking de Habilidades Utilizadas (Top 15)")

            barras_empilhadas_horizontais(*dados_grafico_barras(colunas_por_delimitadores(df_filtrado,'skills',";"), 'value','id', 'tipo_projeto',_agg = 'count'), tamanho = "300px")

            st.markdown("---")
            st.subheader("Tarefas em andamento por data")
            st_echarts(btz.funcoes_graficos_streamlit().calendar_option_from_series(
                btz.funcoes_data_frame().contagem_ativos_por_dia(
                    df_filtrado,
                    'data_criacao',
                    'Data_status_atual'),
                    [2025,2026]),height="450px"
                )

# --- DIAGNÓSTICO ---
elif pagina == "🎙️ Diagnóstico":
    st.header("🎙️ Registrar Diagnóstico de Projeto")

    if not todos_clientes or not todos_produtos:
        st.warning("⚠️ Você precisa ter pelo menos um cliente e um produto cadastrado. Use o menu ao lado.")
    else:
        with st.form("form_nova_entrevista", clear_on_submit=True):
            st.subheader("Informações Iniciais")
            map_clientes = {c.nome: c for c in todos_clientes}
            cliente_selecionado_nome = st.selectbox("Selecione o Cliente", options=map_clientes.keys())
            
            map_produtos = {p.nome_produto: p for p in todos_produtos}
            produto_selecionado_nome = st.selectbox("Selecione o Produto/Serviço", options=map_produtos.keys())

            nome_projeto = st.text_input("Nome do Projeto*")
            tipo_projeto_val = st.selectbox("Tipo do Projeto", options=[t.value for t in TipoProjeto])

            st.subheader("🛠️ Habilidades do Projeto")
            skills_selecionados = st.multiselect(
                "Selecione as habilidades necessárias para este projeto:",
                options=sorted([s.value for s in SkillProjeto])
            )
            
            st.subheader("Perguntas da Entrevista")
            objetivo = st.text_area("1. Qual é o principal objetivo deste projeto?")
            desempenho_atual = st.text_area("2. Como o desempenho é medido atualmente?")
            metrica_avaliacao = st.text_area("3. Qual será a principal métrica para avaliar o sucesso?")
            como_melhorar_desempenho = st.text_area("4. Na sua visão, o que é necessário para melhorar?")
            o_que_prejudica_objetivo = st.text_area("5. O que hoje mais atrapalha o objetivo?")
            como_e_cobrado = st.text_area("6. Como você é cobrado(a) pelos resultados?")

            submitted = st.form_submit_button("Salvar Diagnóstico")
            if submitted:
                if not nome_projeto:
                    st.error("O nome do projeto é obrigatório.")
                else:
                    cliente_obj = map_clientes[cliente_selecionado_nome]
                    produto_obj = map_produtos[produto_selecionado_nome]
                    skills_string = ";".join(skills_selecionados) if skills_selecionados else None
                    
                    novo_projeto = Projeto(
                        nome_projeto=nome_projeto.upper(),
                        objetivo=objetivo,
                        desempenho_atual=desempenho_atual,
                        como_e_cobrado=como_e_cobrado,
                        o_que_prejudica_objetivo=o_que_prejudica_objetivo,
                        metrica_avaliacao=metrica_avaliacao,
                        como_melhorar_desempenho=como_melhorar_desempenho,
                        tipo_projeto=TipoProjeto(tipo_projeto_val),
                        status_projeto=StatusProjeto.LEVANTAMENTO_REQUISITOS,
                        cliente=cliente_obj,
                        produto=produto_obj,
                        skills=skills_string
                    )
                    projeto_repo.create(novo_projeto)
                    st.success(f"Diagnóstico para o projeto '{nome_projeto}' salvo com sucesso!")
                    st.cache_data.clear()

# --- GERENCIAR PROJETOS ---
elif pagina == "📂 Gerenciar Projetos":
    st.header("📂 Gerenciar Projetos")

    st.cache_data.clear()

    if not df_filtrado.empty:
        ids_filtrados = df_filtrado['id'].tolist()
        projetos_para_exibir = [p for p in todos_projetos if p.id in ids_filtrados]
    else:
        projetos_para_exibir = []

    if not todos_projetos:
        st.info("Nenhum projeto foi registrado ainda.")
    elif not projetos_para_exibir:
        st.warning("Nenhum projeto corresponde aos filtros selecionados na barra lateral.")
    else:
        for proj in projetos_para_exibir:
            expander_title = f"**{proj.nome_projeto}** (Status: {proj.status_projeto.value})"
            with st.expander(expander_title):
                cols_status = st.columns(2)
                with cols_status[0]:
                    st.subheader("Status do Projeto")
                    novo_status_valor = st.selectbox(
                        "Alterar status para:",
                        options=[s.value for s in StatusProjeto],
                        index=[s.value for s in StatusProjeto].index(proj.status_projeto.value),
                        key=f"status_{proj.id}"
                    )
                with cols_status[1]:
                    st.text(""); st.text("")
                    if st.button("Atualizar Status", key=f"btn_status_{proj.id}"):
                        projeto_repo.update_status(proj.id, StatusProjeto(novo_status_valor))
                        st.success("Status atualizado!")
                        st.cache_data.clear()
                        st.rerun()
                
                st.markdown("---")
                st.subheader("📝 Detalhes do Diagnóstico")
                st.markdown(f"**Objetivo Principal:** {proj.objetivo}")
                st.markdown(f"**Métrica de Avaliação:** {proj.metrica_avaliacao}")
                if st.toggle("Mostrar todos os detalhes do diagnóstico", key=f"toggle_details_{proj.id}"):
                    with st.container(border=True):
                        st.markdown(f"**Desempenho Atual:**\n\n> {proj.desempenho_atual}")
                        st.markdown(f"**Visão do Cliente para Melhorar:**\n\n> {proj.como_melhorar_desempenho}")
                        st.markdown(f"**Principais Obstáculos:**\n\n> {proj.o_que_prejudica_objetivo}")
                        st.markdown(f"**Forma de Cobrança:**\n\n> {proj.como_e_cobrado}")
                
                st.markdown("---")
                st.subheader("⏳ Histórico de Status do Projeto")
                if proj.historico_status:
                    historico_ordenado = sorted(proj.historico_status, key=lambda h: h.data_mudanca, reverse=True)
                    for entrada in historico_ordenado:
                        data_formatada = entrada.data_mudanca.astimezone(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y às %H:%M:%S")
                        if entrada.status_anterior:
                            st.markdown(f"- Mudou de **{entrada.status_anterior.value}** para **{entrada.status_novo.value}** em *{data_formatada}*")
                        else:
                            st.markdown(f"- Criado com status **{entrada.status_novo.value}** em *{data_formatada}*")
                
                st.markdown("---")
                st.subheader("🛠️ Habilidades Necessárias")
                skills_atuais = proj.skills.split(';') if proj.skills else []
                if skills_atuais:
                    tags_html = "".join(f'<span style="background-color: #e0e0e0; color: #333; border-radius: 12px; padding: 5px 12px; margin: 4px; display: inline-block;">{skill}</span>' for skill in skills_atuais)
                    st.markdown(tags_html, unsafe_allow_html=True)
                with st.form(key=f"form_skills_{proj.id}"):
                    st.markdown("**Editar Habilidades:**")
                    skills_selecionadas = st.multiselect("Selecione ou remova habilidades:", options=sorted([s.value for s in SkillProjeto]), default=skills_atuais, key=f"ms_{proj.id}")
                    if st.form_submit_button("Salvar Habilidades"):
                        novas_skills_string = ";".join(skills_selecionadas) if skills_selecionadas else None
                        projeto_repo.update_skills(proj.id, novas_skills_string)
                        st.success("Habilidades atualizadas!")
                        st.cache_data.clear()
                        st.rerun()

                st.markdown("---")
                st.subheader("Ciclos de Validação")
                if proj.validacoes:
                    st.markdown("**Histórico de Feedbacks:**")
                    for i, validacao in enumerate(proj.validacoes):
                        st.markdown(f"**Validação {i+1}:**")
                        st.warning(f"**O que sentiu falta:** {validacao.o_que_sentiu_falta}")
                        st.error(f"**O que tiraria/mudaria:** {validacao.o_que_tiraria}")
                status_permitidos_validacao = [StatusProjeto.PRIMEIRA_VERSAO, StatusProjeto.AJUSTES]
                if proj.status_projeto in status_permitidos_validacao:
                    st.subheader("➕ Registrar Novo Feedback de Validação")
                    with st.form(f"form_validacao_{proj.id}", clear_on_submit=True):
                        falta = st.text_area("O que o cliente sentiu falta?", key=f"falta_{proj.id}")
                        tiraria = st.text_area("O que o cliente tiraria/mudaria?", key=f"tiraria_{proj.id}")
                        if st.form_submit_button("Salvar Validação"):
                            nova_validacao = ValidacaoProjeto(o_que_sentiu_falta=falta, o_que_tiraria=tiraria, projeto=proj)
                            validacao_repo.create(nova_validacao)
                            st.success("Validação registrada!")
                            st.cache_data.clear()
                            st.rerun()
                st.markdown("---")
                st.subheader("📧 E-mails Adicionais para Comunicação")
                
                # Mostrar e-mails atuais
                emails_atuais = proj.emails_adicionais.split(',') if proj.emails_adicionais else []
                if emails_atuais:
                    st.markdown("**E-mails atuais:**")
                    for email in emails_atuais:
                        st.markdown(f"- {email.strip()}")
                
                # Formulário para adicionar/editar e-mails
                with st.form(key=f"form_emails_{proj.id}"):
                    st.markdown("**Adicionar/Editar E-mails:**")
                    st.info("Separe múltiplos e-mails com ponto e vírgula (;)")
                    novos_emails = st.text_input(
                        "E-mails adicionais (CC):", 
                        value=proj.emails_adicionais if proj.emails_adicionais else "",
                        key=f"emails_{proj.id}"
                    )
                    
                    if st.form_submit_button("Salvar E-mails"):
                        projeto_repo.update_emails_adicionais(proj.id, novos_emails)
                        st.success("E-mails atualizados!")
                        st.cache_data.clear()
                        st.rerun()    

# --- GERENCIAR CLIENTES ---
elif pagina == "👤 Gerenciar Clientes":
    st.header("Gerenciar Clientes")
    with st.expander("➕ Adicionar Novo Cliente"):
        with st.form("form_novo_cliente", clear_on_submit=True):
            st.subheader("Dados do Cliente")
            nome = st.text_input("Nome do Cliente*")
            email = st.text_input("Email")
            empresa = st.text_input("Empresa*")
            cargo = st.text_input("Cargo")
            area = st.text_input("Área/Departamento")
            nivel_estatistico = st.selectbox("Nível de Conhecimento em Dados/Estatística", options=[n.value for n in NivelConhecimento])
            usuario_final = st.checkbox("É o usuário final da solução?")
            
            if st.form_submit_button("Salvar Cliente"):
                if not nome or not empresa:
                    st.error("Por favor, preencha os campos obrigatórios (Nome e Empresa).")
                else:
                    novo_cliente = Cliente(
                        nome=nome.lower(), email=email.lower(), empresa=empresa.lower(),
                        cargo=cargo.lower(), area=area.lower(),
                        nivel_estatistico=NivelConhecimento(nivel_estatistico),
                        usuario_final=usuario_final
                    )
                    cliente_repo.create(novo_cliente)
                    st.success(f"Cliente '{nome}' salvo com sucesso!")
                    st.cache_data.clear()

    st.subheader("Clientes Cadastrados")
    if not todos_clientes:
        st.info("Nenhum cliente cadastrado ainda.")
    else:
        for cliente in todos_clientes:
            st.markdown(f"**{cliente.nome.title()}** ({cliente.empresa.title()}) - *{cliente.email or 'sem email'}*")
            st.markdown("---")

# --- GERENCIAR PRODUTOS ---
elif pagina == "💼 Gerenciar Produtos":
    st.header("Gerenciar Produtos/Serviços")
    with st.expander("➕ Adicionar Novo Produto"):
        with st.form("form_novo_produto", clear_on_submit=True):
            nome_produto = st.text_input("Nome do Produto ou Serviço*")
            if st.form_submit_button("Salvar Produto"):
                if not nome_produto:
                    st.error("O nome do produto não pode ser vazio.")
                else:
                    novo_produto = Produto(nome_produto=nome_produto.lower())
                    produto_repo.create(novo_produto)
                    st.success(f"Produto '{nome_produto}' salvo com sucesso!")
                    st.cache_data.clear()

    st.subheader("Produtos Cadastrados")
    if not todos_produtos:
        st.info("Nenhum produto cadastrado ainda.")
    else:
        for prod in todos_produtos:
            st.markdown(f"- **{prod.nome_produto.title()}**")