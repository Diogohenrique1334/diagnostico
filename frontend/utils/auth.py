"""Autenticação simples por senha de administrador.

O Dashboard é público; todas as outras páginas (que expõem e-mails de clientes
ou permitem escrita) exigem login. A senha vem de `st.secrets["senha_admin"]`
— nunca hardcoded — e é comparada com `hmac.compare_digest` (constante no tempo).
O estado de login vive em `st.session_state` (por sessão do navegador).
"""

from __future__ import annotations

import hmac

import streamlit as st

from frontend.utils import tema

_CHAVE_SESSAO = "admin_ok"


def _senha_configurada() -> str | None:
    """Lê a senha do secrets; None se não estiver configurada."""
    try:
        return st.secrets["senha_admin"]
    except (KeyError, FileNotFoundError):
        return None


def esta_logado() -> bool:
    return bool(st.session_state.get(_CHAVE_SESSAO, False))


def tela_login() -> None:
    """Renderiza o formulário de login. Em senha correta, marca a sessão e recarrega."""
    tema.hero("Área restrita", "Esta seção exige senha de administrador", icone="🔒")

    senha_real = _senha_configurada()
    if senha_real is None:
        st.error(
            "Senha de administrador não configurada. Defina `senha_admin` em "
            "`.streamlit/secrets.toml` (local) ou em App settings → Secrets (Cloud)."
        )
        return

    with st.form("login_admin"):
        senha = st.text_input("Senha", type="password")
        ok = st.form_submit_button("Entrar")

    if ok:
        if hmac.compare_digest(senha, senha_real):
            st.session_state[_CHAVE_SESSAO] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")


def exigir_login() -> bool:
    """Bloqueia a página se não estiver logado. Retorna True se liberado."""
    if esta_logado():
        return True
    tela_login()
    st.stop()


def botao_logout() -> None:
    """Mostra um botão de logout na sidebar quando o usuário está logado."""
    if esta_logado():
        if st.sidebar.button("🚪 Sair"):
            st.session_state[_CHAVE_SESSAO] = False
            st.rerun()
