from conexao_supabase import supabase
import pandas as pd

area_atuacao = "Saúde"

query = (
    supabase.table("tb_tipologia")
    .select("tipologia, frk_id_area_atuacao, tb_area_atuacao!inner(area_atuacao)")
.execute())

df = pd.DataFrame(query.data)
df = pd.concat([df.drop(['tb_area_atuacao'], axis=1), pd.json_normalize(df['tb_area_atuacao'])], axis=1)
df = df.rename(columns={"tb_area_atuacao": "area_atuacao"})


filtered_df = df[df['area_atuacao'] == area_atuacao]
tipologia_list = filtered_df['tipologia'].tolist()

print(tipologia_list)