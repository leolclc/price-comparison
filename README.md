# FarmaCompare 💊

Sistema de comparação de preços de farmácias com foco inicial em **Belo Horizonte / MG**, comparando:
* **Araujo**
* **Pague Menos**
* **Drogaria Raia**
* **Drogaria Pacheco**
* **Drogasil**

O sistema coleta preços em segundo plano via **Collector**, armazena as ofertas e produtos no **PostgreSQL**, e disponibiliza uma API REST rápida em **FastAPI** consultada por um frontend em **React + TypeScript + Vite**. Araujo e Drogaria Raia usam Chromium via Playwright para renderizar as páginas de busca.

---

## 🏗️ Arquitetura

```text
                    ┌─────────────────────┐
                    │   React Frontend    │ (Vite / TanStack Query)
                    └──────────┬──────────┘
                               │ REST
                    ┌──────────▼──────────┐
                    │     FastAPI API     │ (SQLAlchemy Async / Pydantic)
                    └──────────┬──────────┘
                               │
                         PostgreSQL
                               ▲
                               │
                    ┌──────────┴──────────┐
                    │      Collector      │ (APScheduler / httpx / bs4)
                    │  Araujo             │
                    │  Pague Menos        │
                    │  Raia               │
                    │  Pacheco            │
                    └─────────────────────┘
```

> ⚠️ **A API e o frontend nunca fazem scraping síncrono durante a consulta do usuário**. As buscas consultam exclusivamente a base de dados consolidada.

---

## 🚀 Como Executar com Docker Compose

O collector usa Chromium headless por padrão (`COLLECTOR_BROWSER_HEADLESS=true`). No GitHub Actions, o workflow abre o Chromium em modo gráfico numa tela virtual Xvfb, como na execução local com interface gráfica.

Para que a coleta agendada use os termos e grave resultados no banco da aplicação, configure o secret `DATABASE_URL` no repositório com a URL PostgreSQL acessível pelo GitHub Actions. Sem esse secret, o workflow usa um SQLite temporário apenas para CI.

### 1. Pré-requisitos
* Docker e Docker Compose instalados.

### 2. Iniciar todos os serviços

Na raiz do projeto (`farmacompare`):

```bash
docker compose up --build
```

Isso subirá:
1. **PostgreSQL** (`port 5432`) com o seed inicial de farmácias e termos (`database/init.sql`)
2. **Backend FastAPI** (`http://localhost:8000`), executando automaticamente as migrations do Alembic no boot
3. **Collector**, executando o ciclo inicial de coleta e agendando ciclos futuros via APScheduler
4. **Frontend React** (`http://localhost:3000`), servido via Nginx com proxy reverso configurado para a API

---

## 🧪 Executando os Testes Automatizados

Os testes são **100% autônomos e estáticos**: utilizam fixtures salvas e banco SQLite em memória, sem depender da internet.

### Testes do Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
pytest -v
```

### Testes do Collector (Providers e Matching)
```bash
cd collector
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
pytest -v
```

---

## 📡 Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Healthcheck do serviço |
| `GET` | `/api/pharmacies` | Lista de farmácias ativas |
| `GET` | `/api/products/search?q=dipirona` | Busca de produtos e ofertas agrupadas |
| `GET` | `/api/products/{id}` | Detalhes do produto |
| `GET` | `/api/products/{id}/history` | Histórico de variação de preços |
| `GET` | `/api/search-terms` | Termos de busca e contadores de demanda |
| `GET` | `/docs` | Documentação interativa Swagger/OpenAPI |

---

## 🎯 Regras de Matching

O matching de produtos entre farmácias é **conservador**:
1. **EAN/GTIN**: Quando disponível em ambos os produtos, é a chave prioritária (EANs idênticos = mesmo produto; EANs distintos = produtos diferentes).
2. **Discriminação de Dosagem**: `500mg` e `1g` **nunca** são agrupados como o mesmo produto.
3. **Discriminação de Quantidade**: `10 comprimidos` e `20 comprimidos` **nunca** são agrupados.
4. **Atributos + Princípio Ativo**: Se não houver EAN, agrupa por princípio ativo + dosagem + quantidade + marca.
