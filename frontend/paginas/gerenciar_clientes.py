"""Página: Gerenciar Clientes."""

import streamlit as st

from backend.models import NivelConhecimento
from frontend.servicos import AppContext


def render(ctx: AppContext) -> None:
    st.header("Gerenciar Clientes")

    with st.expander("➕ Adicionar Novo Cliente"):
        with st.form("form_novo_cliente", clear_on_submit=True):
            st.subheader("Dados do Cliente")
            nome = st.text_input("Nome do Cliente*")
            email = st.text_input("Email")
            empresa = st.text_input("Empresa*")
            cargo = st.text_input("Cargo")
            area = st.text_input("Área/Departamento")
            nivel_estatistico = st.selectbox(
                "Nível de Conhecimento em Dados/Estatística",
                options=[n.value for n in NivelConhecimento],
            )
            usuario_final = st.checkbox("É o usuário final da solução?")

            if st.form_submit_button("Salvar Cliente"):
                if not nome or not empresa:
                    st.error("Por favor, preencha os campos obrigatórios (Nome e Empresa).")
                else:
                    ctx.run_async(ctx.cliente_repo.create(
                        nome=nome,
                        email=email,
                        empresa=empresa,
                        cargo=cargo,
                        area=area,
                        nivel_estatistico=NivelConhecimento(nivel_estatistico),
                        usuario_final=usuario_final,
                    ))
                    st.success(f"Cliente '{nome}' salvo com sucesso!")
                    st.rerun()

    st.subheader("Clientes Cadastrados")
    if not ctx.todos_clientes:
        st.info("Nenhum cliente cadastrado ainda.")
        return

    for cliente in ctx.todos_clientes:
        empresa_fmt = cliente.empresa.title() if cliente.empresa else "sem empresa"
        nome_fmt = cliente.nome.title() if cliente.nome else "sem nome"
        st.markdown(f"**{nome_fmt}** ({empresa_fmt}) - *{cliente.email or 'sem email'}*")
        st.markdown("---")
