import pandas as pd
import streamlit as st
import utils
from conexao_supabase import supabase
from streamlit_modal import Modal

# Configuração da Página e Cabeçalho
utils.config_pagina()
utils.exibir_cabecalho()

def obter_opcoes_filtro(coluna, id_clickup=None, nome_projeto=None, contrato=None):
    """Obtém valores únicos de uma coluna para os filtros, considerando os outros filtros selecionados."""
    try:
        query = supabase.table("tb_projetos").select(coluna)
        if contrato:
            query = query.eq("contrato", contrato)
        if id_clickup:
            query = query.eq("id_clickup", id_clickup)
        if nome_projeto:
            query = query.ilike("nome_projeto", f"%{nome_projeto}%")
        
        response = query.execute()
        valores = list(set(d[coluna] for d in response.data if d[coluna] is not None))
        return sorted(valores)
    except Exception as e:
        return []
   
def formatar_valores_brasil (df, colunas):
    for col in colunas:
        try:
            df[col] = df[col].apply(
                lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) else "R$ 0,00"
            )
        except:
            continue
    
    return df

def consultar_banco_dados(tabela, coluna):
    query = supabase.table(tabela).select(coluna)
    response = query.execute()
    lista = list(set(d[coluna] for d in response.data if d[coluna] is not None))
    return lista

def cadastrar_projeto(
        id_clickup,contrato,nome_projeto,area_atuacao,tipologia,modelo,
        valor_orcamento,dt_ref_orcamento,area,valor_medicao,caminho_rede,
        projeto_3d,anexo_3d,anexo_planta, disciplinas):    
    
    try:
        existente = (
            supabase.table("tb_projetos")
            .select("id_clickup")
            .eq("id_clickup", id_clickup)
            .execute()
        )
        
        if existente.data:
            return {"erro": "⚠️  Este ID de Projeto já está cadsatrado!"}
        
        data = {
            "id_clickup": id_clickup,
            "contrato":contrato,
            "nome_projeto":nome_projeto,
            "area_atuacao": area_atuacao,
            "tipologia": tipologia,
            "modelo": modelo,
            "valor_orcamento": valor_orcamento,
            "dt_ref_orcamento": dt_ref_orcamento,
            "area": area,
            "valor_medicao": valor_medicao,
            "caminho_rede": caminho_rede,
            "projeto_3d": projeto_3d,
            "anexo_3d": anexo_3d,
            "anexo_planta": anexo_planta
        }
        response_projeto = supabase.table("tb_projetos").insert(data).execute()

        id_projeto = response_projeto.data[0]["id"] if response_projeto.data else None
        if not id_projeto:
            return {"erro": "Erro ao recuperar o ID do projeto."}
        
        # Inserir disciplinas vinculadas ao projeto
        for disciplina in disciplinas:
            supabase.table("tb_disciplinas_por_projeto").insert({"id_projeto": id_projeto, "disciplina": disciplina}).execute()
        
        return response_projeto    
        
    except Exception as e:
        return {"erro": str(e)}

# Função para carregar contratos do Supabase
@st.cache_data(ttl=300) #Mantém o cache dos dados por 5min
def obter_projetos_filtrados(id_clickup=None, nome_projeto=None, contrato=None):
    """Obtém a lista de projetos com disciplinas aplicadas, filtrando conforme necessário."""
    try:
        query = supabase.table("tb_projetos").select("*")
        
        if id_clickup:
            query = query.eq("id_clickup", id_clickup)
        if nome_projeto:
            query = query.ilike("nome_projeto", f"%{nome_projeto}%")
        if contrato:
            query = query.ilike("contrato", f"%{contrato}%")
        
        response = query.execute()
        projetos = response.data if response.data else []
        
        
        # Buscar disciplinas vinculadas
        for projeto in projetos:
            disciplinas_resp = (
                supabase.table("tb_disciplinas_por_projeto")
                .select("disciplina")
                .eq("id_projeto", projeto["id"])                
                .execute()
            )

            disciplinas = [d["disciplina"] for d in disciplinas_resp.data] if disciplinas_resp.data else []
            projeto["disciplinas"] = ", ".join(disciplinas)
        
        return projetos
    except Exception as e:
        return {"erro": str(e)}

if "recarregar" in st.session_state and st.session_state.recarregar:
    st.cache_data.clear()
    st.session_state.recarregar = False

st.subheader("Projetos Cadastrados")
st.write("")

col1, col2, col3, col4 = st.columns(4)

# Filtros interligados

with col1:
# Filtros com opções cadastradas no banco
    contrato = st.selectbox("Contrato", [""] + obter_opcoes_filtro("contrato"))
    
with col2:
    id_clickup = st.selectbox("ID ClickUp", [""] + obter_opcoes_filtro("id_clickup", contrato=contrato if contrato else None))    

with col3:
    nome_projeto = st.selectbox("Nome do Projeto", [""] + obter_opcoes_filtro("nome_projeto", contrato=contrato if contrato else None, id_clickup=id_clickup if id_clickup else None))

with col4:

    col5, col6 = st.columns(2)

    with col6:
        # Criar o modal
        st.write("")
        st.write("")
        modal = Modal(key="form_modal", title="✏️ Cadastro de Projetos",max_width=1500)

        if "modal_aberta" not in st.session_state:
            st.session_state["modal_aberta"] = False

        if st.button("Cadastrar Projeto"):
            modal.open()
            st.session_state["modal_aberta"] = True

projetos = obter_projetos_filtrados(id_clickup or None, nome_projeto or None, contrato or None)

# Definição de colunas a serem exibidas e seus nomes personalizados
colunas_exibir = {
    "id_clickup": "ID ClickUp",
    "nome_projeto": "Nome do Projeto",
    "contrato": "Contrato",
    "area_atuacao": "Área de Atuação",
    "valor_orcamento": "Valor do Orçamento",
    "dt_ref_orcamento": "Data de Referência do Orçamento",
    "area": "Área (m²)",
    "valor_medicao": "Valor da Medição",
    "disciplinas": "Disciplinas",
    "tipologia": "Tipologia",
    "modelo": "Modelo",
    "caminho_rede": "Caminho de rede",
    "projeto_3d": " Projeto 3D",
    "anexo_3d": "Anexo 3D",
    "anexo_planta":"Anexo planta" 
}

# Exibição dos projetos
if isinstance(projetos, dict) and "erro" in projetos:
    st.error(projetos["erro"])
elif projetos:
    df = pd.DataFrame(projetos)    
    df = df[list(colunas_exibir.keys())]  # Exibir apenas colunas selecionadas
    df.rename(columns=colunas_exibir, inplace=True)  # Renomear colunas para exibição
    st.write("")
    df_original = df
    df_editado = st.data_editor(df, hide_index=True)

    if not df_original.equals(df_editado):
        st.warning("Alterações detectadas! Clique no botão para salvar.")

        if st.button("Salvar Alterações"):
            # Percorrer as alterações e atualizar no Supabase
            for index, row in df_editado.iterrows():
                supabase.table("tb_projetos").update({
                    "id_clickup": row["ID ClickUp"],
                    "nome_projeto": row["Nome do Projeto"],
                    "contrato": row["Contrato"]
                }).eq("id_clickup", row["ID ClickUp"]).execute()

            st.success("Alterações salvas!")

else:
    st.write("Nenhum projeto encontrado.")

### TESTE ################################################################

opcoes_disciplinas = consultar_banco_dados("tb_cadastro_disciplinas", "disciplina")

if modal.is_open():

    with modal.container():

        with st.form("cadastro_form"):

            ### Colunas da PRIMEIRA linha do formulário de cadastro
            col1, col2, col3, col4 = st.columns([0.2, 0.4, 0.4, 0.2])

            with col1:
                id_clickup = st.text_input("ID Projeto *",
                                        placeholder="ID do projeto no clickup",                                 
                                        key="id_projeto")
            
            with col2:
                nome_projeto = st.text_input("Nome do projeto",
                                            placeholder="Digite o nome do projeto")
            
            with col3:
                contrato = st.text_input("Contrato",
                                        placeholder="Digite o nome do contrato")

            with col4:
                dt_ref_orcamento = st.date_input("Data de Ref. Orçamento")        

            ### Colunas da SEGUNDA linha do formulário de cadastro
            col5, col6, col7, col8, col9, col10 = st.columns(6)    

            with col5:        
                #area = st.text_input("Área (m²)", value=0)  
                #area = trocar_ponto_virgula(area)    
                area = st.number_input("Área (m²)")   


            with col6:
                #valor_orcamento = st.text_input("Valor de orçamento", value=0) 
                #valor_orcamento = trocar_ponto_virgula(valor_orcamento)   
                valor_orcamento = st.number_input("Valor de orçamento")   

            with col7:
                #valor_medicao = st.text_input("Valor da medição", value=0)      
                #valor_medicao = trocar_ponto_virgula(valor_medicao)
                valor_medicao = st.number_input("Valor da medição")
                            
            with col8:
                area_atuacao = st.text_input("Área de atuação",
                                            placeholder="Área de atuação")
            
            with col9:
                tipologia = st.text_input("Tipologia",
                                        placeholder="Tipologia")
            
            with col10:
                modelo = st.text_input("Modelo",
                                    placeholder="Modelo")
            
            ### Colunas da TERCEIRA linha do formulário de cadastro
            col11, col12, col13, col14 = st.columns(4)

            with col11:
                projeto_3d = st.text_input("Projeto 3D",
                                        placeholder="Projeto 3D")          

            with col12:
                anexo_3d = st.text_input("Anexo 3D",
                                        placeholder="Anexo 3D")         

            with col13:
                caminho_rede = st.text_input("Caminho de rede",
                                            placeholder="Caminho de rede")    
            
            with col14:
                anexo_planta = st.text_input("Anexo planta",
                                            placeholder="Anexo planta") 


            disciplinas = st.multiselect("Disciplinas",
                                        sorted(opcoes_disciplinas),
                                        placeholder="Selecione as diciplinas aplicadas no projeto")    

            ### Botão de cadastro
            submit = st.form_submit_button("Cadastrar")            

            if submit:

                dt_ref_orcamento_str = dt_ref_orcamento.isoformat()        

                response = cadastrar_projeto(id_clickup,contrato,nome_projeto,area_atuacao,tipologia,modelo,
                                            valor_orcamento,dt_ref_orcamento_str,area,valor_medicao,caminho_rede,
                                            projeto_3d,anexo_3d,anexo_planta, disciplinas)
                if "erro" in response:
                        st.error(response["erro"])
                else:
                    st.success("✅  Projeto cadastrado com sucesso!")
                    modal.open()


if st.session_state["modal_aberta"] and not modal.is_open():
    st.session_state["modal_aberta"] = False
    st.rerun()