"""Formatação do resultado do estimador para a UI (Streamlit)."""

from __future__ import annotations

from backend.estimativa import ResultadoEstimativa


def resumo_markdown(resultado: ResultadoEstimativa) -> str:
    """Texto curto explicando a sugestão de horas para exibir na página."""
    rotulo = "📈 por similaridade" if resultado.metodo == "similaridade" else "🧮 heurística"
    return (
        f"**Sugestão: {resultado.horas:.0f} horas** ({rotulo})\n\n"
        f"<small>{resultado.explicacao}</small>"
    )
