"""Estimador de horas de MVP por similaridade entre projetos.

Lógica pura — recebe objetos `Projeto` já carregados (não acessa Streamlit nem
o banco). A ideia: dado um projeto-alvo (tipo + skills), encontrar os projetos
passados mais parecidos que já têm `horas_mvp` registrado e estimar as horas
como a média ponderada pela similaridade. Sem histórico de horas suficiente,
cai numa heurística por tipo de projeto + complexidade (nº de skills).

Similaridade = Jaccard dos conjuntos de skills, com boost quando o tipo de
projeto coincide (mesmo tipo importa mais, mas as skills continuam pesando).
"""

from __future__ import annotations

from dataclasses import dataclass, field

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


def jaccard(a: set[str], b: set[str]) -> float:
    """Índice de Jaccard entre dois conjuntos. Vazio↔vazio = 0."""
    if not a and not b:
        return 0.0
    uniao = a | b
    if not uniao:
        return 0.0
    return len(a & b) / len(uniao)


def similaridade(skills_alvo, skills_hist, tipo_alvo, tipo_hist) -> float:
    """Similaridade [0, 1] combinando skills (Jaccard) e tipo de projeto.

    - Skills: contribuem com `PESO_SKILLS * jaccard`.
    - Mesmo tipo: adiciona um piso `BONUS_MESMO_TIPO` (mesmo sem overlap de
      skills, projetos do mesmo tipo já são parecidos).
    """
    sim = PESO_SKILLS * jaccard(skills_alvo, skills_hist)
    if tipo_alvo is not None and tipo_alvo == tipo_hist:
        sim += BONUS_MESMO_TIPO
    return min(sim, 1.0)


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

    Usa a média ponderada pela similaridade dos K vizinhos com `horas_mvp`
    preenchido; sem vizinhos, cai na heurística.
    """
    skills_alvo = _skills_set(projeto_alvo)
    tipo_alvo = _tipo_value(projeto_alvo)

    candidatos: list[Vizinho] = []
    for p in projetos_hist:
        if p.id == projeto_alvo.id:
            continue
        horas = getattr(p, "horas_mvp", None)
        if horas is None or horas <= 0:
            continue
        sim = similaridade(skills_alvo, _skills_set(p), tipo_alvo, _tipo_value(p))
        if sim > 0:
            candidatos.append(Vizinho(nome=p.nome_projeto, similaridade=sim, horas=float(horas)))

    if not candidatos:
        return _estimativa_heuristica(projeto_alvo)

    candidatos.sort(key=lambda v: v.similaridade, reverse=True)
    vizinhos = candidatos[:k]

    soma_pesos = sum(v.similaridade for v in vizinhos)
    horas = round(sum(v.horas * v.similaridade for v in vizinhos) / soma_pesos, 1)

    nomes = ", ".join(f"{v.nome} ({v.horas:.0f}h)" for v in vizinhos)
    explicacao = (
        f"Média ponderada por similaridade de {len(vizinhos)} "
        f"projeto(s) semelhante(s): {nomes}."
    )
    return ResultadoEstimativa(
        horas=horas, metodo="similaridade", vizinhos=vizinhos, explicacao=explicacao
    )
