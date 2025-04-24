import pandas as pd
import streamlit as st
import utils
from conexao_supabase import supabase

# Configuração da Página e Cabeçalho
utils.config_pagina()
utils.exibir_cabecalho()

def obter_opcoes_filtro(tabela, coluna, area_atuacao=None, tipologia=None, nome_projeto=None, modelo= None):
    """Obtém valores únicos de uma coluna para os filtros, considerando os outros filtros selecionados."""
    try:
        query = supabase.table(tabela).select(coluna)
        if area_atuacao:
            query = query.eq("area_atuacao", area_atuacao)
        if tipologia:
            query = query.eq("tipologia", tipologia)
        if nome_projeto:
            query = query.ilike("nome_projeto", f"%{nome_projeto}%")
        if modelo:
            query = query.ilike("modelo", f"%{modelo}%")            
        
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

# Função para carregar contratos do Supabase
@st.cache_data(ttl=300) #Mantém o cache dos dados por 5min
def obter_projetos_filtrados(area_atuacao=None, tipologia=None, nome_projeto=None, modelo=None, valor_orcamento_min=0, valor_orcamento_max=10000000):
    """Obtém a lista de projetos com disciplinas aplicadas, filtrando conforme necessário."""
    try:
        query = (
            supabase.table("tb_projetos")
            .select("*, tb_tipologia!inner(tipologia, frk_id_area_atuacao, tb_area_atuacao!inner(area_atuacao))")
        )      

        if area_atuacao:
            query = query.eq("tb_tipologia.tb_area_atuacao.area_atuacao", area_atuacao)
        if tipologia:
            query = query.eq("tb_tipologia.tipologia",tipologia)
        if nome_projeto:
            query = query.ilike("nome_projeto", f"%{nome_projeto}%")
        if valor_orcamento_max:
            query = query.gte("valor_orcamento", valor_orcamento_min).lte("valor_orcamento", valor_orcamento_max)           
        if modelo:
            query = query.ilike("modelo", f"%{modelo}%")        
        
        response = query.execute()
        projetos = response.data if response.data else []
        
        for projeto in projetos:    

            tipologia_data = projeto.get("tb_tipologia", {})
            projeto["tipologia"] = tipologia_data.get("tipologia", "Desconhecido")

            area_atuacao_data = tipologia_data.get("tb_area_atuacao", {})
            projeto["area_atuacao"] = area_atuacao_data.get("area_atuacao", "Não informado") 

            del projeto["tb_tipologia"]                       
            
            # Buscar disciplinas vinculadas
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

def on_change():
    st.session_state.tipologia_opcoes = lista_opcoes_tipologia(st.session_state.area_atuacao)

if "tipologia_opcoes" not in st.session_state:
    st.session_state.tipologia_opcoes = [""]

if "projetos" not in st.session_state:
    st.session_state.projetos = [""]

if "recarregar" in st.session_state and st.session_state.recarregar:
    st.cache_data.clear()
    st.session_state.recarregar = False


col76, col77, col78 = st.columns([0.4, 0.4, 0.2])

with col76:
    st.subheader("Projetos Cadastrados")

st.write("")

col1, col2, col3, col4, col5 = st.columns([0.15, 0.20, 0.25, 0.25, 0.15])

# Filtros interligados
### área, tipologia, Nome, valor (range de valores), modelo ###
opcoes_area_atuacao = consultar_banco_dados("tb_area_atuacao", "area_atuacao")

with col1:
# Filtros com opções cadastradas no banco
    area_atuacao = st.selectbox(
        "Área de atuação",                        
        [""] + sorted(opcoes_area_atuacao),
        key="area_atuacao",                               
        placeholder="Selecione a área de atuação",
        on_change=on_change  # Atualiza a lista de tipologia ao mudar
    )

with col2:
    tipologia = st.selectbox("Tipologia",
        [""] + sorted(st.session_state.tipologia_opcoes),
        key="tipologia",        
        placeholder="Selecione a tipologia")
    
with col3:
    nome_projeto = st.selectbox(
        "Nome do Projeto",
        [""] + obter_opcoes_filtro("tb_projetos","nome_projeto", area_atuacao=area_atuacao if area_atuacao else None, tipologia=tipologia if tipologia else None)
        )

with col4:
    modelo = st.selectbox(
        "Modelo",
        [""] + obter_opcoes_filtro("tb_projetos","modelo", area_atuacao=area_atuacao if area_atuacao else None, tipologia=tipologia if tipologia else None)
        )
    

with col5:

    lista_valores_orcamento = obter_opcoes_filtro("tb_projetos", "valor_orcamento", area_atuacao=None, tipologia=None, nome_projeto=None, modelo= None)
    lista_valores_orcamento.sort(reverse=True)

    max_value=lista_valores_orcamento[0] if lista_valores_orcamento else 1,

    valor_orcamento_min, valor_orcamento_max = st.slider(
        "Valor do Orçamento",
        min_value=0,
        max_value=10000000,    
        value=(0, 10000000),    
        step=1000,
        format="R$ %d") 


projetos=obter_projetos_filtrados(area_atuacao or None, tipologia or None, nome_projeto or None, modelo or None, valor_orcamento_min, valor_orcamento_max)

## TESTE DE MÉTRICA (CARTÃO) ###
with col77:    
    st.metric(
        label="Total de Projetos",
        value=len(projetos) if projetos else 0,        
        label_visibility="visible"
    )

with col78:    
    df = pd.DataFrame(projetos)
    if df.empty:
        valor_cartao = 0
    else:
        df_valor_orcamento =df["valor_orcamento"]
        df_valor_orcamento = df_valor_orcamento.dropna()
        media_valor_orcamento = df_valor_orcamento.mean()
        desvio_padrao_valor_orcamento = df_valor_orcamento.std()
        st.metric(
            label="Média de Valor do Orçamento",
            value=f"R$ {media_valor_orcamento:,.2f}",
            delta=f"± {desvio_padrao_valor_orcamento:,.2f}",
            help="Média e desvio padrão dos valores de orçamento"
    )



# Definição de colunas a serem exibidas e seus nomes personalizados
colunas_exibir = {
    "id_clickup": "ID ClickUp",
    "nome_projeto": "Nome do Projeto",
    "contrato": "Contratante", 
    "area_atuacao":"Área de Atuação",
    "tipologia": "Tipologia",   
    "modelo": "Modelo",
    "area": "Área (m²)",
    "valor_orcamento": "Valor do Orçamento",
    "dt_ref_orcamento": "Data de Referência do Orçamento",
    "caminho_rede": "Caminho de rede", 
    "disciplinas": "Disciplinas",
    "valor_medicao": "Valor da Medição",
    "anexo_3d": "Anexo 3D",
    "anexo_planta":"Anexo planta" 
}

# Exibição dos projetos

if isinstance(projetos, dict) and "erro" in projetos:
    valor_cartao = 0
    st.error(projetos["erro"])
elif projetos:
    df = pd.DataFrame(projetos)    
    df = df[list(colunas_exibir.keys())]  # Exibir apenas colunas selecionadas
    df.rename(columns=colunas_exibir, inplace=True)  # Renomear colunas para exibição
    st.write("")
    df_original = df

    df_editado = st.data_editor(df,hide_index=True)

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
    st.info("ℹ️  Nenhum projeto encontrado.")