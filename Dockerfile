# syntax=docker/dockerfile:1
#
# Build a partir do diretório PAI (Projetos), para que a biblioteca local
# `baltazar` (pasta irmã) entre no contexto. Veja docker-compose.yml.
#
#   docker compose up --build
#
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app/diagnostico

# 1) Dependências primeiro (camada cacheável enquanto requirements não muda).
#    - pywin32 é ignorado no Linux pelo marker `sys_platform == 'win32'`.
#    - A linha do baltazar (git+) é removida: no Docker usamos a cópia local
#      via PYTHONPATH (passo 2), sem depender do repositório estar pushado.
COPY diagnostico/requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && grep -vi '^baltazar' requirements.txt > requirements.docker.txt \
    && pip install -r requirements.docker.txt

# 2) Biblioteca local baltazar — fica importável via PYTHONPATH=/app
#    (não precisa de pip install; evita o `where=['..']` do pyproject).
COPY baltazar/ /app/baltazar/

# 3) Código da aplicação.
COPY diagnostico/ /app/diagnostico/

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').status==200 else 1)" || exit 1

CMD ["streamlit", "run", "frontend/main.py", \
     "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
