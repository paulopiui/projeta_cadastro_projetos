import streamlit as st
import streamlit_authenticator as stauth
from conexao_supabase import supabase

# 🔎 Buscar usuários do Supabase e montar config de autenticação
def carregar_usuarios():
    response = supabase.table("tb_usuarios").select("*").execute()
    dados = response.data
    return {
        "usernames": {
            user["usuario"]: {
                "name": user["usuario"],
                "password": user["senha_hash"]
            } for user in dados
        }
    }

# 🔧 Configuração direta, sem arquivo externo
config = {
    "credentials": carregar_usuarios()
}

# 🔐 Inicializar autenticação com dados do Supabase
authenticator = stauth.Authenticate(
    config["credentials"],
    "cookie_login_projetos",           # Nome do cookie
    "chave_super_secreta_cookie",      # Chave de segurança
    cookie_expiry_days=1
)

st.subheader("Login")

# Tela de login
login_result = authenticator.login(location="main", fields={"Form name": "Login"})

if login_result:
    nome, autenticado, username = login_result

    if autenticado:
        st.success(f"Bem-vinda, {nome} 👋")
        authenticator.logout("Sair", "sidebar")
    else:
        st.error("Usuário ou senha inválidos.")

