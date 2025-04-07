import streamlit as st
import pandas as pd
from conexao_supabase import supabase
import bcrypt
import utils
from streamlit_modal import Modal

utils.config_pagina()
utils.exibir_cabecalho()

col1, col2, col3 = st.columns([0.4, 0.3, 0.3])


with col2:
    st.subheader("Usuários")

    query = supabase.table("tb_usuarios").select("nome", "usuario", "email")
    response = query.execute()

    usuarios = response.data if response.data else []

    df = pd.DataFrame(usuarios)

    st.dataframe(df, hide_index=True)
    #df_sem_indice = df.reset_index(drop=True)
    #st.write(df_sem_indice)
    #st.table(df)

    # Criar o modal
    modal = Modal(key="form_modal", title="👤 Cadastro de Usuários")

    if st.button("Cadastrar usuário"):
        modal.open()

if modal.is_open():
    with modal.container():        

        with st.form("cadastro_form"):
            nome = st.text_input("Nome completo")
            username = st.text_input("Nome de usuário (login)")
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            confirmar_senha = st.text_input("Confirmar senha", type="password")
            submit = st.form_submit_button("Cadastrar")

        if submit:
            if not nome or not username or not senha:
                st.warning("Por favor, preencha todos os campos.")
            elif senha != confirmar_senha:
                st.warning("As senhas não coincidem.")
            else:
                # Verifica se o usuário já existe
                existe = (supabase.table("tb_usuarios")
                        .select("id")
                        .or_(f"usuario.eq.{username},email.eq.{email}")
                        .execute()
                        )
                
                if existe.data:
                    st.error("⚠️  Este nome de usuário/email já está cadastrado.")
                else:
                    # Gera hash da senha
                    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

                    # Insere no Supabase
                    resultado = supabase.table("tb_usuarios").insert({
                        "nome": nome,
                        "usuario": username,
                        "email": email,
                        "senha_hash": senha_hash
                    }).execute()

                    if resultado.data:
                        st.success(f"Usuário {username} cadastrado com sucesso! ✅")
                    else:
                        st.error("Erro ao cadastrar usuário.")