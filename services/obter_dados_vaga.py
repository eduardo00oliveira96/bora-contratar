import sqlite3
from pprint import pprint


conn = sqlite3.connect("bd_bora_contratar.db")

cursor = conn.cursor()

def obter_dados_vaga(id_vaga):
    dados = cursor.execute("""
               select 
               v.titulo,
               v.descricao,
               v.local_trabalho,
               v.contrato_trabalho,
               v.requisitos,
               v.habilidades,
               v.salario
               from vagas v
               where v.id = ?
               """, (id_vaga,))
    resumo = [
        {
            "titulo": vaga[0],
            "descricao": vaga[1],
            "local_trabalho": vaga[2],
            "contrato_trabalho": vaga[3],
            "requisitos": vaga[4],
            "habilidades": vaga[5],
            "salario": vaga[6]
        }
        for vaga in dados.fetchall()
    ]
        
    resumo_vaga = {"resumo_vaga": resumo[0]}
        
        
    return resumo_vaga

if __name__ == "__main__":
    pprint(obter_dados_vaga(1))