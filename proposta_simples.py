"""CLI de exemplo: gera um PDF de proposta usando backend.propostas.

A lógica de geração mora em `backend/propostas/` (camada de documento, usada
também pelo app em Gerenciar Projetos). Este script só monta um exemplo e grava
o PDF em disco — útil para inspecionar o layout fora do Streamlit.

Uso:
    python proposta_simples.py                # modelo simples (padrão)
    python proposta_simples.py avancada       # modelo avançada
    python proposta_simples.py dias           # modelo dias trabalhados
"""

import sys
from pathlib import Path

from backend.propostas import (
    DadosProposta,
    ModeloProposta,
    gerar_proposta,
    horas_para_dias,
    valor_padrao,
)

_PDF_PATH = "Proposta_Modelo_Cobranca_Projetos.pdf"
_FOTO_PATH = Path(__file__).resolve().parent / "foto_diogo.jpg"

_ESCOPO = [
    "Pipeline de ingestão e limpeza dos dados",
    "Dashboard interativo com os principais indicadores",
    "Modelo preditivo inicial (baseline)",
    "Documentação de uso e handover",
]


def _exemplo(modelo: ModeloProposta) -> DadosProposta:
    is_dias = modelo is ModeloProposta.DIAS
    horas = 28
    quantidade = horas_para_dias(48) if is_dias else horas
    foto = None if is_dias else (str(_FOTO_PATH) if _FOTO_PATH.exists() else None)
    return DadosProposta(
        modelo=modelo,
        nome_projeto="Previsão de Churn",
        cliente="João Silva",
        tipo_projeto="Classificação",
        valor_unitario=valor_padrao(modelo),
        quantidade=quantidade,
        escopo=_ESCOPO,
        objetivo="Reduzir o churn antecipando clientes em risco.",
        prazo_dias=15,
        referencias=[("Dashboard Comercial", 6), ("ETL de Faturamento", 8)],
        destinatario="Carlos",
        foto_path=foto,
    )


def main() -> None:
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "simples"
    modelo = {
        "simples": ModeloProposta.SIMPLES,
        "avancada": ModeloProposta.AVANCADA,
        "dias": ModeloProposta.DIAS,
    }.get(arg, ModeloProposta.SIMPLES)

    pdf = gerar_proposta(modelo, _exemplo(modelo))
    with open(_PDF_PATH, "wb") as f:
        f.write(pdf)
    print(f"{_PDF_PATH} ({modelo.value})")


if __name__ == "__main__":
    main()
