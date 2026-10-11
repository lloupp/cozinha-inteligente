# Auditoria Hermes — cozinha-inteligente

Gerado em: `2026-09-06 12:01:32`

## Escopo

- **Não alterei código-fonte nem arquivos de configuração.**
- Arquivo criado/atualizado por pedido do Eduardo: `HERMES_AUDIT.md`.
- Testes executados apenas quando havia comando/estrutura detectável, com timeout curto e sem instalar dependências do projeto.

## Resumo

- Tipo detectado: **Python app/lib**
- Arquivos analisados: **32**
- Tamanho aproximado analisado: **1.15 MB**

## Linguagens / tipos de arquivo

- Markdown: 9
- Python: 8
- Outro: 8
- JSON: 3
- JavaScript: 2
- CSS: 1
- HTML: 1

## Arquivos principais vistos

- `.gitignore`
- `.python-version`
- `Dockerfile`
- `LICENSE`
- `PLANO-AUDITORIA.md`
- `PLANO-EVOLUCAO.md`
- `README.md`
- `SPEC.md`
- `app.log`
- `app.py`
- `engine.py`
- `piolium/attack-surface/knowledge-base-report.md`
- `piolium/attack-surface/sbom.json`
- `piolium/chamber-workspace/chamber-01/debate.md`
- `piolium/chamber-workspace/devil-advocate-briefs.md`
- `piolium/final-audit-report.md`
- `piolium/findings/M1-docker-root/report.md`
- `receitas.json`
- `requirements-dev.txt`
- `requirements.txt`
- `scrape_50_recipes.py`
- `scrape_recipes.py`
- `scrape_recipes_v2.py`
- `static/app.js`
- `static/icon.svg`
- `static/index.html`
- `static/manifest.json`
- `static/style.css`
- `static/sw.js`
- `tests/__init__.py`
- `tests/test_api.py`
- `tests/test_engine.py`

## Estado Git

- Comando: `git status --short --branch`
- Exit code: `0`

```text
## main...origin/main
 M Dockerfile
 M engine.py
 M receitas.json
 M static/app.js
 M static/index.html
 M static/style.css
?? PLANO-AUDITORIA.md
?? PLANO-EVOLUCAO.md
?? piolium/
?? scrape_50_recipes.py
?? scrape_recipes.py
?? scrape_recipes_v2.py
```

## Resultado dos testes / validações

### ❌ FALHOU
- Comando: `python3 -m pytest -q`
- Exit code: `2`
- Tempo: `1.28s`

```text
==================================== ERRORS ====================================
______________________ ERROR collecting tests/test_api.py ______________________
ImportError while importing test module '/home/eduardodlima/projetos/cozinha-inteligente/tests/test_api.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../.hermes/hermes-agent/.hermes-runtime/python/generation-1786058349-79079-96026584/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_api.py:10: in <module>
    from app import app
app.py:12: in <module>
    from flask import Flask, request, jsonify, send_from_directory
E   ModuleNotFoundError: No module named 'flask'
=========================== short test summary info ============================
ERROR tests/test_api.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.16s
```

### ✅ OK
- Comando: `python3 -m compileall -q /home/eduardodlima/projetos/cozinha-inteligente/scrape_50_recipes.py /home/eduardodlima/projetos/cozinha-inteligente/engine.py /home/eduardodlima/projetos/cozinha-inteligente/app.py /home/eduardodlima/projetos/cozinha-inteligente/scrape_recipes_v2.py /home/eduardodlima/projetos/cozinha-inteligente/scrape_recipes.py /home/eduardodlima/projetos/cozinha-inteligente/tests/__init__.py /home/eduardodlima/projetos/cozinha-inteligente/tests/test_api.py /home/eduardodlima/projetos/cozinha-inteligente/tests/test_engine.py`
- Exit code: `0`
- Tempo: `0.72s`

```text
(sem saída)
```

### ✅ OK
- Comando: `node /tmp/check_html_inline_scripts.js /home/eduardodlima/projetos/cozinha-inteligente`
- Exit code: `0`
- Tempo: `0.59s`

```text
/home/eduardodlima/projetos/cozinha-inteligente/.venv/lib/python3.11/site-packages/setuptools/tests/indexes/test_links_priority/external.html sem script inline para checar
/home/eduardodlima/projetos/cozinha-inteligente/.venv/lib/python3.11/site-packages/setuptools/tests/indexes/test_links_priority/simple/foobar/index.html sem script inline para checar
/home/eduardodlima/projetos/cozinha-inteligente/static/index.html sem script inline para checar
```


## Propostas gerais de melhoria

1. Corrigir os testes/comandos que falharam antes de evoluir funcionalidades.

## Próximo passo sugerido

Primeiro estabilizar os testes/comandos que falharam; depois evoluir funcionalidades.

---

## Intervenção Claude Code

Data: `2026-09-06`

### Diagnóstico da falha do relatório

A falha `❌ FALHOU` em `python3 -m pytest -q` (`ModuleNotFoundError: No module named 'flask'`)
foi um **falso-positivo ambiental**: a auditoria rodou com um Python isolado do runtime
Hermes, sem as dependências do projeto instaladas. Rodando com o `.venv` do próprio projeto
(Flask 3.1.3, pytest), **os 24 testes originais já passavam**. Nenhum bug de código estava
por trás da falha.

### O que foi alterado

1. **`.github/workflows/ci.yml`** — o passo de instalação passou a usar
   `pip install -r requirements.txt -r requirements-dev.txt` em vez de listar pacotes
   fixos (`flask pytest pytest-cov`). Fonte única de verdade para dependências e evita
   divergência entre CI e projeto — ataca a causa raiz do problema (ambiente sem Flask).

2. **`tests/test_receitas_data.py`** (novo) — teste de integridade do dataset
   `receitas.json`, que havia sido massivamente expandido (1976 receitas) sem cobertura.
   Verifica: JSON válido com chave `receitas`, dataset não vazio, campos obrigatórios
   (`id`, `nome`, `ingredientes`, `modo`) presentes, ingredientes como listas não vazias
   e ids únicos.

Não houve remoção de funcionalidades. As melhorias já pendentes no working tree
(Docker rodando como usuário não-root — achado `M1-docker-root`; e código defensivo em
`engine.py`) foram preservadas e validadas.

### Testes executados

- `.venv/bin/python -m pytest -q` → **28 passed** (24 originais + 4 novos)
- Smoke test da API (`/`, `/api/receitas`, `/api/dietas-validas`) → todos `200`/OK
- Validação de sintaxe do `ci.yml` → OK
- Integridade do `receitas.json` → 1976 receitas, 0 ids duplicados, 0 campos faltando

### Próximo passo recomendado

Comitar estas mudanças junto com o trabalho pendente já revisado. Opcionalmente, adicionar
cache de pip no CI e cobertura mínima (`--cov-fail-under`) para consolidar a qualidade.

---

## Intervenção Codex

Data: `2026-09-06`

### Diagnóstico

A falha atual em `python3 -m pytest -q` era ambiental: o executável `python3` em uso
apontava para `/home/eduardodlima/.hermes/hermes-agent/venv/bin/python3`, que tinha
`pytest` instalado, mas não tinha `Flask`. O projeto já declarava `Flask>=3.0` em
`requirements.txt` e `pytest>=8.0` em `requirements-dev.txt`, então não foi necessário
alterar código para resolver o `ModuleNotFoundError`.

### Arquivos alterados

- `HERMES_AUDIT.md` — adicionada esta seção de intervenção.

### Ação executada

- `python3 -m pip install -r requirements.txt -r requirements-dev.txt` — sincronizou o
  Python usado pelo check com as dependências declaradas do projeto.

### Testes e verificações

- `python3 -m pytest -q` → **28 passed**
- `node --check static/app.js` → **OK**
- `python3 -m compileall -q app.py engine.py tests` → **OK**
- `python3 -m compileall -q scrape_50_recipes.py scrape_recipes.py scrape_recipes_v2.py` → **OK**
- Parse simples de `static/index.html` com `html.parser` → **OK**

### Resultado

O check principal solicitado, `python3 -m pytest -q`, passou no ambiente atual após a
instalação das dependências já declaradas. Nenhum arquivo em
`/home/eduardodlima/projetos/apura-tributario-v2` foi acessado ou alterado.
