# Devil's Advocate — Defense Briefs (Phase 10 Deep Analysis)

**Caso:** Cozinha Inteligente ("Tem em Casa?")
**Papel:** Devil's Advocate (defesa)
**Base factual:** código em `app.py`, `engine.py`, `static/app.js`, `Dockerfile`, `.github/workflows/ci.yml`.

## 1. Dockerfile — container roda como root (sem `USER`)

### Veredito: Residual risk (Medium, defense-in-depth)
- **BLOCKING PROTECTION found?** Nenhuma. Nenhuma das 5 camadas (linguagem/framework/middleware/aplicação/documentação) oferece proteção. O container realmente roda como root (UID 0).
- **Defesa:** É um *insecure default* (CWE-250), não uma vulnerabilidade explorável remotamente. O atacante só se beneficia do root *se já tiver comprometido* o container via outra vulnerabilidade. Blast radius amplia, mas não é exploitable por si só. Fix trivial: adicionar `USER app`.
- **Claude-Specific FP:** `defense-in-depth-only` (sim), `low-severity` (probabilidade baixa). → Não é FP puro; há *insecure default* real → **mantido como Medium.**

## 2. CI — tags mutáveis (`actions/checkout@v4`, `actions/setup-python@v5`)

### Veredito: Residual risk (Low, build-only)
- **BLOCKING PROTECTION found?** Nenhuma. Mas **impacto zero**: CI só executa `pytest`; não há deploy, secrets, ou publicação.
- **Defesa:** As ações são *first-party* da GitHub. Ataque exigiria compromisso do próprio GitHub (ameaça de nível estatal). Probabilidade × impacto ≈ desprezível.
- **Claude-Specific FP:** `build-only` (sim), `dev-only` (sim), `low-severity` (sim). → **Low, hardening.**

( ... defendante analisou também sendo tags mutáveis, mas o escopo é *build-only* — risco supply-chain teórico, sem blast radius de produção.)

## 3. `send_from_directory` com literal
- **Proteção bloqueante:** `werkzeug.utils.safe_join` (framework) + argumentos literais constantes + Werkzeug 3.1.8 patch (CVE-2025-66221).
- **Veredito: FALSE POSITIVE** — regra custom sobre-ajustada (erro de schema documentado). → drop.

## 4. `innerHTML` + escapeHtml
- **Proteção bloqueante:** output encoding via `escapeHtml()` em todos os pontos de inserção.
- **Veredito: FALSE POSITIVE** — regra bug (pattern-not em template literals). → drop.

## 5. DoS por `ingredientes` gigante
- **Defesa:** amplificação limitada — loop externo fixo (150 receitas), não exponencial; gunicorn 2 workers; limites de URL de browser/proxy (~8KB). *Real* risco é flood (rate limiting), não request gigante.
- **Veredito: Residual risk (Low, defense-in-depth).** → hardening note.

## 6. `startswith` prefix match ("ovo"↔"ovulo")
- **Defesa:** não é security — output é compat-score ao próprio usuário; nenhuma trust boundary cruzada.
- **Veredito: NOT APPLICABLE** (correctness, não security). → drop.

## 7. SECRET_KEY ausente
- **Defesa:** não há `session`/`flash`/`SECRET_KEY_FALLBACKS` usados → código de assinatura não exercitado. CVE-2025-47278 fora de escopo (3.1.3 patch + não-uso).
- **Veredito: NOT APPLICABLE** (risco futuro condicional, não finding ativo). → drop.

## 8. XSS via localStorage prefs
- **Proteção bloqueante:** `escapeHtml()` output encoding + `normalizar()` na escrita + `same-user` (localStorage é same-origin same-user).
- **Veredito: FALSE POSITIVE** (primary defense em vigor + same-user). → drop.

---

## Resumo consolidado — Verdecitos

| # | Candidato | Veredito | Proteção bloqueante | FP Pattern |
|---|---|---|---|---|
| 1 | Docker root | **Residual risk (Medium)** | Nenhuma | `defense-in-depth-only`, `low-severity` |
| 2 | CI tags mutáveis | **Residual risk (Low)** | Nenhuma, mas `build-only`/`dev-only` | `build-only`, `dev-only`, `low-severity` |
| 3 | send_from_directory literal | **FALSE POSITIVE** | `safe_join` + literais + patch | (rule bug) |
| 4 | innerHTML + escapeHtml | **FALSE POSITIVE** | `escapeHtml()` output encoding | (rule bug) |
| 5 | DoS params | **Residual risk (Low)** | Nenhuma (amplificação limitada) | `defense-in-depth-only`, `low-severity`, `same-user` |
| 6 | startswith prefix | **NOT APPLICABLE** | Nenhuma necessária | `informational`, `low-severity` |
| 7 | SECRET_KEY ausente | **NOT APPLICABLE** | Nenhuma necessária (sem sessões) | `informational`, `defense-in-depth-only`, `low-severity` |
| 8 | localStorage XSS | **FALSE POSITIVE** | `escapeHtml` + `normalizar()` + same-user | `same-user`, `low-severity` |

**3 reais achados de *hardening*** (1, 2, 5) — Low/Medium, nenhum blocking para release.  
**5 false positives ou não aplicáveis** (3, 4, 6, 7, 8).
