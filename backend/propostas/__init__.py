"""Geração de propostas em PDF (+ e-mail no modelo Dias).

API pública:
- `gerar_proposta(modelo, dados) -> bytes`
- `gerar_email_dias(dados) -> (assunto, corpo)`
- `DadosProposta`, `ModeloProposta` e helpers de valor/formatação.
"""

from __future__ import annotations

from backend.propostas import avancada, dias, simples
from backend.propostas.dados import (
    DadosProposta,
    ModeloProposta,
    formatar_moeda,
    horas_para_dias,
    numero_proposta,
    unidade,
    valor_padrao,
)
from backend.propostas.dias import gerar_email_dias

_BUILDERS = {
    ModeloProposta.SIMPLES: simples.gerar,
    ModeloProposta.AVANCADA: avancada.gerar,
    ModeloProposta.DIAS: dias.gerar,
}


def gerar_proposta(modelo: ModeloProposta, dados: DadosProposta) -> bytes:
    """Gera o PDF da proposta no modelo escolhido e devolve os bytes."""
    return _BUILDERS[modelo](dados)


__all__ = [
    "gerar_proposta",
    "gerar_email_dias",
    "DadosProposta",
    "ModeloProposta",
    "formatar_moeda",
    "horas_para_dias",
    "numero_proposta",
    "unidade",
    "valor_padrao",
]
