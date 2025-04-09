import pandas as pd
import streamlit as st
import utils
from conexao_supabase import supabase
import time

# Configuração da Página e Cabeçalho
utils.config_pagina()
utils.exibir_cabecalho()

def trocar_ponto_virgula (valor):
    resultado = valor.replace(",", "X").replace(".", ",").replace("X", ".").replace(",", "")
    return resultado

def cadastrar_projeto(
        id_clickup,contrato,nome_projeto,tipologia,modelo,
        valor_orcamento,dt_ref_orcamento,area,valor_medicao,caminho_rede,
        anexo_3d,anexo_planta,disciplinas):    
    
    try:
        existente = (
            supabase.table("tb_projetos")
            .select("id_clickup")
            .eq("id_clickup", id_clickup)
            .execute()
        )
        
        if existente.data:
            return {"erro": "⚠️  Este ID de Projeto já está cadsatrado!"}
        
        frk_id_tipologia = (
            supabase.table("tb_tipologia")
            .select("id")
            .eq("tipologia", tipologia)
            .execute()
            .data
        )

        # Se houver resultado, pegar o primeiro ID; senão, definir como None
        frk_id_tipologia = frk_id_tipologia[0]["id"] if frk_id_tipologia else None
        
        data_projeto = {
            "id_clickup": id_clickup,
            "contrato":contrato,
            "nome_projeto":nome_projeto,            
            "frk_id_tipologia": frk_id_tipologia,
            "modelo": modelo,
            "valor_orcamento": valor_orcamento,
            "dt_ref_orcamento": dt_ref_orcamento,
            "area": area,
            "valor_medicao": valor_medicao,
            "caminho_rede": caminho_rede,           
            "anexo_3d": anexo_3d,
            "anexo_planta": anexo_planta
        }
        response_projeto = supabase.table("tb_projetos").insert(data_projeto).execute()

        id_projeto = response_projeto.data[0]["id"] if response_projeto.data else None
        
        if not id_projeto:
            return {"erro": "Erro ao recuperar o ID do projeto."} 

        # Inserir disciplinas vinculadas ao projeto
        for disciplina in disciplinas:
            supabase.table("tb_disciplinas_por_projeto").insert({"id_projeto": id_projeto, "disciplina": disciplina}).execute()
        
        return response_projeto    
        
    except Exception as e:
        return {"erro": str(e)}

def converter_para_float(valor_str):
    """Converte número no formato brasileiro para float"""
    try:
        # Remove pontos separadores de milhar
        valor_str = valor_str.replace(".", "").replace(",", ".")
        return float(valor_str)
    except ValueError:
        return None

def consultar_banco_dados(tabela, coluna):
    query = supabase.table(tabela).select(coluna)
    response = query.execute()
    lista = list(set(d[coluna] for d in response.data if d[coluna] is not None))
    return lista

def lista_opcoes_tipologia(area_atuacao):

    query = (
        supabase.table("tb_tipologia")
        .select("tipologia, frk_id_area_atuacao, tb_area_atuacao!inner(area_atuacao)")
    .execute())

    df = pd.DataFrame(query.data)
    df = pd.concat([df.drop(['tb_area_atuacao'], axis=1), pd.json_normalize(df['tb_area_atuacao'])], axis=1)
    df = df.rename(columns={"tb_area_atuacao": "area_atuacao"})

    if area_atuacao != "":
        filtered_df = df[df['area_atuacao'] == area_atuacao]
    else:
        filtered_df = df
    
    lista_tipologias = filtered_df['tipologia'].tolist()

    return lista_tipologias


a = 2

def on_change():
    st.session_state.tipologia_opcoes = lista_opcoes_tipologia(st.session_state.area_atuacao_cad)

col76, col77 = st.columns([0.2, 0.8])
with col76:
    st.subheader("Cadastro de Projetos")

opcoes_disciplinas = [""] + sorted(consultar_banco_dados("tb_cadastro_disciplinas", "disciplina"))
opcoes_area_atuacao = [""] + sorted(consultar_banco_dados("tb_area_atuacao", "area_atuacao"))

if "tipologia_opcoes" not in st.session_state:
    st.session_state.tipologia_opcoes = [""]

#with st.form("cadastro_projeto"):

if "area_atuacao_cad" not in st.session_state:
    st.session_state["area_atuacao_cad"] = opcoes_area_atuacao[0]
if "tipologia_cad" not in st.session_state:
    st.session_state["tipologia_cad"] = opcoes_area_atuacao[0]

### Colunas da PRIMEIRA linha do formulário de cadastro
col1, col2, col3, col4 = st.columns([0.2, 0.2, 0.4, 0.2])

with col1:        
    area_atuacao = st.selectbox(
        "Área de atuação*",                        
        opcoes_area_atuacao,
        key="area_atuacao_cad",                        
        placeholder="Selecione a área de atuação",        
        on_change=on_change  # Atualiza a lista de tipologia ao mudar
    )
        
with col2:    

    opcoes_tipologia = [""] + st.session_state.tipologia_opcoes                       

    tipologia = st.selectbox("Tipologia*",
        opcoes_tipologia,
        key="tipologia_cad",        
        placeholder="Selecione a tipologia")
            
with col3:
    modelo = st.text_input("Modelo*",
                key="modelo",
                placeholder="Modelo")
    
with col4:
    #area = st.text_input("Área (m²)", value=0)  
    #area = trocar_ponto_virgula(area)    
    area = st.number_input("Área (m²)*")             

### Colunas da SEGUNDA linha do formulário de cadastro        
col5, col6, col7, col8, col9 = st.columns([0.2, 0.2, 0.1, 0.3, 0.2]) 

with col5:
    #valor_orcamento = st.text_input("Valor de orçamento", value=0) 
    #valor_orcamento = trocar_ponto_virgula(valor_orcamento)   
    valor_orcamento = st.number_input("Valor de orçamento*")       

with col6:
    dt_ref_orcamento = st.date_input("Data de Ref. Orçamento*") 

with col7:
    id_clickup = st.text_input("ID Projeto *",
                                placeholder="ID do projeto no clickup",                                 
                                key="id_projeto")
                    
with col8:
    nome_projeto = st.text_input("Nome do projeto*",
                                    placeholder="Digite o nome do projeto")

with col9:
    contrato = st.text_input("Contratante*",
                                placeholder="Digite o nome do contrato")

### Colunas da TERCEIRA linha do formulário de cadastro
col10, col11, = st.columns([0.4, 0.6])

with col10:
    caminho_rede = st.text_input("Caminho de rede*",
                            placeholder="Caminho de rede")   
    
with col11:
    disciplinas = st.multiselect("Disciplinas*",
                            sorted(opcoes_disciplinas),
                            placeholder="Selecione as diciplinas aplicadas no projeto")       

col12, col13, col14 = st.columns([0.2, 0.4, 0.4])

with col12:
    #valor_medicao = st.text_input("Valor da medição", value=0)      
    #valor_medicao = trocar_ponto_virgula(valor_medicao)
    valor_medicao = st.number_input("Valor da medição")

with col13:
    anexo_3d = st.text_input("Anexo 3D",
                                placeholder="Anexo 3D")   
    
with col14:
    anexo_planta = st.text_input("Anexo planta",
                                    placeholder="Anexo planta") 

### Botão de cadastro
submit = st.button("Cadastrar")

if submit:

    dt_ref_orcamento_str = dt_ref_orcamento.isoformat()       

    response = cadastrar_projeto(id_clickup,contrato,nome_projeto,tipologia,
                                    modelo,valor_orcamento,dt_ref_orcamento_str,area,valor_medicao,
                                    caminho_rede,anexo_3d,anexo_planta,disciplinas)
    
    if "erro" in response:
            st.error(response["erro"])
    else: 
        st.success("✅  Projeto cadastrado com sucesso!")
        
        time.sleep(2)

        # JavaScript para recarregar a pagina
        st.markdown('<meta http-equiv="refresh" content="1">', unsafe_allow_html=True)
        
        