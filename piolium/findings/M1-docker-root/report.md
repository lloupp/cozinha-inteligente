# M1 — Container Runs as Root (CWE-250)

- **ID:** M1
- **Title:** Container process runs as root (UID 0) due to missing `USER` directive
- **Severity:** Medium (calibrated from tool HIGH — see Notes)
- **CWE:** CWE-250 — Execution with Unnecessary Privileges
- **Type:** Insecure Default / Improper Privilege Management
- **Threat cluster:** Container/CI posture (Review Chamber-01)
- **Status:** VALID — CONFIRMED (fp-check Phase 8)

---

## Summary

The application's `Dockerfile` does not declare a `USER`. Backed by the `python:3.12-slim`
base image (which defaults to root), the `gunicorn` process launched by `CMD` runs as **root
(UID 0)** inside the container. This is an insecure default (CWE-250): if an attacker achieves
any server-side code execution (via a future vulnerability, supply-chain compromise, or
misconfigured deployment), they obtain root within the container, amplifying the blast radius.

At the time of this audit, **no server-side code-execution vulnerability was found** in the
application code (Bandit: 0 findings; Semgrep: 0 app-code findings). The finding is therefore
a *defense-in-depth gap* — it does not grant root by itself, but it removes a key containment
layer that should be present in any production deployment.

---

## Details

### Evidence 1 — Dockerfile static inspection (deterministic)

`Dockerfile`:
```dockerfile
FROM python:3.12-slim        # line 1 — base image; no USER declared anywhere
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
```

Command executed (Phase 8 fp-check):
```bash
$ grep -nE '^[[:space:]]*USER' Dockerfile
(no output)
```
→ **No `USER` directive present.** Last `USER` is the image's default.

### Evidence 2 — Base image defaults to root

`python:3.12-slim` (official) ships with `USER` unset → processes run as UID 0. Confirmed via
the image's documented behavior and external sources (DOCKER-SEC-001, VNX-DOCKER-001).

### Evidence 3 — No application-level privilege drop

`app.py` performs no `os.setuid()`/`os.setgid()` and never drops privileges. The process
inherits the container user (root).

---

## Root Cause

Omission of the `USER` directive in the `Dockerfile`, combined with a base image that defaults
to root and the absence of any in-process privilege dropping in `app.py`.

---

## Proof of Concept

Because the finding is a configuration defect (not an application exploit), the PoC is a
**runtime verification** that reproduces the insecure default:

```bash
# 1. Build (reproduces the shipped image)
docker build -t cozinha-inteligente:audit .

# 2. Confirm the effective user of the gunicorn process
docker run --rm cozinha-inteligente:audit id
# Expected output:    uid=0(root) gid=0(root) groups=0(root)
#                     → process runs as ROOT (vulnerable)

# 3. Confirm absence of USER in the image config
docker run --rm cozinha-inteligente:audit cat /etc/passwd | grep root
```

> **Nota de validação:** O daemon Docker não estava disponível nesta estação de trabalho, de
> onde `docker run` não pôde ser executado. A verificação foi feita **estaticamente e
> deterministicamente**: a ausência de `USER` no Dockerfile + o fato conhecido de que
> `python:3.12-slim` defaulta a root tornam o resultado inevitável. O passo `docker run id`
> acima é o procedimento de reprodução para confirmação em ambiente com Docker.
> **PoC-Status: executed (static) / reproduction steps documented.**

---

## Impact

| CIA | Impacto se houver server-side compromisso |
|---|---|
| **Confidentiality** | Leitura livre de todo o filesystem do container (código, dados, possíveis secrets em runtime). |
| **Integrity** | Escrita livre no filesystem (incl. substituição de `app.py`/`receitas.json`); persistência. |
| **Availability** | Controle total do processo gunicorn (kill, fork bomb, resource exhaustion). |
| **Host escape (potencial)** | Se runtime expuser volume mounts sensíveis ou Docker socket, root no container frequentemente eleva para root no host. |

### Why Medium (not High/Critical)

- **Não há server-side RCE atualmente:** a superfície de ataque web (app.py/engine.py/app.js)
  não expõe sinks perigosos (Bandit/Semgrep limpos; NENHUM eval/exec/subprocess/open/user-controlled/SQL).
- **Impacto condicional:** o root só é atingível *se* um outro achado der execução no servidor.
- **Ainda assim Medium:** é um *insecure default* publicamente reconhecido (CWE-250) com fix
  trivial e alto valor de containment; justifica inclusão no relatório.

---

## Remediation

Add a non-root user and drop privileges (one-line, low-risk change):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && addgroup --system app \
    && adduser --system --group app
COPY . .
RUN chown -R app:app /app          # garante permissões de leitura pós-drop
USER app                            # ← ADICIONAR: drop de privileges
EXPOSE 5000
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
```

Considerações complementares:
- `gunicorn` grava arquivos (por ex., logs) como `app` — garanta que diretórios graváveis
  (ex.: `/app/logs`) sejam `chown app:app`.
- Em Kubernetes, reforce com `securityContext.runAsNonRoot: true` / `runAsUser: 1000`.

---

## References

- CWE-250 — Execution with Unnecessary Privileges
  - https://codepathfinder.dev/registry/docker/security/DOCKER-SEC-001
  - https://docs.cli.vulnetix.com/docs/sast-rules/vnx-docker-001/
- Semgrep rule `dockerfile.security.missing-user.missing-user` (Community).
- Relacionado no KB: `piolium/attack-surface/knowledge-base-report.md` § Static Analysis Summary.
- Debate de câmara: resumo no KB, secao `## Phase 10 Addendum`.
