import sqlite3
import sys
import json
from pathlib import Path
import os
from pydantic import BaseModel
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from pprint import pprint
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Adiciona a raiz ao sys.path se ainda não estiver
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
from services.obter_dados_vaga import obter_dados_vaga
from .prompt_avaliar_cv import prompt_avaliar_cv

DB_PATH = "database/bd_bora_contratar.db"

conn = sqlite3.connect(os.path.join(BASE_DIR, DB_PATH), check_same_thread=False)
cursor = conn.cursor()

load_dotenv()

from pydantic import BaseModel, Field
from typing import Dict, List, Literal

class AvaliacaoCV(BaseModel):
    """
    Schema de saída para avaliação estruturada de um candidato.
    Usado como output_schema do Agente de Recrutamento.
    """
    
    nota: int = Field(
        ...,
        description="Nota final de 0 a 100 que resume o fit do candidato com a vaga.",
        ge=0,
        le=100,
        
    )
    
    analise_detalhada: str = Field(
        default_factory=str,
        description="Análise qualitativa detalhada do candidato em relação à vaga.",
        max_length=1000
    )
    
    pontos_fortes: List[str] = Field(
        default_factory=list,
        description="Lista de pontos positivos do candidato em relação à vaga.",
        max_length=20
    )
    
    gaps_atencao: List[str] = Field(
        default_factory=list,
        description="Lista de lacunas ou pontos de atenção identificados no CV em relação à vaga.",
        max_length=20
    )
    
    recomendacao: Literal[
        "Entrevistar",
        "Banco de talentos",
        "Não Prosseguir"
    ] = Field(
        ...,
        description="Decisão final baseada na nota e análise: 'Entrevistar' (nota >= 70), 'Banco de talentos' (nota 50-69), 'Não Prosseguir' (nota < 50)",
        max_length=20
    )
    
    tags_extraidas: List[str] = Field(
        default_factory=list,
        description="Lista de palavras-chave técnicas e comportamentais extraídas do CV.",
        max_length=30
    )



def avaliar_cv(texto_cv: str, dados_vaga: dict, vaga_id: int) -> AvaliacaoCV:
    reposta = None # Inicializa para evitar erro no finally
    
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
        reposta: AvaliacaoCV = processamento.content
        return reposta

    except Exception as e:
        print("Erro ao avaliar CV:", e)
        # Opcional: criar um objeto de fallback para não quebrar o banco
        return None
        
    finally:
        # Só executa o update se a resposta da IA foi gerada com sucesso
        if reposta:
            try:
                cursor.execute("""
                    UPDATE candidaturas SET 
                        status = 'Avaliado',
                        nota = ?,
                        analise_detalhada = ?,
                        pontos_fortes = ?,
                        gaps_atencao = ?,
                        recomendacao = ?,
                        tags = ?,
                        etapa_entrevista = ?
                    WHERE vaga_id = ? 
                """, (
                    reposta.nota,
                    reposta.analise_detalhada,
                    str(reposta.pontos_fortes),
                    str(reposta.gaps_atencao),
                    reposta.recomendacao,
                    str(reposta.tags_extraidas),
                    "Pré Análise com IA",
                    vaga_id # Certifique-se que o nome da coluna é vaga_id ou id
                ))
                conn.commit()
            except sqlite3.Error as db_err:
                print(f"Erro ao atualizar banco: {db_err}")
        
        
        

if __name__ == "__main__":
    # Exemplo de uso
    texto_cv = """
    Francisco Eduardo Lira de Oliveira
Brasileiro, Solteiro, 29 anos | CNH: A (veículo próprio)
Endereço: Rua Luiza Pinheiro Nº 128, Bairro Tapuio, Aquiraz, CEP: 61.700-000
Cel: (85) 9 8124-3269 / (85) 9 9160-0719 |
E-mail: eduardosmolk9@hotmail.com
LinkedIn: https://www.linkedin.com/in/eduardo-oliveira-44b037148/
Resumo Profissional
Profissional com sólida experiência em Engenharia de Produção e especialização em
Engenharia de Software, com foco em automação de processos, inteligência artificial e
desenvolvimento de soluções na Microsoft Power Platform. Possuo uma trajetória
comprovada na otimização de operações, implementação de metodologias ágeis e criação de
agentes de IA para impulsionar a eficiência e a inovação em ambientes industriais e de
serviços. Busco aplicar minha expertise para desenvolver soluções tecnológicas que gerem
impacto e resultados tangíveis.
Formação Acadêmica
● Pós-graduação em Engenharia de Software | Descomplica
● Bacharelado em Engenharia de Produção | Unip
Experiência Profissional
Desenvolvedor de Tecnologia e Inovação
Têxtil Bezerra de Menezes | Setembro de 2025 – Presente
● Desenvolvimento e implementação de automações de processos para ganho de
eficiência operacional.
● Criação e aplicação de agentes de Inteligência Artificial em cenários de negócio.
● Pesquisa e adoção de tecnologias emergentes, propondo e acompanhando POCs e
MVPs.
● Desenvolvimento de soluções no ecossistema Microsoft Power Platform (Power Apps,
Power Automate).
● Gerenciamento de containers para padronização e escalabilidade de aplicações.
● Modelagem de dados e construção de consultas SQL para suporte a sistemas e
análises.
Analista de Processos
Têxtil Bezerra de Menezes | Setembro de 2024 – Setembro de 2025
● Colaboração na definição de políticas e procedimentos organizacionais, garantindo
conformidade e padronização.
● Condução de análises de desempenho de processos, utilizando ferramentas de
simulação e indicadores para identificar e corrigir gargalos.
● Gestão de projetos e implementação de metodologias ágeis, promovendo entregas
consistentes.
● Desenvolvimento e implementação de agentes de inteligência artificial utilizando a
plataforma Copilot Studio.
● Criação e otimização de soluções digitais na Power Platform (Power Apps, Power BI,
Power Automate).
Carmel Hotéis
Junho de 2023 – Setembro de 2024
● Analista de Planejamento da Qualidade | Janeiro de 2024 – Setembro de 2024
● Analista de Qualidade | Junho de 2023 – Janeiro de 2024
Principais Responsabilidades e Conquistas:
● Manutenção da conformidade dos serviços e padrões de qualidade (ISO 9001),
monitorando processos e procedimentos.
● Realização de auditorias internas da qualidade baseadas na ISO 9001, identificando
melhorias e implementando ações corretivas.
● Acompanhamento de não conformidades e suas tratativas, investigando causas raízes
e propondo soluções.
● Elaboração de mapas de processos, riscos e fluxogramas, identificando riscos
potenciais e desenvolvendo estratégias de mitigação.
● Desenvolvimento de soluções utilizando Power BI para criação de relatórios gerenciais
e painéis de controle.
● Implementação de sistemas internos utilizando FlutterFlow, criando interfaces intuitivas
e funcionais.
● Acompanhamento de indicadores de setores e implementação de planos de ação para
otimização operacional.
Supervisor de PCP/Qualidade
Companhia Têxtil do Brasil | Janeiro de 2023 – Junho de 2023
● Acompanhamento de rotinas da Qualidade e PCP, garantindo padrões e cumprimento
de prazos.
● Análise de produtividade, perdas e desperdícios, identificando oportunidades de
melhoria.
● Implementação de análise de dados com Power BI, movimento 5S e manufatura
enxuta.
Metalix Estruturas Metálicas
Julho de 2021 – Janeiro de 2023
● Assistente de Montagem | Dezembro de 2022 – Janeiro de 2023
● Auxiliar de Automação de Processos | Julho de 2022 – Dezembro de 2022
● Trainee de Engenharia de Produção | Dezembro de 2021 – Julho de 2022
● Estagiário de Engenharia de Produção | Julho de 2021 – Dezembro de 2021
Principais Responsabilidades e Conquistas:
● Elaboração de procedimentos operacionais, instruções de trabalho e métodos de
ensaio.
● Realização de auditorias de processos e mapeamento AS IS/TO BE e SIPOC.
● Implementação de indicadores de desempenho e trabalho padronizado.
● Desenvolvimento de Power BI's e Apps/sistemas internos via Power Platform
(PowerApps, PowerAutomate).
● Criação de automações via Power Automate Desktop e implementação de RPA.
● Auxílio na implementação do movimento 5S e MASP (Método de Análise e Solução de
Problemas).
● Garantia da qualidade das estruturas fabricadas e controle do fluxo de RNC.
● Levantamento e análise de processos para identificar oportunidades de automação.
● Configuração e implementação de fluxos de trabalho automatizados.
● Documentação de processos automatizados e suporte a usuários.
Experiências Anteriores
● Operador I | Teclav – Elis | Março de 2015 – Julho de 2021
● Auxiliar de Produção | Rochetech – Tecnologia em Rochas Ornamentais | Dezembro
de 2014 – Março de 2015
Habilidades Técnicas
● Automação e IA: Microsoft Power Automate, Power Automate Desktop, RPA, Copilot
Studio, Crewai, Agno, Langchain,Pyautogui, Selenium etc…
● Desenvolvimento: Python, Docker, Fastapi, Power Platform, SQL e Streamlit.
● Business Intelligence: Power BI (criação de relatórios e dashboards).
● Gestão de Processos: Metodologias Ágeis, Lean Manufacturing, 5S, MASP, ISO 9001,
Mapeamento de Processos (AS IS, TO BE, SIPOC).
Idiomas
● Português (Nativo)
    """
    dados_vaga = obter_dados_vaga(1)
    
    resultado_avaliacao:AvaliacaoCV = avaliar_cv(texto_cv, dados_vaga)
    
    print(resultado_avaliacao.nota)
    print(resultado_avaliacao.analise_detalhada)
    print(resultado_avaliacao.pontos_fortes)
    print(resultado_avaliacao.gaps_atencao)
    print(resultado_avaliacao.recomendacao)
    