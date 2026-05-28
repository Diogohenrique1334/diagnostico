# models.py
import enum
import datetime # Import necessário para o timestamp
from sqlalchemy import Column, String, Integer, Boolean, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class NivelConhecimento(enum.Enum):
    BASICO = "Básico"
    INTERMEDIARIO = "Intermediário"
    AVANCADO = "Avançado"
    ESPECIALISTA = "Especialista"

class TipoProjeto(enum.Enum):

    AUTOMACAO = "Automação"
    DASHBOARD = "Dashboard"
    ANALISE_ESTATISTICA = "Análise Estatística"
    SOFTWARE_APLICATIVO = "Software / Aplicativo"
    VISAO_COMPUTACIONAL = "Visão Computacional"
    CLASSIFICACAO = "Classificação"
    REGRESSAO = "Regressão"
    WEBSCRAPING = "webscraping"
    OUTROS = "Outros"

class StatusProjeto(enum.Enum):
    LEVANTAMENTO_REQUISITOS = "Levantamento de Requisitos"
    RECEBIMENTO_BASES = "Recebimento de Bases"
    ANALISE_EXPLORATORIA = "Análise exploratória da base de dados"
    CONSTRUCAO_PIPELINE = "Construção da Pipeline"
    PRIMEIRA_VERSAO = "Criação da Primeira Versão"
    AJUSTES = "Ajustes no Projeto"
    DOCUMENTACAO = "Criação da Documentação"
    AJUSTES_FINOS = "Ajustes Finos"
    CANCELADO = "CANCELADO"
    FINALIZADO = "Projeto Finalizado"

# NOVO ENUM DE HABILIDADES
class SkillProjeto(enum.Enum):
    # Programação e Scripting
    PYTHON = "Python"
    R = "R"
    VBA = "VBA"
    JAVASCRIPT = "JavaScript"
    HTML = "html"
    
    # Bancos de Dados
    SQL = "SQL"
    MYSQL = "MySQL"
    POSTGRESQL = "PostgreSQL"
    SQL_SERVER = "SQL Server"
    MONGODB = "MongoDB"
    ALEMBIC = "Alembic"
    
    # Data Science & Machine Learning
    PANDAS = "Pandas"
    NUMPY = "NumPy"
    SCIKIT_LEARN = "Scikit-learn"
    ESTATISTICA_DESCRITIVA = "Estatística Descritiva"
    TESTES_HIPOTESE = "Testes de Hipótese"
    REGRESSAO_LINEAR = "Regressão Linear"
    REGRESSAO_LOGISTICA = "Regressão Logística"
    ARVORES_DECISAO = "Árvores de Decisão"
    RANDOM_FOREST = "Random Forest"
    XGBOOST = "XGBoost"
    CLUSTERIZACAO = "Clusterização (K-Means)"
    SERIES_TEMPORAIS = "Séries temporais"
    SARIMAX = "Sarimax"
    STATSMODELS = "Statsmodels"
    STATISTICA_PREDITIVA = "Statística descritiva"
    SVM = "SVM"
    ESTATISTICA_PRESCRITIVA = "Estatística prescritiva"
    SCIPY = "scipy"
    STEPWISE_AUTOMATICO = "Stepwise automático"
    
    # Deep Learning
    TENSORFLOW = "TensorFlow"
    KERAS = "Keras"
    PYTORCH = "PyTorch"
    VISAO_COMPUTACIONAL_CV2 = "Visão Computacional (OpenCV)"
    VISAO_COMPUTACIONAL_YOLO = "Visão computacional com Yolo"
    
    # Visualização de Dados
    MATPLOTLIB = "Matplotlib"
    SEABORN = "Seaborn"
    PLOTLY = "Plotly"
    STREAMLIT = "Streamlit"
    POWER_BI = "Power BI"
    TABLEAU = "Tableau"

    DAX = "Linguagem DAX"
    M = "Linguagem M"
    EXCEL = "Excel"
    
    # Engenharia de Dados & Automação
    ETL = "ETL (Extração, Transformação, Carga)"
    WEB_SCRAPING = "Web Scraping (BeautifulSoup, Selenium)"
    AUTOMACAO_PROCESSOS_RPA = "Automação de Processos (RPA)"
    APACHE_SPARK = "Apache Spark"
    APACHE_AIRFLOW = "Apache Airflow"
    LANGCHAIN = "langchain"
    RAG = "RAG"
    DOCKER = "DOCKER"

    # Interfaces de aplicativos
    PYINSTALLER = "PyInstaller"
    TKINTER = "tkinter"



# --- Tabelas ---
class Cliente(Base):
    
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    ativo = Column(Boolean, default=True)
    cargo = Column(String, nullable=True)
    area = Column(String, nullable=True)
    empresa = Column(String, nullable=True)
    nivel_estatistico = Column(Enum(NivelConhecimento), nullable=True)
    usuario_final = Column(Boolean, default=False)
    projetos = relationship("Projeto", back_populates="cliente", cascade="all, delete-orphan")


class Produto(Base):
    
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_produto = Column(String, nullable=False, unique=True)
    projetos = relationship("Projeto", back_populates="produto", cascade="all, delete-orphan")


class Projeto(Base):
    __tablename__ = "projetos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_projeto = Column(String, nullable=False)
    objetivo = Column(String, nullable=True)
    desempenho_atual = Column(String, nullable=True)
    como_e_cobrado = Column(String, nullable=True)
    o_que_prejudica_objetivo = Column(String, nullable=True)
    metrica_avaliacao = Column(String, nullable=True)
    como_melhorar_desempenho = Column(String, nullable=True)
    tipo_projeto = Column(Enum(TipoProjeto), nullable=True, default=TipoProjeto.OUTROS)
    status_projeto = Column(Enum(StatusProjeto), nullable=True, default=StatusProjeto.LEVANTAMENTO_REQUISITOS)
    id_cliente = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    id_produto = Column(Integer, ForeignKey('produtos.id'), nullable=False)
    cliente = relationship("Cliente", back_populates="projetos")
    produto = relationship("Produto", back_populates="projetos")
    validacoes = relationship("ValidacaoProjeto", back_populates="projeto", cascade="all, delete-orphan")
    
    historico_status = relationship("HistoricoStatusProjeto", back_populates="projeto", cascade="all, delete-orphan")

    skills = Column(String, nullable=True)

    emails_adicionais = Column(String, nullable=True)


class ValidacaoProjeto(Base):
    
    __tablename__ = "validacoes_projeto"
    id = Column(Integer, primary_key=True, autoincrement=True)
    o_que_sentiu_falta = Column(String, nullable=True)
    o_que_tiraria = Column(String, nullable=True)
    id_projeto = Column(Integer, ForeignKey('projetos.id'), nullable=False) 
    projeto = relationship("Projeto", back_populates="validacoes")



class HistoricoStatusProjeto(Base):
    __tablename__ = "historico_status_projeto"
    id = Column(Integer, primary_key=True, autoincrement=True)
    status_anterior = Column(Enum(StatusProjeto), nullable=True) # Null para o primeiro status
    status_novo = Column(Enum(StatusProjeto), nullable=False)
    data_mudanca = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    id_projeto = Column(Integer, ForeignKey('projetos.id'), nullable=False)
    projeto = relationship("Projeto", back_populates="historico_status")
