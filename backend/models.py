# models.py
"""Modelos SQLAlchemy — schema normalizado (PostgreSQL/Neon).

Mudanças de normalização em relação ao schema SQLite original:
- `area` e `cargo` (antes strings livres em Cliente) viram tabelas lookup.
- `skills` e `emails_adicionais` (antes strings delimitadas por ';' em Projeto)
  viram tabelas filhas (1 linha por item).
- Enums armazenados como VARCHAR (native_enum=False) para evitar ALTER TYPE.
- `HistoricoStatusProjeto.data_mudanca` agora é timezone-aware (Brasília).
- Projeto ganhou campos de diagnóstico adicionais (decisão, baseline, meta,
  prazo, dados, stakeholders, restrições, tentativas).
"""

import enum
import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Enum,
    ForeignKey,
    DateTime,
    Date,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.database import Base

_FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")


def agora_brasilia() -> datetime.datetime:
    """Retorna o horário atual aware no fuso de Brasília."""
    return datetime.datetime.now(_FUSO_BRASILIA)


# --- Enums ---
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


# --- Tabelas lookup (normalização de area/cargo) ---
class Area(Base):
    __tablename__ = "areas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False, unique=True)
    clientes = relationship("Cliente", back_populates="area")


class Cargo(Base):
    __tablename__ = "cargos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False, unique=True)
    clientes = relationship("Cliente", back_populates="cargo")


# --- Tabelas principais ---
class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    ativo = Column(Boolean, default=True)
    empresa = Column(String, nullable=True)
    nivel_estatistico = Column(Enum(NivelConhecimento, native_enum=False), nullable=True)
    usuario_final = Column(Boolean, default=False)

    id_area = Column(Integer, ForeignKey("areas.id"), nullable=True)
    id_cargo = Column(Integer, ForeignKey("cargos.id"), nullable=True)
    area = relationship("Area", back_populates="clientes")
    cargo = relationship("Cargo", back_populates="clientes")

    projetos = relationship(
        "Projeto", back_populates="cliente", cascade="all, delete-orphan"
    )


class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_produto = Column(String, nullable=False, unique=True)
    projetos = relationship(
        "Projeto", back_populates="produto", cascade="all, delete-orphan"
    )


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

    # --- Campos de diagnóstico adicionais (Jun/2026) ---
    decisao_ou_acao = Column(String, nullable=True)        # decisão/ação que o resultado dispara + quem consome
    custo_inacao = Column(String, nullable=True)           # o que acontece se nada for feito
    valor_baseline = Column(String, nullable=True)         # valor atual da métrica (baseline)
    meta_desejada = Column(String, nullable=True)          # meta (de X para Y)
    prazo_desejado = Column(Date, nullable=True)           # prazo desejado (estruturado)
    dados_fontes = Column(String, nullable=True)           # fontes, dono, acesso, formato, volume, histórico
    dados_qualidade = Column(String, nullable=True)        # qualidade conhecida dos dados
    stakeholders = Column(String, nullable=True)           # quem usa/aprova (sponsor, usuários, quem barra)
    restricoes = Column(String, nullable=True)             # prazo, orçamento, LGPD, infra
    tentativas_anteriores = Column(String, nullable=True)  # já tentaram antes? o que aconteceu

    # Horas efetivamente investidas no MVP. Alimenta o estimador por similaridade
    # (backend/estimativa.py) e a geração de propostas. None = ainda não medido.
    horas_mvp = Column(Float, nullable=True)

    tipo_projeto = Column(
        Enum(TipoProjeto, native_enum=False), nullable=True, default=TipoProjeto.OUTROS
    )
    status_projeto = Column(
        Enum(StatusProjeto, native_enum=False),
        nullable=True,
        default=StatusProjeto.LEVANTAMENTO_REQUISITOS,
    )
    id_cliente = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    id_produto = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    cliente = relationship("Cliente", back_populates="projetos")
    produto = relationship("Produto", back_populates="projetos")
    validacoes = relationship(
        "ValidacaoProjeto", back_populates="projeto", cascade="all, delete-orphan"
    )
    historico_status = relationship(
        "HistoricoStatusProjeto",
        back_populates="projeto",
        cascade="all, delete-orphan",
    )
    skills = relationship(
        "ProjetoSkill", back_populates="projeto", cascade="all, delete-orphan"
    )
    emails_adicionais = relationship(
        "ProjetoEmail", back_populates="projeto", cascade="all, delete-orphan"
    )


class ProjetoSkill(Base):
    """Uma habilidade associada a um projeto (substitui a string delimitada)."""

    __tablename__ = "projeto_skill"
    __table_args__ = (UniqueConstraint("id_projeto", "skill", name="uq_projeto_skill"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_projeto = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    skill = Column(String, nullable=False)
    projeto = relationship("Projeto", back_populates="skills")


class ProjetoEmail(Base):
    """Um e-mail adicional associado a um projeto (substitui a string delimitada)."""

    __tablename__ = "projeto_email"
    __table_args__ = (UniqueConstraint("id_projeto", "email", name="uq_projeto_email"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_projeto = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    email = Column(String, nullable=False)
    projeto = relationship("Projeto", back_populates="emails_adicionais")


class ValidacaoProjeto(Base):
    __tablename__ = "validacoes_projeto"
    id = Column(Integer, primary_key=True, autoincrement=True)
    o_que_sentiu_falta = Column(String, nullable=True)
    o_que_tiraria = Column(String, nullable=True)
    id_projeto = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    projeto = relationship("Projeto", back_populates="validacoes")


class HistoricoStatusProjeto(Base):
    __tablename__ = "historico_status_projeto"
    id = Column(Integer, primary_key=True, autoincrement=True)
    status_anterior = Column(Enum(StatusProjeto, native_enum=False), nullable=True)
    status_novo = Column(Enum(StatusProjeto, native_enum=False), nullable=False)
    data_mudanca = Column(
        DateTime(timezone=True), nullable=False, default=agora_brasilia
    )
    id_projeto = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    projeto = relationship("Projeto", back_populates="historico_status")
