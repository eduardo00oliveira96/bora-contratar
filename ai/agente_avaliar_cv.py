import sys
import logging
import os
from pydantic import BaseModel, Field, ValidationError
from typing import List, Literal
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openrouter import OpenRouter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from services.obter_dados_vaga import obter_dados_vaga
from ai.prompt_avaliar_cv import prompt_avaliar_cv
from models.candidatura import update_candidatura_ai_eval, update_candidatura_erro

load_dotenv()

logger = logging.getLogger(__name__)


class AvaliacaoCV(BaseModel):
    nota: int = Field(..., description="Nota final de 0 a 100", ge=0, le=100)
    analise_detalhada: str = Field(default_factory=str, max_length=1000)
    pontos_fortes: List[str] = Field(default_factory=list, max_length=20)
    gaps_atencao: List[str] = Field(default_factory=list, max_length=20)
    recomendacao: Literal["Entrevistar", "Banco de talentos", "Não Prosseguir"] = Field(...)
    tags_extraidas: List[str] = Field(default_factory=list, max_length=30)


def avaliar_cv(texto_cv: str, dados_vaga: dict, candidatura_id: int) -> bool:
    if not texto_cv or not texto_cv.strip():
        logger.warning(f"Texto do CV vazio para candidatura {candidatura_id}")
        update_candidatura_erro(candidatura_id, "CV sem texto extraído para avaliação.")
        return False

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
        resposta = processamento.content

        if not isinstance(resposta, AvaliacaoCV):
            raise ValueError(f"Resposta inesperada da IA: {type(resposta).__name__}")

        update_candidatura_ai_eval(
            candidatura_id,
            resposta.nota,
            resposta.analise_detalhada,
            str(resposta.pontos_fortes),
            str(resposta.gaps_atencao),
            resposta.recomendacao,
            str(resposta.tags_extraidas)
        )
        logger.info(f"Candidatura {candidatura_id} avaliada: nota {resposta.nota}, recomendação {resposta.recomendacao}")
        return True

    except ValidationError as e:
        erro = f"Resposta da IA não seguiu o schema esperado: {e}"
        logger.error(f"Erro de validação na candidatura {candidatura_id}: {e}")
        update_candidatura_erro(candidatura_id, erro)
        return False
    except Exception as e:
        erro = f"Erro ao avaliar CV: {e}"
        logger.error(f"Erro na avaliação da candidatura {candidatura_id}: {e}", exc_info=True)
        update_candidatura_erro(candidatura_id, erro)
        return False


if __name__ == "__main__":
    texto_cv = "..."  # (example CV omitted for brevity)
    dados_vaga = obter_dados_vaga(1)
    sucesso = avaliar_cv(texto_cv, dados_vaga, candidatura_id="some-uuid")
    print(f"Avaliação concluída: {sucesso}")
