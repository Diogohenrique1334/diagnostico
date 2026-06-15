"""Normalização de dados categóricos e de contato.

Usado tanto na migração SQLite→Neon quanto nos fluxos de criação ao vivo, para
que os dados se mantenham limpos daqui pra frente (sem o drift que existia:
'cx', 'cx - matricial', 'cx pme', 'cx - pme'...).
"""

from __future__ import annotations

import re

# Mapeamento canônico de ÁREAS (aplicado após normalização básica).
_AREA_CANONICA = {
    "cx - matricial": "cx",
    "cx - pme": "cx pme",
    "ger de gestao de aparelhos": "gestao de aparelhos",
}

# Mapeamento canônico de CARGOS (conservador — sem expandir abreviações).
_CARGO_CANONICA = {
    "professora": "professor",
}


def _norm_basico(valor: str | None) -> str | None:
    """Trim, colapsa espaços internos e lowercase. Vazio vira None."""
    if valor is None:
        return None
    limpo = re.sub(r"\s+", " ", valor).strip().lower()
    return limpo or None


def normalizar_area(valor: str | None) -> str | None:
    """Normaliza e aplica merges canônicos de área."""
    base = _norm_basico(valor)
    if base is None:
        return None
    return _AREA_CANONICA.get(base, base)


def normalizar_cargo(valor: str | None) -> str | None:
    """Normaliza e aplica merges canônicos de cargo."""
    base = _norm_basico(valor)
    if base is None:
        return None
    return _CARGO_CANONICA.get(base, base)


def normalizar_empresa(valor: str | None) -> str | None:
    """Normaliza nome de empresa (sem merges — apenas limpeza)."""
    return _norm_basico(valor)


def normalizar_emails(valor) -> list[str]:
    """Aceita string delimitada (',' ou ';') ou lista e retorna e-mails limpos.

    Lowercase, sem espaços, sem duplicatas, preservando a ordem.
    """
    if not valor:
        return []
    if isinstance(valor, str):
        partes = re.split(r"[;,]", valor)
    else:
        partes = list(valor)

    vistos: set[str] = set()
    resultado: list[str] = []
    for parte in partes:
        email = (parte or "").strip().lower()
        if email and email not in vistos:
            vistos.add(email)
            resultado.append(email)
    return resultado


def normalizar_skills(valor) -> list[str]:
    """Aceita string delimitada por ';' ou lista e retorna skills limpas.

    Preserva a capitalização original (os valores são labels do enum
    SkillProjeto, ex.: 'Power BI'). Remove duplicatas preservando a ordem.
    """
    if not valor:
        return []
    if isinstance(valor, str):
        partes = valor.split(";")
    else:
        partes = list(valor)

    vistos: set[str] = set()
    resultado: list[str] = []
    for parte in partes:
        skill = (parte or "").strip()
        if skill and skill not in vistos:
            vistos.add(skill)
            resultado.append(skill)
    return resultado
