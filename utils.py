import streamlit as st
import bcrypt

def exibir_cabecalho():
    
    col1, col2, col3 = st.columns([0.2, 0.1 ,0.6])

    with col1:        
        st.image("img/logo_preto_vermelho.png", width=300)

    with col3:        
        st.title("Gerenciamento de Projetos")

    st.divider()

def config_pagina():    
    st.set_page_config(
        page_title="Grupo Projeta | Projetos",      
        page_icon="img/favicon2.png",
        layout="wide"
    )

    # Configuração para ocultar menu do streamlit
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """

    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def criptografar_senha(senha):    

    hashed = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    return(hashed)


