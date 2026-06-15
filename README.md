# Gestão de Diagnósticos de Projetos de Data Science

Aplicação Streamlit para registrar entrevistas de diagnóstico com clientes,
acompanhar o status de projetos de Data Science ao longo do pipeline e enviar
e-mails automáticos de atualização via Outlook.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | Streamlit |
| ORM | SQLAlchemy 2.x **async** (asyncpg) |
| Banco | PostgreSQL no **Neon** |
| Migrações | Alembic (env.py async) |
| Config | pydantic-settings (lê `.env`) |
| Visualizações | Plotly, streamlit-echarts, [baltazar](../baltazar) |
| E-mail | pywin32 (Outlook COM — Windows) |

## Arquitetura

```
backend/
├── config.py        # pydantic-settings (DATABASE_URL via .env)
├── database.py      # engine async + async_session (Neon/asyncpg)
├── async_runner.py  # ponte async↔Streamlit (event loop dedicado em thread)
├── models.py        # Cliente, Produto, Projeto, Area, Cargo, ProjetoSkill, ProjetoEmail, Histórico, Validação
├── repositories.py  # Repository async (eager loading)
├── normalizacao.py  # normalização de area/cargo/empresa/skills/emails
├── emails.py        # envio via Outlook COM
└── db/alembic/      # migrações (env.py async)

frontend/
├── main.py          # orquestrador fino: contexto + navegação + dispatch
├── servicos.py      # AppContext + runner/repos/dados cacheados
├── filtros.py       # sidebar de filtros → df_filtrado
├── paginas/         # uma seção por módulo (render(ctx))
│   ├── dashboard.py
│   ├── diagnostico.py
│   ├── gerenciar_projetos.py
│   ├── gerenciar_clientes.py
│   └── gerenciar_produtos.py
└── utils/           # transformadores (DataFrames) e gráficos
```

### Por que `async_runner`?

O Streamlit é síncrono e re-executa o script a cada interação; o asyncpg amarra
conexões ao event loop que as criou. O `AsyncRunner` mantém **um** event loop
vivo numa thread de fundo (cacheado via `@st.cache_resource`) e todas as
coroutines são submetidas a ele, preservando o pool de conexões entre reruns.

## Setup

1. **Criar o `.env`** na raiz com a conexão do Neon (formato asyncpg):

   ```
   DATABASE_URL=postgresql+asyncpg://USUARIO:SENHA@HOST-pooler.../neondb?ssl=require
   DEBUG=False
   ```

   > O pooler do Neon (PgBouncer) exige `statement_cache_size=0`, já configurado
   > no `database.py` e no `env.py`.

2. **Criar o ambiente e instalar dependências:**

   ```bash
   python -m venv myenv
   myenv\Scripts\activate
   pip install -r requirements.txt
   pip install -e "<caminho>\Projetos\baltazar"
   ```

3. **Rodar o app:**

   ```bash
   streamlit run frontend/main.py
   ```

## Funcionalidades

- **Dashboard:** KPIs (Total, Taxa de Conclusão, Tempo Médio de Entrega/cycle
  time, Concluídos, Abertos, Clientes), rosca de status, barras por tipo,
  heatmap de habilidades × tipo, calendário de tarefas, funil do pipeline,
  velocímetro e nuvem de habilidades.
- **Diagnóstico:** formulário de 16 perguntas em blocos (Contexto & Objetivo,
  Situação Atual, Definição de Sucesso, Dados, Stakeholders & Restrições).
- **Gerenciar Projetos:** busca, paginação, export CSV/Excel, edição de status
  (com e-mail automático), skills, e-mails adicionais e ciclos de validação.
- **Gerenciar Clientes / Produtos.**

## Docker

A solução é dockerizada. Como o `baltazar` é uma biblioteca local numa pasta
**irmã**, o build usa o **diretório pai** (`Projetos`) como contexto — já
configurado no `docker-compose.yml`. Requer Docker com BuildKit (Docker Desktop
moderno já vem com ele).

```bash
# a partir da pasta diagnostico/, com o .env preenchido:
docker compose up --build
```

App em **http://localhost:8501**.

Detalhes:
- **Banco:** o container conecta no **Neon** via `DATABASE_URL` do `.env`
  (injetado como variável de ambiente em runtime — não vai para a imagem).
- **baltazar:** copiado para `/app/baltazar` e importável via `PYTHONPATH=/app`.
- **E-mail (Outlook/pywin32):** é **Windows-only** e **não funciona no container
  Linux**. O `emails.py` faz import lazy do pywin32, então o app roda normal no
  Docker; apenas o envio de e-mail de atualização de status não acontece lá
  dentro (no Windows nativo continua funcionando).
- O `Dockerfile.dockerignore` mantém o contexto enxuto (exclui `myenv`, `.git`,
  `.env`, demais projetos da pasta pai).

## Deploy no Streamlit Community Cloud

1. **Suba os dois repositórios no GitHub:**
   - `diagnostico` (esta app)
   - `baltazar` (a biblioteca) — o `requirements.txt` a instala via
     `git+https://github.com/.../baltazar.git@main`, então ela **precisa estar
     pushada** (e o pyproject já está corrigido para `pip install`).

2. **No Streamlit Cloud**, aponte para `frontend/main.py` e configure os
   **Secrets** (App settings → Secrets) com o conteúdo de
   [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example):

   ```toml
   DATABASE_URL = "postgresql+asyncpg://USUARIO:SENHA@HOST-pooler.../neondb?ssl=require"
   DEBUG = false
   ```

   O `config.py` lê o `DATABASE_URL` do ambiente, do `.env` ou do `st.secrets`
   (nessa ordem), então funciona no Cloud sem `.env`.

3. **Banco:** é o **mesmo Neon** de dev/Docker — rodar local, no Docker ou no
   Cloud usa a mesma base (a `DATABASE_URL` é a fonte única da verdade).

> **E-mail (Outlook/pywin32):** não funciona no Cloud (Linux). O app roda
> normal; só o envio de e-mail de status não acontece — igual no Docker.

## Migrações (Alembic)

```bash
alembic -c backend/db/alembic.ini revision --autogenerate -m "descricao"
alembic -c backend/db/alembic.ini upgrade head
```

> As migrações da era SQLite ficam em `backend/db/alembic/_archived_sqlite_versions/`.

## Notas

- O schema é **normalizado**: `skills`/`emails_adicionais` são tabelas filhas
  (não strings delimitadas); `area`/`cargo` são tabelas lookup.
- `prazo_desejado` é um campo `Date` estruturado (habilita análises de prazo).
- Mudanças no **baltazar** exigem reiniciar o Streamlit (lib externa não recarrega no hot-reload).
