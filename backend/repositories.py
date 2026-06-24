"""Repositories assíncronos (SQLAlchemy async + asyncpg).

Cada método abre a própria sessão (padrão adequado ao Streamlit, que re-executa
o script a cada interação). Todas as relações acessadas pelo frontend são
carregadas de forma eager — com async não há lazy-load fora do contexto await.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from backend import models
from backend.database import async_session
from backend.emails import enviar_email_inicio_projeto, enviar_email_status
from backend.models import agora_brasilia
from backend.normalizacao import (
    normalizar_area,
    normalizar_cargo,
    normalizar_emails,
    normalizar_empresa,
    normalizar_skills,
)

logger = logging.getLogger(__name__)


async def _get_or_create(session, model, nome: str | None):
    """Busca uma linha lookup por nome; cria se não existir. None → None."""
    if nome is None:
        return None
    res = await session.execute(select(model).where(model.nome == nome))
    obj = res.scalar_one_or_none()
    if obj is None:
        obj = model(nome=nome)
        session.add(obj)
        await session.flush()
    return obj


class ClienteRepository:
    async def get_all(self) -> list[models.Cliente]:
        async with async_session() as s:
            res = await s.execute(
                select(models.Cliente)
                .options(
                    joinedload(models.Cliente.area),
                    joinedload(models.Cliente.cargo),
                )
                .order_by(models.Cliente.nome)
            )
            return list(res.scalars().all())

    async def create(
        self,
        *,
        nome: str,
        email: str | None,
        empresa: str | None,
        cargo: str | None,
        area: str | None,
        nivel_estatistico: models.NivelConhecimento | None,
        usuario_final: bool,
    ) -> int:
        async with async_session() as s:
            area_obj = await _get_or_create(s, models.Area, normalizar_area(area))
            cargo_obj = await _get_or_create(s, models.Cargo, normalizar_cargo(cargo))
            cliente = models.Cliente(
                nome=(nome or "").strip().lower() or None,
                email=(email or "").strip().lower() or None,
                empresa=normalizar_empresa(empresa),
                nivel_estatistico=nivel_estatistico,
                usuario_final=usuario_final,
                area=area_obj,
                cargo=cargo_obj,
            )
            s.add(cliente)
            await s.commit()
            return cliente.id


class ProdutoRepository:
    async def get_all(self) -> list[models.Produto]:
        async with async_session() as s:
            res = await s.execute(
                select(models.Produto).order_by(models.Produto.nome_produto)
            )
            return list(res.scalars().all())

    async def create(self, nome_produto: str) -> int:
        async with async_session() as s:
            produto = models.Produto(nome_produto=(nome_produto or "").strip().lower())
            s.add(produto)
            await s.commit()
            return produto.id


class ProjetoRepository:
    def _eager_options(self):
        return (
            joinedload(models.Projeto.cliente).joinedload(models.Cliente.area),
            joinedload(models.Projeto.cliente).joinedload(models.Cliente.cargo),
            joinedload(models.Projeto.produto),
            selectinload(models.Projeto.validacoes),
            selectinload(models.Projeto.historico_status),
            selectinload(models.Projeto.skills),
            selectinload(models.Projeto.emails_adicionais),
        )

    async def get_all(self) -> list[models.Projeto]:
        async with async_session() as s:
            res = await s.execute(
                select(models.Projeto)
                .options(*self._eager_options())
                .order_by(models.Projeto.id.desc())
            )
            return list(res.scalars().unique().all())

    async def create(self, dados_projeto: dict, skills=None) -> int:
        """Cria um projeto + histórico inicial + skills normalizadas."""
        async with async_session() as s:
            projeto = models.Projeto(**dados_projeto)
            projeto.historico_status.append(
                models.HistoricoStatusProjeto(
                    status_anterior=None,
                    status_novo=projeto.status_projeto,
                    data_mudanca=agora_brasilia(),
                )
            )
            for skill in normalizar_skills(skills):
                projeto.skills.append(models.ProjetoSkill(skill=skill))
            s.add(projeto)
            await s.commit()
            return projeto.id

    async def update_status(
        self, projeto_id: int, novo_status: models.StatusProjeto
    ) -> bool:
        """Atualiza o status, registra histórico e dispara e-mail (Outlook)."""
        async with async_session() as s:
            res = await s.execute(
                select(models.Projeto)
                .options(
                    joinedload(models.Projeto.cliente),
                    selectinload(models.Projeto.emails_adicionais),
                )
                .where(models.Projeto.id == projeto_id)
            )
            projeto = res.scalars().unique().one_or_none()

            if projeto is None or projeto.status_projeto == novo_status:
                return False

            s.add(
                models.HistoricoStatusProjeto(
                    status_anterior=projeto.status_projeto,
                    status_novo=novo_status,
                    data_mudanca=agora_brasilia(),
                    id_projeto=projeto.id,
                )
            )
            projeto.status_projeto = novo_status
            await s.commit()

        # E-mail fora da sessão; atributos já estão carregados (expire_on_commit=False).
        try:
            enviar_email_status(projeto, novo_status)
        except Exception as e:
            logger.error(
                "Falha ao enviar e-mail após atualização de status. "
                "Status salvo. Erro: %s",
                e,
            )
        return True

    async def set_skills(self, projeto_id: int, skills) -> None:
        """Substitui completamente as skills de um projeto."""
        async with async_session() as s:
            res = await s.execute(
                select(models.Projeto)
                .options(selectinload(models.Projeto.skills))
                .where(models.Projeto.id == projeto_id)
            )
            projeto = res.scalars().unique().one_or_none()
            if projeto is None:
                return
            # Diff em vez de clear()+re-add: evita DELETE+INSERT da MESMA linha no
            # mesmo flush (o INSERT vinha antes do DELETE e violava uq_projeto_skill).
            novas = set(normalizar_skills(skills))
            atuais = {ps.skill: ps for ps in projeto.skills}
            for skill, ps in atuais.items():
                if skill not in novas:
                    projeto.skills.remove(ps)
            for skill in novas - atuais.keys():
                projeto.skills.append(models.ProjetoSkill(skill=skill))
            await s.commit()

    async def enviar_email_inicio(self, projeto_id: int, dias: int) -> str | None:
        """Carrega o projeto (cliente + e-mails) e dispara o e-mail de início.

        Retorna o endereço de destino (To) em caso de sucesso, ou None se o
        projeto não existir. Erros de envio são propagados ao chamador.
        """
        async with async_session() as s:
            res = await s.execute(
                select(models.Projeto)
                .options(
                    joinedload(models.Projeto.cliente),
                    selectinload(models.Projeto.emails_adicionais),
                )
                .where(models.Projeto.id == projeto_id)
            )
            projeto = res.scalars().unique().one_or_none()
        if projeto is None:
            return None
        # Fora da sessão (atributos já carregados; expire_on_commit=False).
        return enviar_email_inicio_projeto(projeto, dias)

    async def set_horas_mvp(self, projeto_id: int, horas: float | None) -> None:
        """Registra (ou limpa) as horas efetivamente investidas no MVP."""
        async with async_session() as s:
            res = await s.execute(
                select(models.Projeto).where(models.Projeto.id == projeto_id)
            )
            projeto = res.scalars().unique().one_or_none()
            if projeto is None:
                return
            projeto.horas_mvp = horas
            await s.commit()

    async def set_emails(self, projeto_id: int, emails) -> None:
        """Substitui completamente os e-mails adicionais de um projeto."""
        async with async_session() as s:
            res = await s.execute(
                select(models.Projeto)
                .options(selectinload(models.Projeto.emails_adicionais))
                .where(models.Projeto.id == projeto_id)
            )
            projeto = res.scalars().unique().one_or_none()
            if projeto is None:
                return
            # Diff (mesmo motivo do set_skills: evita violar uq_projeto_email).
            novos = set(normalizar_emails(emails))
            atuais = {pe.email: pe for pe in projeto.emails_adicionais}
            for email, pe in atuais.items():
                if email not in novos:
                    projeto.emails_adicionais.remove(pe)
            for email in novos - atuais.keys():
                projeto.emails_adicionais.append(models.ProjetoEmail(email=email))
            await s.commit()


class ValidacaoRepository:
    async def create(
        self, *, o_que_sentiu_falta: str, o_que_tiraria: str, id_projeto: int
    ) -> int:
        async with async_session() as s:
            validacao = models.ValidacaoProjeto(
                o_que_sentiu_falta=o_que_sentiu_falta,
                o_que_tiraria=o_que_tiraria,
                id_projeto=id_projeto,
            )
            s.add(validacao)
            await s.commit()
            return validacao.id
