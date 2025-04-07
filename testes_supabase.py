from conexao_supabase import supabase

area_atuacao = "Saúde"
tipologia = "CRAS"
nome_projeto = None

query_area_atuacao = (
supabase.table("tb_area_atuacao")
.select("id")        
)

if area_atuacao != "":
    query_area_atuacao = query_area_atuacao.eq("area_atuacao", area_atuacao).execute()    

    if query_area_atuacao.data:
        
        area_atuacao_id = query_area_atuacao.data[0]["id"]                        
        query_tipologia = supabase.table("tb_tipologia").select("tipologia").eq("frk_id_area_atuacao", area_atuacao_id).execute()

        if query_tipologia.data:
            lista = list(set(d["tipologia"] for d in query_tipologia.data if d["tipologia"] is not None))
            lista  = sorted(lista) if lista else ["Nenhuma tipologia disponível"]
        else:
            lista = []
else:
    lista = []

"""Obtém a lista de projetos com disciplinas aplicadas, filtrando conforme necessário."""
try:
    query = (
        supabase.table("tb_projetos")
        .select("*, tb_tipologia!inner(tipologia, frk_id_area_atuacao, tb_area_atuacao!inner(area_atuacao))")
    )

    if area_atuacao:
        query = query.eq("area_atuacao", area_atuacao)
    if tipologia:
        query = query.ilike("tipologia", f"%{tipologia}%")    
    
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
            
 
except Exception as e:
    {"erro": str(e)}