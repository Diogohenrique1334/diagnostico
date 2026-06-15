"""Página: Registrar Diagnóstico de Projeto."""

import datetime as dt

import streamlit as st

from backend.models import TipoProjeto, StatusProjeto, SkillProjeto
from frontend.servicos import AppContext


def render(ctx: AppContext) -> None:
    st.header("🎙️ Registrar Diagnóstico de Projeto")

    if not ctx.todos_clientes or not ctx.todos_produtos:
        st.warning("⚠️ Você precisa ter pelo menos um cliente e um produto cadastrado. Use o menu ao lado.")
        return

    with st.form("form_nova_entrevista", clear_on_submit=True):
        # --- Identificação ---
        st.subheader("Informações Iniciais")
        map_clientes = {c.nome: c for c in ctx.todos_clientes}
        cliente_selecionado_nome = st.selectbox("Selecione o Cliente", options=map_clientes.keys())

        map_produtos = {p.nome_produto: p for p in ctx.todos_produtos}
        produto_selecionado_nome = st.selectbox("Selecione o Produto/Serviço", options=map_produtos.keys())

        nome_projeto = st.text_input("Nome do Projeto*")
        tipo_projeto_val = st.selectbox("Tipo do Projeto", options=[t.value for t in TipoProjeto])

        st.subheader("🛠️ Habilidades do Projeto")
        skills_selecionados = st.multiselect(
            "Selecione as habilidades necessárias para este projeto:",
            options=sorted([s.value for s in SkillProjeto]),
        )

        # --- Bloco 1: Contexto & Objetivo ---
        st.subheader("🎯 Contexto & Objetivo")
        objetivo = st.text_area(
            "1. Qual é o objetivo principal? (descreva o problema de negócio, não a solução)"
        )
        decisao_ou_acao = st.text_area(
            "2. Que decisão ou ação concreta o resultado vai disparar? Quem consome o resultado?"
        )
        custo_inacao = st.text_area(
            "3. O que acontece se nada for feito? (o custo de continuar como está hoje)"
        )

        # --- Bloco 2: Situação Atual ---
        st.subheader("📊 Situação Atual")
        desempenho_atual = st.text_area(
            "4. Como esse desempenho é medido / acompanhado hoje?"
        )
        valor_baseline = st.text_input(
            "5. Qual o valor atual da métrica hoje? (baseline — ex: 85%, R$ 30k/mês)"
        )
        o_que_prejudica_objetivo = st.text_area(
            "6. O que hoje mais atrapalha esse objetivo?"
        )

        # --- Bloco 3: Definição de Sucesso ---
        st.subheader("🏁 Definição de Sucesso")
        metrica_avaliacao = st.text_area(
            "7. Qual a métrica principal que vai definir o sucesso do projeto?"
        )
        meta_desejada = st.text_input(
            "8. Qual a meta desejada? (de quanto para quanto — ex: de 85% para 95%)"
        )
        col_p1, col_p2 = st.columns([1, 2])
        sem_prazo = col_p1.checkbox("Sem prazo definido", key="diag_sem_prazo")
        prazo_input = col_p2.date_input("9. Prazo desejado", value=dt.date.today(), key="diag_prazo")

        # --- Bloco 4: Dados ---
        st.subheader("🗄️ Dados")
        dados_fontes = st.text_area(
            "10. Onde estão os dados? (fontes, dono, acesso, formato, volume e histórico disponível)"
        )
        dados_qualidade = st.text_area(
            "11. Qualidade conhecida dos dados (furos, inconsistências, confiabilidade)"
        )

        # --- Bloco 5: Stakeholders & Restrições ---
        st.subheader("👥 Stakeholders & Restrições")
        stakeholders = st.text_area(
            "12. Quem usa e quem aprova a solução? (sponsor, usuários, quem pode barrar)"
        )
        como_e_cobrado = st.text_area(
            "13. Como você é cobrado(a) pelos resultados? (quem cobra e com que frequência)"
        )
        restricoes = st.text_area(
            "14. Restrições do projeto (prazo, orçamento, LGPD, onde precisa rodar)"
        )
        tentativas_anteriores = st.text_area(
            "15. Já tentaram resolver isso antes? O que aconteceu?"
        )
        como_melhorar_desempenho = st.text_area(
            "16. Na sua hipótese, o que poderia melhorar isso? "
            "(registro a visão do cliente — sem compromisso de seguir por ela)"
        )

        if st.form_submit_button("Salvar Diagnóstico"):
            if not nome_projeto:
                st.error("O nome do projeto é obrigatório.")
                return

            cliente_obj = map_clientes[cliente_selecionado_nome]
            produto_obj = map_produtos[produto_selecionado_nome]
            dados_projeto = dict(
                nome_projeto=nome_projeto.upper(),
                objetivo=objetivo,
                decisao_ou_acao=decisao_ou_acao,
                custo_inacao=custo_inacao,
                desempenho_atual=desempenho_atual,
                valor_baseline=valor_baseline,
                o_que_prejudica_objetivo=o_que_prejudica_objetivo,
                metrica_avaliacao=metrica_avaliacao,
                meta_desejada=meta_desejada,
                prazo_desejado=None if sem_prazo else prazo_input,
                dados_fontes=dados_fontes,
                dados_qualidade=dados_qualidade,
                stakeholders=stakeholders,
                como_e_cobrado=como_e_cobrado,
                restricoes=restricoes,
                tentativas_anteriores=tentativas_anteriores,
                como_melhorar_desempenho=como_melhorar_desempenho,
                tipo_projeto=TipoProjeto(tipo_projeto_val),
                status_projeto=StatusProjeto.LEVANTAMENTO_REQUISITOS,
                id_cliente=cliente_obj.id,
                id_produto=produto_obj.id,
            )
            ctx.run_async(ctx.projeto_repo.create(dados_projeto, skills=skills_selecionados))
            st.success(f"Diagnóstico para o projeto '{nome_projeto}' salvo com sucesso!")
            st.rerun()
