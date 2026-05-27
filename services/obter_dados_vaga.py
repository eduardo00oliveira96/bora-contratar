from models.vaga import get_vaga_by_id

def obter_dados_vaga(id_vaga):
    vaga = get_vaga_by_id(id_vaga)
    if not vaga:
        return {"resumo_vaga": {}}
    resumo_vaga = {
        "resumo_vaga": {
            "titulo": vaga.get("titulo", ""),
            "descricao": vaga.get("descricao", ""),
            "local_trabalho": vaga.get("local_trabalho", ""),
            "contrato_trabalho": vaga.get("tipo_contrato", ""),
            "requisitos": vaga.get("requisitos", ""),
            "habilidades": vaga.get("habilidades", ""),
            "salario": vaga.get("salario"),
        }
    }
    return resumo_vaga
