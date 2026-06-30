"""Estimador de horas de MVP por similaridade entre projetos.

Adaptador fino de domínio: traduz objetos `Projeto` (skills + tipo + horas) para
o KNN genérico do Baltazar (`baltazar.ML.supervisionado.knn_similaridade`) e
veste o resultado na interface que a UI espera. A matemática (Jaccard +
vizinhos + média ponderada) vive no Baltazar e é reutilizável entre projetos.

Aqui ficam só as partes de domínio: como extrair skills/tipo de um `Projeto` e o
fallback heurístico (horas-base por tipo + complexidade) usado quando ainda não
há projetos semelhantes com `horas_mvp` registrado.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from baltazar.ML.supervisionado.knn_similaridade import (
    ItemHistorico,
    knn_regressao_similaridade,
)

# --- Parâmetros do modelo (ajustáveis) ---
K_VIZINHOS = 5
PESO_SKILLS = 0.6        # quanto a similaridade de skills contribui
BONUS_MESMO_TIPO = 0.4   # piso de similaridade quando o tipo coincide
SKILLS_BASE_COMPLEXIDADE = 3  # skills "de graça" antes de somar complexidade
HORAS_POR_SKILL_EXTRA = 2.0   # horas somadas por skill acima da base (heurística)

# Horas-base por tipo de projeto (MVP enxuto). Usadas só no cold start, quando
# não há projetos semelhantes com horas registradas. Chave = TipoProjeto.value.
HORAS_BASE_TIPO = {
    "Automação": 16.0,
    "Dashboard": 24.0,
    "Análise Estatística": 20.0,
    "Software / Aplicativo": 40.0,
    "Visão Computacional": 40.0,
    "Classificação": 28.0,
    "Regressão": 24.0,
    "webscraping": 16.0,
    "Outros": 20.0,
}
HORAS_BASE_PADRAO = 20.0


@dataclass
class Vizinho:
    """Um projeto histórico usado na estimativa."""

    nome: str
    similaridade: float
    horas: float


@dataclass
class ResultadoEstimativa:
    """Resultado do estimador, pronto para a UI."""

    horas: float
    metodo: str                       # "similaridade" | "heuristica"
    vizinhos: list[Vizinho] = field(default_factory=list)
    explicacao: str = ""


def _skills_set(projeto) -> set[str]:
    """Conjunto de skills (strings) de um projeto, normalizado para comparação."""
    return {s.skill.strip().lower() for s in projeto.skills if s.skill and s.skill.strip()}


def _tipo_value(projeto) -> str | None:
    return projeto.tipo_projeto.value if projeto.tipo_projeto else None


def _estimativa_heuristica(projeto_alvo) -> ResultadoEstimativa:
    """Fallback: horas-base do tipo + complexidade pelo nº de skills."""
    tipo = _tipo_value(projeto_alvo)
    base = HORAS_BASE_TIPO.get(tipo, HORAS_BASE_PADRAO)
    n_skills = len(_skills_set(projeto_alvo))
    extra = max(0, n_skills - SKILLS_BASE_COMPLEXIDADE) * HORAS_POR_SKILL_EXTRA
    horas = round(base + extra, 1)
    explicacao = (
        f"Sem projetos semelhantes com horas registradas. Estimativa heurística: "
        f"base de {base:.0f}h para '{tipo or 'Outros'}' + "
        f"{extra:.0f}h por complexidade ({n_skills} skills)."
    )
    return ResultadoEstimativa(horas=horas, metodo="heuristica", explicacao=explicacao)


def estimar_horas(projeto_alvo, projetos_hist, k: int = K_VIZINHOS) -> ResultadoEstimativa:
    """Estima horas de MVP do `projeto_alvo` a partir de `projetos_hist`.

    Monta o histórico (projetos com `horas_mvp` > 0), delega ao KNN do Baltazar
    e, sem vizinhos, cai na heurística de domínio.
    """
    historico = [
        ItemHistorico(
            rotulo=p.nome_projeto,
            tags=_skills_set(p),
            valor=getattr(p, "horas_mvp", None),
            categoria=_tipo_value(p),
        )
        for p in projetos_hist
        if p.id != projeto_alvo.id and (getattr(p, "horas_mvp", None) or 0) > 0
    ]

    resultado = knn_regressao_similaridade(
        _skills_set(projeto_alvo),
        _tipo_value(projeto_alvo),
        historico,
        k=k,
        peso_tags=PESO_SKILLS,
        bonus_mesma_categoria=BONUS_MESMO_TIPO,
    )

    if resultado.valor is None:
        return _estimativa_heuristica(projeto_alvo)

    vizinhos = [
        Vizinho(nome=v.rotulo, similaridade=v.similaridade, horas=v.valor)
        for v in resultado.vizinhos
    ]
    nomes = ", ".join(f"{v.nome} ({v.horas:.0f}h)" for v in vizinhos)
    explicacao = (
        f"Média ponderada por similaridade de {len(vizinhos)} "
        f"projeto(s) semelhante(s): {nomes}."
    )
    return ResultadoEstimativa(
        horas=round(resultado.valor, 1),
        metodo="similaridade",
        vizinhos=vizinhos,
        explicacao=explicacao,
    )
