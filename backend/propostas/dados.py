"""Camada de dados das propostas: enum de modelo, dataclass e defaults.

Sem dependência de ReportLab/Streamlit — só estrutura e regras de valor. Os
builders em `simples.py`/`avancada.py`/`dias.py` consomem `DadosProposta`.
"""

from __future__ import annotations

import datetime as dt
import enum
import math
from dataclasses import dataclass, field

# --- Identidade (defaults; editáveis ao gerar) ---
PROFISSIONAL = "Diogo Oliveira"
CARGO = "Cientista de Dados"
CONTATO = "diogohenrique1334@gmail.com"

GARANTIA_PADRAO_DIAS = 7

# Premissas e exclusões padrão (editáveis ao gerar) — protegem o escopo.
PREMISSAS_PADRAO = [
    "O cliente disponibiliza acesso aos dados e às pessoas-chave necessárias.",
    "Decisões e validações ocorrem dentro dos prazos combinados.",
    "Ferramentas e ambientes necessários estão disponíveis quando preciso.",
]
EXCLUSOES_PADRAO = [
    "Infraestrutura de produção e custos de nuvem, licenças ou APIs pagas.",
    "Manutenção evolutiva após o período de garantia.",
    "Qualquer item não descrito explicitamente no escopo acima.",
]


def numero_proposta(projeto_id: int, data: dt.date | None = None) -> str:
    """Gera um código de proposta no padrão PROP-AAAA-NNNN."""
    ano = (data or dt.date.today()).year
    return f"PROP-{ano}-{projeto_id:04d}"

# --- Defaults de valor (R$) — confirmados pelo Diogo ---
VALOR_HORA_SIMPLES = 70.0
VALOR_HORA_AVANCADA = 150.0
VALOR_DIA = 900.0

VALIDADE_PADRAO_DIAS = 15
HORAS_POR_DIA = 6  # horas produtivas/dia (conversão horas → dias no modelo Dias)


class ModeloProposta(enum.Enum):
    SIMPLES = "Simples"
    AVANCADA = "Avançada"
    DIAS = "Dias trabalhados"


def valor_padrao(modelo: ModeloProposta) -> float:
    return {
        ModeloProposta.SIMPLES: VALOR_HORA_SIMPLES,
        ModeloProposta.AVANCADA: VALOR_HORA_AVANCADA,
        ModeloProposta.DIAS: VALOR_DIA,
    }[modelo]


def unidade(modelo: ModeloProposta) -> str:
    return "dia" if modelo is ModeloProposta.DIAS else "hora"


def horas_para_dias(horas: float) -> int:
    """Converte horas estimadas em dias de trabalho (arredonda p/ cima)."""
    return max(1, math.ceil(horas / HORAS_POR_DIA))


_TITULO_MINUSCULAS = {
    "de", "da", "do", "das", "dos", "e", "com", "para", "por", "a", "o",
    "as", "os", "em", "no", "na", "nos", "nas", "ao", "à", "às", "aos", "um", "uma",
}
_TITULO_ACRONIMOS = {
    "ia", "ml", "bi", "etl", "api", "sql", "crm", "kpi", "nlp", "rag", "llm",
    "cv", "rpa", "ux", "ui", "pme", "cx", "ti", "pdf", "csv",
}


def formatar_titulo(texto: str) -> str:
    """Title-case em português: minúsculas para preposições, acrônimos em CAIXA."""
    palavras = (texto or "").lower().split()
    saida = []
    for i, p in enumerate(palavras):
        if p in _TITULO_ACRONIMOS:
            saida.append(p.upper())
        elif i > 0 and p in _TITULO_MINUSCULAS:
            saida.append(p)
        else:
            saida.append(p.capitalize())
    return " ".join(saida)


def formatar_moeda(valor: float) -> str:
    """Formata em reais no padrão brasileiro: 1234.5 -> 'R$ 1.234,50'."""
    inteiro, centavos = f"{valor:,.2f}".split(".")
    inteiro = inteiro.replace(",", ".")
    return f"R$ {inteiro},{centavos}"


@dataclass
class DadosProposta:
    """Tudo que um builder de PDF precisa para montar uma proposta."""

    modelo: ModeloProposta
    nome_projeto: str
    cliente: str
    tipo_projeto: str
    valor_unitario: float          # R$/hora (Simples/Avançada) ou R$/dia (Dias)
    quantidade: float              # horas ou dias
    escopo: list[str] = field(default_factory=list)   # entregáveis / itens de escopo
    objetivo: str | None = None
    prazo_dias: int | None = None
    validade_dias: int = VALIDADE_PADRAO_DIAS
    profissional: str = PROFISSIONAL
    cargo: str = CARGO
    contato: str = CONTATO
    numero: str | None = None
    data: dt.date = field(default_factory=dt.date.today)
    # Modo dos valores: True = estimados (no diagnóstico); False = horas já realizadas.
    valores_estimados: bool = True
    # Seções extras (cliente-facing). Listas vazias usam os defaults nos builders.
    premissas: list[str] = field(default_factory=list)
    exclusoes: list[str] = field(default_factory=list)
    garantia_dias: int | None = GARANTIA_PADRAO_DIAS
    incluir_aceite: bool = True
    # Projetos semelhantes usados na estimativa (nome, quantidade) — modelo Dias.
    referencias: list[tuple[str, float]] = field(default_factory=list)
    # Destinatário do e-mail (modelo Dias). Ex.: nome do gestor.
    destinatario: str | None = None
    # Caminho da foto para a capa (None = sem foto). Cliente-facing por padrão.
    foto_path: str | None = None
    # Caminho da assinatura (None = linha em branco no aceite).
    assinatura_path: str | None = None

    @property
    def unidade(self) -> str:
        return unidade(self.modelo)

    @property
    def total(self) -> float:
        return round(self.valor_unitario * self.quantidade, 2)

    @property
    def data_formatada(self) -> str:
        return self.data.strftime("%d/%m/%Y")

    @property
    def validade_formatada(self) -> str:
        return (self.data + dt.timedelta(days=self.validade_dias)).strftime("%d/%m/%Y")
