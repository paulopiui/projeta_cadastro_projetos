from supabase import create_client, Client
from dotenv import load_dotenv
import tomllib
import streamlit as st

# 🔹 Carregar configurações do arquivo TOML
def load_config():
    with open("config/secrets.toml", "rb") as file:
        config = tomllib.load(file)
    return {
        "supabase_url": config["supabase"]["SUPABASE_URL"],
        "supabase_key": config["supabase"]["SUPABASE_KEY"]
    }

# 🔹 Conectar ao Supabase
@st.cache_resource
def connect_to_supabase(config) -> Client:
    return create_client(config["supabase_url"], config["supabase_key"])

# Carregar configurações e conectar ao Supabase
config = load_config()
supabase = connect_to_supabase(config)
