"""Página: Gerenciar Produtos/Serviços."""

import streamlit as st

from frontend.servicos import AppContext


def render(ctx: AppContext) -> None:
    st.header("Gerenciar Produtos/Serviços")

    with st.expander("➕ Adicionar Novo Produto"):
        with st.form("form_novo_produto", clear_on_submit=True):
            nome_produto = st.text_input("Nome do Produto ou Serviço*")
            if st.form_submit_button("Salvar Produto"):
                if not nome_produto:
                    st.error("O nome do produto não pode ser vazio.")
                else:
                    ctx.run_async(ctx.produto_repo.create(nome_produto))
                    st.success(f"Produto '{nome_produto}' salvo com sucesso!")
                    st.rerun()

    st.subheader("Produtos Cadastrados")
    if not ctx.todos_produtos:
        st.info("Nenhum produto cadastrado ainda.")
        return

    for prod in ctx.todos_produtos:
        st.markdown(f"- **{prod.nome_produto.title()}**")
