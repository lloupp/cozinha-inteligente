# Plano de Auditoria de Segurança — "Tem em Casa?" (cozinha-inteligente)

Objetivo: auditar o projeto `cozinha-inteligente` (Python/Flask + vanilla JS PWA) seguindo a
metodologia do `audit` skill, adaptada ao escopo escolhido pelo usuário.

## Escolhas do usuário (confirmadas)
- Escopo: **leve (foco essencial)** — fases 1, 3, 4 (SAST leve), 5, 7, 10.
- Semgrep: **Community apenas** (sem Pro).
- Validação de PoC: **localhost/loopback** (app em 127.0.0.1:5000).
- CodeQL: **desativado** (escopo leve) → substituído por bandit + semgrep community + pip-audit.
  Este desvio é documentado no KB (`## Static Analysis Summary`) e no relatório final.

## Fases

### Fase 0 — Setup
- `pip install bandit pip-audit semgrep` (na .venv existente ou global).
- Criar `piolium/audit-state.json` (entrada in_progress), `piolium/attack-surface/`.

### Fase 1 — Inteligência + SBOM
- `pip-audit` sobre Flask/gunicorn + Python 3.12.
- SBOM → `piolium/attack-surface/sbom.json`.
- Seções KB: `## Advisory Intelligence`, `## Component Inventory`.

### Fase 2 — Patch bypass
- Só se Phase 1 encontrar advisories aplicáveis. Senão: "None identified".

### Fase 3 — Knowledge Base + threat model
- Tipo: web PWA + API JSON. Trust boundary: browser ↔ Flask.
- DFD slices: (a) query→parse→matching; (b) servimento de estáticos.
- Seções KB: `## Threat Model`, `## High-Risk DFD/CFD Slices`, `## Domain Attack Research`,
  `## Phase 4 Extraction Targets`.

### Fase 4 — SAST (leve)
- `bandit -r .` (Python), `semgrep --config=auto .` (community).
- Regras customizadas bandit/semgrep para o matching de ingredientes e parsing de query.
- `agentic-actions-auditor` sobre `.github/workflows/ci.yml`.
- KB: `## Static Analysis Summary`, `## SAST Enrichment`, `## GitHub Actions Audit`.

### Fase 5 — Inline enrichment (faz parte da 4 acima): classificar findings.

### Fase 6 — Spec gap: SEM RFC → "None identified", pula.

### Fase 7 — Deep bug hunting (Review Chambers via subagents)
- 1-3 câmaras × 4 papéis (Attack Ideator, Code Tracer, Devil's Advocate, Synthesizer).
- `piolium/chamber-workspace/<id>/debate.md`; drafts em `piolium/findings-draft/`.

### Fase 8 — P11-LITE: fp-check sobre findings VALID; cold verification (localhost) só para C/H.

### Fase 9 — Variant analysis (leve, usando registry + grep/QL on-demand).

### Fase 10 — Exploração & relatório final
- Promover drafts → `piolium/findings/<ID>-<slug>/`.
- PoC real no localhost para CRITICAL/HIGH.
- `vuln-report` por finding; `piolium/final-audit-report.md`.
- Cleanup: remover working artifacts; manter KB, sbom.json, findings/, final-audit-report.md.

## Validações
- pip-audit / bandit / semgrep rodam.
- `pytest -v` continua verde (regressão).
- KB tem todas as seções Phase-labelled.
- Consistency checks do método ao final.

## Próximos passos
Iniciar Fase 0 (instalação) + Fase 1 (SBOM + pip-audit).
