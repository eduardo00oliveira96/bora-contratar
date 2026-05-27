import sys
import json
from pathlib import Path
import os
from pydantic import BaseModel, Field
from typing import List, Literal
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openrouter import OpenRouter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from services.obter_dados_vaga import obter_dados_vaga
from ai.prompt_avaliar_cv import prompt_avaliar_cv
from models.candidatura import update_candidatura_ai_eval

load_dotenv()


class AvaliacaoCV(BaseModel):
    nota: int = Field(..., description="Nota final de 0 a 100", ge=0, le=100)
    analise_detalhada: str = Field(default_factory=str, max_length=1000)
    pontos_fortes: List[str] = Field(default_factory=list, max_length=20)
    gaps_atencao: List[str] = Field(default_factory=list, max_length=20)
    recomendacao: Literal["Entrevistar", "Banco de talentos", "Não Prosseguir"] = Field(...)
    tags_extraidas: List[str] = Field(default_factory=list, max_length=30)


def avaliar_cv(texto_cv: str, dados_vaga: dict, candidatura_id: int) -> AvaliacaoCV:
    resposta = None
    try:
        agente_recrutamento = Agent(
            name="Agente de Recrutamento",
            model=OpenRouter('google/gemini-2.5-flash-lite'),
            system_message=prompt_avaliar_cv(),
            output_schema=AvaliacaoCV,
            use_json_mode=True
        )

        mensagem_usuario = f"""
        AVALIAÇÃO DE CANDIDATO PARA VAGA
        ## DADOS DA VAGA:
        {dados_vaga}
        ## CV DO CANDIDATO:
        {texto_cv}
        """

        processamento = agente_recrutamento.run(input=mensagem_usuario)
        resposta: AvaliacaoCV = processamento.content
        return resposta

    except Exception as e:
        print("Erro ao avaliar CV:", e)
        return None

    finally:
        if resposta:
            try:
                update_candidatura_ai_eval(
                    candidatura_id,
                    resposta.nota,
                    resposta.analise_detalhada,
                    str(resposta.pontos_fortes),
                    str(resposta.gaps_atencao),
                    resposta.recomendacao,
                    str(resposta.tags_extraidas)
                )
            except Exception as db_err:
                print(f"Erro ao atualizar banco: {db_err}")


if __name__ == "__main__":
    texto_cv = "..."  # (example CV omitted for brevity)
    dados_vaga = obter_dados_vaga(1)
    resultado = avaliar_cv(texto_cv, dados_vaga, candidatura_id="some-uuid")
    if resultado:
        print(resultado.nota)
