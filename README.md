# Bora Contratar

🤖 Avaliador de currículos com IA para PMEs. Open Source, 100% Python, Flask + Agno + Supabase + PostgreSQL + Docker.

---

## Visão Geral

O **Bora Contratar** é uma aplicação web que automatiza a avaliação de currículos usando inteligência artificial. Projetado para pequenas e médias empresas, o sistema permite que gestores de RH façam upload de currículos (PDF), configurem vagas com requisitos específicos e recebam análises automatizadas com notas, pontos fortes e recomendações de fit — tudo via uma interface intuitiva.

### Funcionalidades Principais

- **Upload e parsing de currículos** — Extração automática de texto de PDFs usando PyMuPDF
- **Avaliação com IA** — Análise de fit entre currículo e vaga usando Agno + OpenAI
- **Interface com sidebar colapsável** — Grupos expansíveis para navegação fluida entre vagas e candidatos
- **Fluxo de entrevistas** — Gerenciamento de etapas com `avancar_etapa()` e popup de agendamento RH→Manager
- **Autenticação via Supabase** — Login seguro com PyJWT para gestão de sessão
- **Sistema de notificações** — Alertas in-app e email para gestores, RH e aprovadores
- **Rate limiting** — Controle de requisições via Flask-Limiter
- **Formulários protegidos** — CSRF token via Flask-WTF

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| **Backend** | Flask 3.1+ (Python ≥ 3.11) |
| **Templates** | Jinja2 (HTML server-side rendering) |
| **IA** | Agno 2.5+ + OpenAI API |
| **Banco de Dados** | PostgreSQL via Supabase |
| **Upload de PDFs** | PyMuPDF |
| **Autenticação** | PyJWT + Supabase Auth |
| **Proteção** | Flask-Limiter (rate limiting) + Flask-WTF (CSRF) |
| **Variáveis de Ambiente** | python-dotenv |
| **Gerenciamento de Deps** | UV |
| **Containerização** | Docker |

---

## Pré-requisitos

- Python ≥ 3.11
- [UV](https://docs.astral.sh/uv/) (gerenciador de pacotes)
- Docker (opcional, para containerização)
- Conta [Supabase](https://supabase.com/) com projeto configurado
- Chave de API [OpenAI](https://platform.openai.com/)

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/bora-contratar.git
cd bora-contratar
```

### 2. Instale as dependências com UV

```bash
uv sync
```

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon

# OpenAI
OPENAI_API_KEY=sk-sua-chave

# JWT
JWT_SECRET=sua-chave-secreta

# Flask
FLASK_SECRET_KEY=sua-chave-secreta-flask
FLASK_DEBUG=true
```

### 4. Execute a aplicação

```bash
uv run python app.py
```

A aplicação estará disponível em `http://localhost:5000`.

### Com Docker

```bash
docker build -t bora-contratar .
docker run -p 5000:5000 --env-file .env bora-contratar
```

---

## Estrutura do Projeto

```
bora-contratar/
├── app.py                  # Entry point da aplicação Flask
├── pyproject.toml          # Configuração do projeto e dependências
├── uv.lock                 # Lockfile do UV
├── routes/                 # Rotas Flask (endpoints)
├── models/                 # Modelos e lógica de negócio
├── templates/              # Templates Jinja2 (HTML)
├── static/                 # Assets estáticos (CSS, JS, imagens)
├── ai/                     # Módulo de IA (Agno + OpenAI)
├── services/               # Serviços da aplicação
├── database/               # Configuração e migrações de banco
├── supabase/               # Integração com Supabase
├── scripts/                # Scripts utilitários
├── src/                    # Código-fonte auxiliar
├── docs/                   # Documentação adicional
├── upload_curriculos/      # Diretório de uploads de currículos
└── LICENSE                 # Licença do projeto
```

---

## Como Funciona

1. **Cadastro/Login** — O usuário se autentica via Supabase Auth
2. **Criação de Vaga** — O gestor define título, descrição, requisitos e peso de cada critério
3. **Upload de Currículos** — RH faz upload de PDFs dos candidatos
4. **Avaliação com IA** — O sistema analisa cada currículo contra a vaga usando Agno + OpenAI
5. **Resultado** — Nota de fit, pontos fortes, pontos de atenção e recomendação final
6. **Próximos Passos** — Agendamento de entrevistas via popup integrado

---

## Licença

Este projeto é Open Source. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## Contribuindo

Contribuições são bem-vindas! Abra uma issue ou envie um pull request.
