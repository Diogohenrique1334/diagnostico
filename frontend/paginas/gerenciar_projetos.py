"""Página: Gerenciar Projetos (busca, export, paginação e edição)."""

import io

import pandas as pd
import pytz
import streamlit as st

from backend.models import StatusProjeto, SkillProjeto
from frontend.servicos import AppContext

_FUSO = pytz.timezone("America/Sao_Paulo")
_COLS_EXPORT = [
    "id", "nome_projeto", "tipo_projeto", "status_projeto", "produto_projeto",
    "nome_cliente", "empresa_cliente", "Area_cliente", "nivel_cliente",
    "skills", "emails_adicionais", "data_criacao", "objetivo", "metrica_avaliacao",
    "valor_baseline", "meta_desejada", "prazo_desejado",
]


def _botoes_export(df_export: pd.DataFrame) -> None:
    col_csv, col_xlsx, _ = st.columns([1, 1, 4])
    with col_csv:
        st.download_button(
            "⬇️ CSV", data=df_export.to_csv(index=False).encode("utf-8-sig"),
            file_name="projetos.csv", mime="text/csv", use_container_width=True,
        )
    with col_xlsx:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Projetos")
        st.download_button(
            "⬇️ Excel", data=buffer.getvalue(), file_name="projetos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def _paginar(projetos: list) -> list:
    col_tam, col_pag = st.columns([1, 3])
    tamanho_pagina = col_tam.selectbox("Por página", [5, 10, 20, 50], index=1, key="tam_pagina")
    total = len(projetos)
    n_paginas = max(1, (total + tamanho_pagina - 1) // tamanho_pagina)
    pagina_atual = col_pag.number_input(
        f"Página (1–{n_paginas}) — {total} projeto(s)",
        min_value=1, max_value=n_paginas, value=1, step=1, key="num_pagina",
    )
    inicio = (pagina_atual - 1) * tamanho_pagina
    return projetos[inicio:inicio + tamanho_pagina]


def _bloco_status(ctx: AppContext, proj) -> None:
    cols_status = st.columns(2)
    with cols_status[0]:
        st.subheader("Status do Projeto")
        opcoes = [s.value for s in StatusProjeto]
        novo_status_valor = st.selectbox(
            "Alterar status para:", options=opcoes,
            index=opcoes.index(proj.status_projeto.value), key=f"status_{proj.id}",
        )
    with cols_status[1]:
        st.text(""); st.text("")
        if st.button("Atualizar Status", key=f"btn_status_{proj.id}"):
            ctx.run_async(ctx.projeto_repo.update_status(proj.id, StatusProjeto(novo_status_valor)))
            st.success("Status atualizado!")
            st.rerun()


def _linha(label: str, valor) -> None:
    """Exibe uma linha de detalhe apenas se houver conteúdo."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return
    st.markdown(f"**{label}:**\n\n> {valor}")


def _bloco_detalhes(proj) -> None:
    st.markdown("---")
    st.subheader("📝 Detalhes do Diagnóstico")
    st.markdown(f"**Objetivo Principal:** {proj.objetivo}")
    st.markdown(f"**Métrica de Avaliação:** {proj.metrica_avaliacao}")

    if st.toggle("Mostrar todos os detalhes do diagnóstico", key=f"toggle_details_{proj.id}"):
        with st.container(border=True):
            st.markdown("##### 🎯 Contexto & Objetivo")
            _linha("Decisão/ação que dispara", proj.decisao_ou_acao)
            _linha("Custo da inação", proj.custo_inacao)

            st.markdown("##### 📊 Situação Atual")
            _linha("Desempenho atual", proj.desempenho_atual)
            _linha("Baseline (valor atual)", proj.valor_baseline)
            _linha("Principais obstáculos", proj.o_que_prejudica_objetivo)

            st.markdown("##### 🏁 Definição de Sucesso")
            _linha("Meta desejada", proj.meta_desejada)
            if proj.prazo_desejado:
                _linha("Prazo desejado", proj.prazo_desejado.strftime("%d/%m/%Y"))

            st.markdown("##### 🗄️ Dados")
            _linha("Fontes / acesso", proj.dados_fontes)
            _linha("Qualidade conhecida", proj.dados_qualidade)

            st.markdown("##### 👥 Stakeholders & Restrições")
            _linha("Stakeholders", proj.stakeholders)
            _linha("Forma de cobrança", proj.como_e_cobrado)
            _linha("Restrições", proj.restricoes)
            _linha("Tentativas anteriores", proj.tentativas_anteriores)
            _linha("Hipótese do cliente", proj.como_melhorar_desempenho)


def _bloco_historico(proj) -> None:
    st.markdown("---")
    st.subheader("⏳ Histórico de Status do Projeto")
    if not proj.historico_status:
        return
    historico_ordenado = sorted(proj.historico_status, key=lambda h: h.data_mudanca, reverse=True)
    for entrada in historico_ordenado:
        data_formatada = entrada.data_mudanca.astimezone(_FUSO).strftime("%d/%m/%Y às %H:%M:%S")
        if entrada.status_anterior:
            st.markdown(f"- Mudou de **{entrada.status_anterior.value}** para **{entrada.status_novo.value}** em *{data_formatada}*")
        else:
            st.markdown(f"- Criado com status **{entrada.status_novo.value}** em *{data_formatada}*")


def _bloco_skills(ctx: AppContext, proj) -> None:
    st.markdown("---")
    st.subheader("🛠️ Habilidades Necessárias")
    skills_atuais = [s.skill for s in proj.skills]
    if skills_atuais:
        tags_html = "".join(
            f'<span style="background-color: #e0e0e0; color: #333; border-radius: 12px; padding: 5px 12px; margin: 4px; display: inline-block;">{skill}</span>'
            for skill in skills_atuais
        )
        st.markdown(tags_html, unsafe_allow_html=True)
    with st.form(key=f"form_skills_{proj.id}"):
        st.markdown("**Editar Habilidades:**")
        opcoes_skills = sorted([s.value for s in SkillProjeto])
        default_skills = [s for s in skills_atuais if s in opcoes_skills]
        skills_selecionadas = st.multiselect(
            "Selecione ou remova habilidades:", options=opcoes_skills,
            default=default_skills, key=f"ms_{proj.id}",
        )
        if st.form_submit_button("Salvar Habilidades"):
            ctx.run_async(ctx.projeto_repo.set_skills(proj.id, skills_selecionadas))
            st.success("Habilidades atualizadas!")
            st.rerun()


def _bloco_validacoes(ctx: AppContext, proj) -> None:
    st.markdown("---")
    st.subheader("Ciclos de Validação")
    if proj.validacoes:
        st.markdown("**Histórico de Feedbacks:**")
        for i, validacao in enumerate(proj.validacoes):
            st.markdown(f"**Validação {i + 1}:**")
            st.warning(f"**O que sentiu falta:** {validacao.o_que_sentiu_falta}")
            st.error(f"**O que tiraria/mudaria:** {validacao.o_que_tiraria}")

    if proj.status_projeto in (StatusProjeto.PRIMEIRA_VERSAO, StatusProjeto.AJUSTES):
        st.subheader("➕ Registrar Novo Feedback de Validação")
        with st.form(f"form_validacao_{proj.id}", clear_on_submit=True):
            falta = st.text_area("O que o cliente sentiu falta?", key=f"falta_{proj.id}")
            tiraria = st.text_area("O que o cliente tiraria/mudaria?", key=f"tiraria_{proj.id}")
            if st.form_submit_button("Salvar Validação"):
                ctx.run_async(ctx.validacao_repo.create(o_que_sentiu_falta=falta, o_que_tiraria=tiraria, id_projeto=proj.id))
                st.success("Validação registrada!")
                st.rerun()


def _bloco_emails(ctx: AppContext, proj) -> None:
    st.markdown("---")
    st.subheader("📧 E-mails Adicionais para Comunicação")
    emails_atuais = [e.email for e in proj.emails_adicionais]
    if emails_atuais:
        st.markdown("**E-mails atuais:**")
        for email in emails_atuais:
            st.markdown(f"- {email}")

    with st.form(key=f"form_emails_{proj.id}"):
        st.markdown("**Adicionar/Editar E-mails:**")
        st.info("Separe múltiplos e-mails com vírgula (,)")
        novos_emails = st.text_input(
            "E-mails adicionais (CC):", value=", ".join(emails_atuais), key=f"emails_{proj.id}"
        )
        if st.form_submit_button("Salvar E-mails"):
            ctx.run_async(ctx.projeto_repo.set_emails(proj.id, novos_emails))
            st.success("E-mails atualizados!")
            st.rerun()


def _render_projeto(ctx: AppContext, proj) -> None:
    titulo = f"**{proj.nome_projeto}** (Status: {proj.status_projeto.value})"
    with st.expander(titulo):
        _bloco_status(ctx, proj)
        _bloco_detalhes(proj)
        _bloco_historico(proj)
        _bloco_skills(ctx, proj)
        _bloco_validacoes(ctx, proj)
        _bloco_emails(ctx, proj)


def render(ctx: AppContext) -> None:
    st.header("📂 Gerenciar Projetos")

    df_filtrado = ctx.df_filtrado
    if not df_filtrado.empty:
        ids_filtrados = df_filtrado["id"].tolist()
        projetos_para_exibir = [p for p in ctx.todos_projetos if p.id in ids_filtrados]
    else:
        projetos_para_exibir = []

    if not ctx.todos_projetos:
        st.info("Nenhum projeto foi registrado ainda.")
        return
    if not projetos_para_exibir:
        st.warning("Nenhum projeto corresponde aos filtros selecionados na barra lateral.")
        return

    # Busca textual (nome do projeto ou cliente)
    busca = st.text_input("🔎 Buscar projeto (nome ou cliente)", key="busca_projetos").strip().lower()
    if busca:
        projetos_para_exibir = [
            p for p in projetos_para_exibir
            if busca in (p.nome_projeto or "").lower() or busca in (p.cliente.nome or "").lower()
        ]

    # Export da seleção visível
    ids_visiveis = [p.id for p in projetos_para_exibir]
    df_export = df_filtrado[df_filtrado["id"].isin(ids_visiveis)]
    df_export = df_export[[c for c in _COLS_EXPORT if c in df_export.columns]]
    _botoes_export(df_export)

    # Paginação
    if not projetos_para_exibir:
        st.warning("Nenhum projeto corresponde à busca.")
        return

    for proj in _paginar(projetos_para_exibir):
        _render_projeto(ctx, proj)
