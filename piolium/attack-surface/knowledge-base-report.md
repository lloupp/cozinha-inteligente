# Security Audit Knowledge Base — cozinha-inteligente ("Tem em Casa?")

- **Projeto:** lloupp/cozinha-inteligente
- **Commit de referência:** `24abbe512129f6469cf631b00e18386519a820c4`
- **Data início:** 2026-08-17
- **Escopo adotado:** leve (foco essencial). Fases 1, 3, 4/5, 7, 10.
- **Desvio documentado:** CodeQL CLI e Semgrep **Pro** desativados por decisão do usuário.
  Substituídos por **Bandit 1.9.4 + Semgrep Community 1.173.0 + pip-audit 2.10.1**.
  Essa desviação é registrada aqui e no `final-audit-report.md`.

---

## Advisory Intelligence

Scan de dependências realizado com `pip-audit 2.10.1` (OSV + GitHub Advisory DB).

| Componente | Versão | Status | Observação |
|---|---|---|---|
| Flask | 3.1.3 | ✅ Sem avisos | — |
| Werkzeug | 3.1.8 | ✅ Sem avisos | — |
| gunicorn | 26.0.0 | ✅ Sem avisos | — |
| blinker / click / itsdangerous / jinja2 / markupsafe | transitivas | ✅ Sem avisos | — |

**Ambiente (ruído, do escopo de TI):** o scan ambiental flagrou vulnerabilidades em `pip 24.0`
(PYSEC-2026-196/1795/1796/2875/2876) e `setuptools 79.0.1` (PYSEC-2026-3447). Estes são
*build/dev tooling* do venv, **não** dependências de runtime da aplicação. Não fazem parte da
superfície de ameaça web (um atacante só os atingiria se já tivesse execução local de pip).

### Advisories recentes do stack pesquisadas (Phase 1 + Phase 2)

1. **CVE-2025-47278 / PYSEC-2026-1377** — Flask ≤ 3.1.0: fallback key usado no lugar da
   chave de assinatura atual (sessions). Introduzido em 3.1.0, **fix em 3.1.1**.
   - App usa Flask **3.1.3** → **fora da faixa afetada** (corrigido).
   - **Além disso:** o app **não configura `SECRET_KEY` nem usa sessions/flash/cookies**,
     portanto o código de assinatura vulnerável nem é exercitado. **Não aplicável.**
   - *Bypass check:* a vulnerabilidade exige `SECRET_KEY_FALLBACKS` configurado; não está.
     Sem bypass plausível.

2. **CVE-2025-66221** — Werkzeug < 3.1.4: `safe_join` aceita device names do Windows
   (CON, AUX, PRN, NUL) → path traversal (Windows-only).
   - App usa Werkzeug **3.1.8** → **fora da faixa afetada** (corrigido).
   - **Além disso:** o app roda em **Linux** (Docker `python:3.12-slim`, servidor Linux).
     - As rotas estáticas chamam `send_from_directory("static", "<literal>")` com
       nomes de arquivo **constantes**, não provenientes de input do usuário.
   - *Bypass check:* mesmo em versão vulnerável, exigiria (a) Windows e (b) filename
     user-controlled — nenhuma das duas ocorre. Sem bypass plausível.

**Conclusão Phase 2 (Patch Bypass):** não há patches em vigor para este commit; as due CVEs
estão fora de escopo por versão corrigida + não-uso do código vulnerável. Nada a bypassar.

---

## Component Inventory

Veja `piolium/attack-surface/sbom.json` para o inventário completo.
Resumo: Python 3.11/3.12 (runtime), Flask 3.1.3 + Werkzeug 3.1.8 + gunicorn 26.0.0
(runtime web), `receitas.json` (dados, 150 receitas), frontend vanilla PWA, CI GitHub
Actions (checkout+setup-python+pytest), Docker `python:3.12-slim`.

**Subset security-relevant (runtime atingível por atacante):**
- Flask/Werkzeug — expõe toda a superfície HTTP (`/api/*`, rotas estáticas).
- gunicorn — expõe porta 5000/tcp na internet via Docker.
- `receitas.json` — lido via `json.load` com path fixo (não user-controlled).

---

## Threat Model

- **Tipo:** web app (PWA offline) + API JSON backend.
- **Trust boundary:** browser (cliente, **sem confiança**) ↔ servidor Flask.
- **Autenticação/autorização:** **ausentes**. Toda a API é anônima e pública.
- **Sessões:** **nenhuma** (nada de `session`/`flash`/`SECRET_KEY`). Estado do cliente
  vive apenas em `localStorage` (completamente user-controlled → não confiável).
- **Secrets:** nenhum configurado. Nenhum credential em código.
- **Entrantes atacante:** parâmetros de query (`ingredientes`, `vencendo`, `dietas`,
  `sotenho`) na rota `GET /api/receitas`; upload de foto (stub retorna valores fixos).
- **Trust boundary cruzada?** Não. É single-tenant/single-user. O "atacante" é qualquer
  visitante anônimo; não há fronteira entre usuários. Cross-user não se aplica.

### Attacker-controlled inputs map
| Input | Fonte | Parsing | Sink potencial |
|---|---|---|---|
| `ingredientes` | query string | `request.args.get` → `split(",")` → `normalize()` | matching engine (prefix `startswith`); nunca toca disco/SQL/eval |
| `vencendo` | query string | idem | matching (urgencia) |
| `dietas` | query string | idem | filtro `in` em lista |
| `sotenho` | query string | `== "true"` | flag booleana |
| foto (stub) | `<input type=file>` | nenhum (ignora arquivo) | push fixo de tags |
| `localStorage` | cliente | `JSON.parse` | re-render (sem server roundtrip para isso) |

---

## High-Risk DFD / CFD Slices

```mermaid
flowchart LR
  U[Usuário (browser)] -->|"GET /api/receitas?<input>"| F(Flask /api/receitas)
  F --> P[parse: request.args.get]
  P --> N[normalize(): strip + replace acentos]
  N --> M[engine.calcular_receita loop × 150]
  M --> J[jsonify response]
  J --> U
  subgraph Server
    P;N;M;J
  end
```

**Slice A — Data ingestion (query → matching):** `HTTP query → app.api_receitas → split/normalize → engine.esta_comprado (prefix match) → jsonify`. Sem sinks de execução (não há SQL, eval, subprocess, open() com input do usuário).

**Slice B — Static asset serving:** `HTTP request → send_from_directory("static","<literal>")`. Filename é constante por rota (não user-controlled).

**Slice C — CI/CD + container:** GitHub Actions (checkout/setup-python/pytest) → Docker `python:3.12-slim` → gunicorn como root.

---

## Domain Attack Research

**Tech-stack relevante:** Python Flask (WSGI) — webapp genérica. OWASP Top 10 clássico aplica:
A01 Broken Access Control (ausência de auth aqui é por design — app público), A02 Crypto
Failures (nenhum segredo), A03 Injection (não há SQL/template/eval com user data), A04 Insecure
Design, A05 Security Misconfig (debug=False ✓; Docker root ✗; SEMGREP), A06 Vulnerable &
Outdated Components (checado — Flask/Werkzeug atual), A07 Auth Failures (não aplicável), A08
SSRF (nenhuma chamada outbound do servidor), A09 Logging Failures, A10 SSRF.

**Domínio específico (recipe/meal-planning PWA):**
- Food-recipe apps têm exposto: XSS via nomes de ingredientes/receitas (renderizados no
  cliente — aqui mitigado por `escapeHtml`); scraping de ingredientes "sugeridos" (info
  disclosure de propósito — lista de preços, by design); lógica de matching falha em
  prefixos ("ovo" casa com "ovolo") — correção, não segurança.
- Não há integração com serviços externos (pagamento, entrega, OCR real) — o "OCR da
  geladeira" é um **stub** que injeta ingredientes fixos (`ovo, tomate, queijo, cebola, arroz`),
  eliminando a superfície de upload/imagem real.

---

## Phase 4 CodeQL Extraction Targets

> *Nota de escopo:* CodeQL desativado (escopo leve). Esta seção lista os alvos que
> **teriam** sido extraídos, como contrato para a análise estática realizada com Bandit+Semgrep:

| Slice | Fonte esperada (CodeQL) | Sink esperado | Evidência real |
|---|---|---|---|
| A-query | `RemoteFlowSource` (HTTP query params) | N/A (nenhum sink perigoso) | Bandit 0 / Semgrep 0 em app.py+engine.py |
| A-query | `LocalUserInput` | `jsonify` / `list.append` | Semgrep-custom: nenhum fluxo para eval/exec/subprocess/SQL |
| B-static | `RemoteFlowSource` (path da URL) | `send_from_directory` | Semgrep-custom: path é literal → 0 finding |
| B-static | — | `werkzeug.utils.safe_join` | N/A (literal) |

---

## Static Analysis Summary

| Ferramenta | Escopo | Finding | Severidade | Triagem |
|---|---|---|---|---|
| pip-audit 2.10.1 | Flask/Werkzeug/gunicorn + transitivas | 0 | — | sem avisos |
| Bandit 1.9.4 | app.py, engine.py (185 LOC) | 0 | — | nenhuma |
| Semgrep 1.173.0 (auto, 498 rules) | repo inteira | 3 | 1 ERROR / 2 WARNING | 2 real (Docker/CI), 0 app-code |
| Semgrep custom (3 rules) | app.py, engine.py, app.js | 0 (após refinamento) | — | 9 FP iniciais triados a FALSE POSITIVE |
| agentic-actions-auditor | .github/workflows/ci.yml | 0 | — | sem integração AI agent |

**Regras customizadas criadas em `piolium/semgrep-rules/`** (arquitetura-específicas):
1. `send-from-directory-non-literal-path` — path traversal em `send_from_directory` com arg
   variável. Resultado: **0** (todos os paths são literais → safe).
2. `flask-query-param-flow-to-dangerous-sink` — query param → eval/exec/subprocess/SQL.
   Resultado: **0** (não há esses sinks).
3. `js-innerhtml-unescaped-user-interpolation` — `innerHTML += \`${bareVar}\`` sem escape.
   Resultado: **0** após refinamento (todos os tokens user-data vão por `escapeHtml`).

### Phase 4 — GitHub Actions Audit
Workflow `.github/workflows/ci.yml` executa apenas `pytest`. **Nenhuma integração de AI agent**
(Claude Code Action, Gemini CLI, OpenAI Codex, etc.) → `agentic-actions-auditor`: **clean**.
Aberto como *improvement*: pinar actions a SHAs de commit e adicionar step de segurança.

---

## SAST Enrichment (Phase 5)

Classificação de cada candidato encontrado, pelas 6 perguntas do método:

1. **Dockerfile — `missing USER` (ERROR, L16).**
   1. Quem controla input? Ninguém via HTTP — é configuração de build.
   2. Runtime? Container Docker (gunicorn).
   3. Trust boundary cruzada? Não (build-time / deploy-time).
   4. Cross-user? Não.
   5. Código usado em runtime? Sim (imagem de produção).
   6. Reachable? Sim — é a imagem que roda.
   → Classificação: **security / hardening**. Executar como root aumenta blast radius se o
   container for comprometido (ex.: via outra vuln). Não é exploitable remotamente por si só,
   mas é um achado real de *insecure default*. **Severidade: Medium** (hardening).

2. **CI — tags mutáveis `actions/checkout@v4`, `actions/setup-python@v5` (WARNING).**
   1. Input? Configuração CI.
   2. Runtime? GitHub-hosted runner.
   3. Trust boundary? Supply chain de build.
   4. Cross-user? Não diretamente, mas afeta todos os contribs.
   5. Usado em runtime? Não — é build.
   6. Reachable? Indireto (ataque de supply-chain na ação).
   → Classificação: **security / supply-chain**. Severidade: **Low** (hardening); risco real
   mas de baixa probabilidade/impacto para um projeto open-source deste porte.

3. **9 falsos positivos iniciais de regras customizadas** — todos triados:
   - 6× `send_from_directory` com **literal** → path traversal não aplicável.
   - 3× `innerHTML` com `escapeHtml()` ou número → XSS não aplicável.
   → Todos **FALSE POSITIVE** (regra sobre-ajustada; refinada a 0 finding).

**App-code (app.py/engine.py/app.js): zero findings segurança.** Nenhuma injeção, path
traversal, XSS server-side, SSRF, ou deserialization. O matching usa `startswith` (correção,
não segurança).

---

## CodeQL Structural Analysis

> *CodeQL desativado neste escopo (leve). Substituído por Bandit + Semgrep custom + revisão
> manual de DFD. Esta seção registra a cobertura obtida:* 
> - Entry points mapeados: `/api/receitas`, `/api/ingredientes-sugeridos`, `/api/dietas-validas`,
>   rotas estáticas `/<file>`.
> - Sinks identificados: `jsonify` (safe), `send_from_directory` (literal → safe).
> - Call-graph slices: `api_receitas → split → normalize → esta_comprado → calcular_receita → jsonify`.
>   Nenhum caminho atinge `eval`/`exec`/`open`/`subprocess`/`os.system`.
> - Machine DFD/CFD: ver diagrama acima.

---

## Spec Gap Analysis

## None identified
O projeto não implementa RFCs nem specs formais. `SPEC.md` é um documento de design de produto
(funcionalidades/MVP), não uma especificação técnica protocolar com invariantes de segurança.
Não há parsing/normalization de protocolos a validar contra RFC. (Ex.: não há implementação de
OAuth, JWT, TLS, HTTP/2, parsing de CABECALHOS complexos.) **Fase 6 pulada.**

---

## GitHub Actions Audit

Workflow `.github/workflows/ci.yml`, 3 steps:
- `actions/checkout@v4` (tag mutável — **Low**, supply-chain; ver M1/L1).
- `actions/setup-python@v5` (tag mutável — **Low**, supply-chain).
- `pip install flask pytest pytest-cov` + `pytest -v`.

**AI agent integration check (agentic-actions-auditor):** Nenhuma. Nenhum step de
Claude Code Action / Gemini CLI / OpenAI Codex / agentes AI. Nenhum secret, Nenhum deploy,
Nenhuma publicação de artefato. Apenas teste unitário. → **clean.**

## Phase 10 Addendum

*(povoado ao final da Review Chamber-01 - ver piolium/chamber-workspace/chamber-01/debate.md)*

### Deep bug hunting outcomes
- 8 hipoteses geradas e traceadas file:line: 1 Medium (M1 Docker root), 5 FP/nao-aplicaveis, 4 Low.
- 1 finding Medium confirmado: M1 - Dockerfile root (CWE-250).
- 5 falsos positivos / nao aplicaveis: static /static/ traversal (safe_join+patch), innerHTML+escapeHtml, prefix-match startswith (correctness), SECRET_KEY ausente (sem sessions), localStorage XSS (escapeHtml+same-user).
- 3 Low (hardening): CI tags mutaveis, rate limiting ausente, security headers ausentes.
- 2 Low (supply-chain): Google Fonts externo; deps despinned.

### Trust boundaries revisados
- Sem alteracoes. Browser (nao confiavel) <-> Flask; app single-tenant, sem auth/sessions.

### Superficie adicional descoberta durante a camara
- Rota implicita /static/<path:filename> registrada pelo Flask (static_folder="static" em app.py L55). Segura por werkzeug.utils.safe_join + Werkzeug 3.1.8 (CVE-2025-66221 patchada).
- Dependencia externa: index.html L23-24 carrega CSS do Google Fonts.
- Ausencia de security headers: nenhum after_request em app.py (sem CSP/XFO/XCTO/HSTS).

### Defense briefs (Devil's Advocate)
Detalhes por candidato nas 5 camadas (linguagem/framework/middleware/aplicacao/documentacao)
e checklist dos 8 Claude-Specific FP patterns: ver `piolium/chamber-workspace/devil-advocate-briefs.md`.

### Attack ideation + tracing (Attack Ideator + Code Tracer)
8 hipoteses geradas e traceadas file:line no debate `piolium/chamber-workspace/chamber-01/debate.md`.

### Variant analysis (Phase 9)
- PAT-001 (container-runs-as-root, CWE-250): grep `USER Dockerfile` (ausencia = flag) +
  regra Semgrep `dockerfile.security.missing-user`. Unico Dockerfile -> 0 variantes.
- PAT-002 (mutable-ci-tags): grep `@v[0-9]+` em workflows. Unica workflow -> 0 variantes.
- Nenhuma variante Medium+ identificada (app code limpo: 0 sinks perigosos).
