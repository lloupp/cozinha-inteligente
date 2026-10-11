# Final Security Audit Report — cozinha-inteligente ("Tem em Casa?")

- **Repositório:** `lloupp/cozinha-inteligente`
- **Commit auditado:** `24abbe512129f6469cf631b00e18386519a820c4` (branch `main`)
- **Data:** 2026-08-17
- **Escopo:** leve (foco essencial). Fases 1, 3, 4/5, 7, 8, 10.
- **Ferramentas:** pip-audit 2.10.1, Bandit 1.9.4, Semgrep 1.173.0 (Community).
- **Desvio do método:** CodeQL CLI e Semgrep **Pro** desativados por decisão do usuário
  (escopo leve). Substituídos por Bandit + Semgrep Community + pip-audit. Este desvio é
  documentado aqui e no KB (`## Static Analysis Summary`). Em um escopo pleno, CodeQL (build
  de database + structural extraction) seria acrescentado para cobertura de *taint analysis*
  cross-file; para esta aplicação pequena e sem sinks perigosos, a cobertura obtida foi
  suficiente para conclusão.

---

## Executive Summary

**Postura de segurança: razoável para um app demo, com um único achado Medium de hardening.**

O app "Tem em Casa?" é um PWA Python/Flask + JS puro que sugere receitas a partir de
ingredientes informados. Sua arquitetura é deliberadamente simples: API JSON sem autenticação,
sem sessões, sem database, sem chamadas outbound — o que encolhe drasticamente a superfície
de ataque.

- **Dependências (Flask 3.1.3, Werkzeug 3.1.8, gunicorn 26.0.0):** sem vulnerabilidades
  conhecidas (`pip-audit` limpo). Duas CVEs recentes do stack (CVE-2025-47278 Flask ≤3.1.0;
  CVE-2025-66221 Werkzeug <3.1.4) **não aplicam** — versões corrigidas + código vulnerável
  não é exercitado (sem `SECRET_KEY`/sessions).
- **Código da aplicação (app.py, engine.py, app.js — ~530 LOC):** Bandit **0 findings**;
  Semgrep **0 app-code findings**; regras customizadas (path traversal via
  `send_from_directory`, DOM-XSS via `innerHTML`, query-param→dangerous-sink) **0 findings**
  após refinamento. Nenhum eval/exec/open/user-controlled/subprocess/SQL.
- **Deep bug hunting (Review Chamber, 4 papéis + subagente Devil's Advocate):** 8 hipóteses
  geradas e traceadas com file:line. Apenas **1 finding seguro** sobreviveu (M1). 5 foram
  false positives / não aplicáveis.
- **Único achado Medium (M1):** o `Dockerfile` roda o container como **root (UID 0)** —
  insecure default (CWE-250). Não há RCE atualmente, mas o achado remove camada de
  containment e amplia blast radius de futura vulnerabilidade.

**Recomendação:** corrigir M1 (single-line `USER` no Dockerfile) antes de qualquer deploy
produzido. Os itens de restante (Low) são observações de *hardening* documentadas na seção
final — não são achados de segurança que impeçam o uso.

---

## Methodology Summary

Auditoria conduzida pela metodologia de 10 fases do `audit` skill, adaptada a um escopo leve
para este projeto de pequeno porte:

| Fase | Atividade | Resultado |
|---|---|---|
| 0 (setup) | Instalar bandit/pip-audit/semgrep; iniciar `piolium/` | ✓ |
| 1 | Advisory intel + SBOM | 0 vulns em deps; 2 CVEs do stack fora de escopo |
| 2 | Patch bypass analysis | Nenhum patch em análise — "None identified" |
| 3 | Threat model + DFD + domain research | web PWA + JSON API, browser↔Flask, 3 DFD slices |
| 4 | SAST (Bandit + Semgrep + rules custom) | 0 app-code findings; 3 infra findings (Docker/CI) |
| 5 | Inline enrichment (6 perguntas) | 12 candidatos classificados: 2 security, 9 FP, 1 corr |
| 6 | Spec gap | None identified (sem RFC) — pulado |
| 7 | Deep bug hunting (Review Chamber) | 1 finding Medium (M1); 5 descartados |
| 8 | P11-LITE (fp-check) | M1 CONFIRMED; cold verification pulado (Medium) |
| 9 | Variant analysis | Nenhuma variante Medium+ identificada (app code limpo) |
| 10 | Exploração + relatório | M1 promovido; PoC estático; este relatório |

---

## Summary of Findings

> Conforme a metodologia, apenas achados **Medium+** aparecem na tabela. Itens Low foram
> dropados dos *findings* e recolhidos como observações de *hardening* (seção final).

| ID | Finding | Severidade | CWE | Tipo | Status |
|----|---------|-----------|-----|------|--------|
| **M1** | Container roda como root (CWE-250) | **Medium** | CWE-250 | Insecure default / hardening | ✅ VALID — CONFIRMED |

**Contra-examina de severidade:** Semgrep classifica `dockerfile.security.missing-user` como
ERROR (alguns scanners como HIGH). Calibrei para **Medium** porque não há qualquer server-side
RCE atualmente (app code limpo) — o root é atingível *apenas* via outra vulnerabilidade. Em um
deploy onde uma RCE existisse, a severidade subiria para High/Critical.

Várias observações Low (CI tags mutáveis, rate limiting ausente, security headers, deps despinned, Google Fonts) e 5 falsos positivos foram identificadas durante as Review Chambers e **dropadas da tabela de findings conforme a metodologia** (Low não aparece em output final). Veja-as recolhidas como *Hardening Recommendations* — não são findings de segurança.

## Technical Findings Detail

### M1 — Container Runs as Root (CWE-250)

- **Report completo + PoC:** `piolium/findings/M1-docker-root/report.md`
- **PoC-Status:** executed (verificação estática determinística; `docker run id` documentado
  para confirmação em ambiente com Docker).
- **Root Cause:** omissão de `USER` no `Dockerfile`; base `python:3.12-slim` defaulta a root;
  `app.py` não dropa privileges.
- **Impacto:** amplia deConfidentialidade/Integridade/Disponibilidade e potencial host escape
  se houver outra vuln ou runtime malconfigurado. Condicional — não há RCE atual.
- **Remediação:** adicionar `USER app` + `adduser --system` no Dockerfile (single-line).

---

## Conclusion

O projeto "Tem em Casa?" tem **boa postura de segurança por design**: arquitetura minimalista
sem sinks perigosos, dependências atualizadas, debug desligado, outputs HTML sempre
*escaped*, e rotas estáticas com path literal protegidas por `safe_join`. Nenhuma vulnerabilidade
explorável foi encontrada na superfície web.

O **único achado Medium** é o container rodando como root — um *insecure default* que deve ser
corrigido antes de produção, especialmente se a aplicação crescer (adicionar sessões, uploads
reais, integração de entrega). A correção é trivial e de baixo risco.

### Hardening Recommendations (não são findings — melhorias de postura)

1. **`Dockerfile`:** adicione `USER app` (veja M1). ✅prioritário.
2. **`requirements.txt`:** pinnifique versões exatas (`Flask==3.1.3`, `gunicorn==26.0.0`) e
   adicione `requirements-lock.txt` / `pip-tools` para reprodutibilidade e supply-chain.
3. **CI:** pinne `actions/checkout` e `actions/setup-python` a SHAs de commit; adicione step
   de `pip-audit`/Semgrep no pipeline.
4. **Headers de segurança:** adicione `after_request` com CSP, `X-Content-Type-Options: nosniff`,
   `X-Frame-Options: DENY`, `Referrer-Policy`; HSTS se HTTPS.
5. **Rate limiting:** `Flask-Limiter` na `/api/receitas` para mitigar flood (Low hoje).
6. **Google Fonts:** considere self-host para remover dependência cross-origin (não urgente).
7. **Foto da geladeira:** se o stub virar OCR real no futuro, adicione validação de tipo/tamanho
   de upload e trabalhe em sandbox separado.

---

## Artefatos de auditoria (retidos)

- `piolium/attack-surface/knowledge-base-report.md` — base de conhecimento (todas as fases).
- `piolium/attack-surface/sbom.json` — inventário de componentes.
- `piolium/final-audit-report.md` — este relatório.
- `piolium/findings/M1-docker-root/report.md` — finding promovido + PoC.

> Artefatos de trabalho intermediários (bandit/semgrep raw resultados, findings-draft,
> semgrep-rules, audit-state, codeql-artifacts) foram removidos conforme a metodologia.
> Mantido como evidência de apoio: `piolium/chamber-workspace/` (transcript da Review
> Chamber + defense briefs do Devil's Advocate), referenciado pelo KB (§ Phase 10 Addendum).
