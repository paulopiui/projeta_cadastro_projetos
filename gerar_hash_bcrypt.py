import bcrypt

def gerar_hash(senha):
    hash_gerado = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    print("Hash gerado:")
    print(hash_gerado)

if __name__ == "__main__":
    senha = input("Digite a senha: ")
    gerar_hash(senha)