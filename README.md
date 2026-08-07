# Tem em Casa? — Cozinha Inteligente

App web que responde à pergunta diária **"o que eu cozinho hoje com o que já tenho em casa?"**,
reduzindo o desperdício de alimentos e sugerindo receitas personalizadas a partir dos
ingredientes disponíveis.

![CI](https://github.com/lloupp/cozinha-inteligente/actions/workflows/ci.yml/badge.svg)
![Licença](https://img.shields.io/badge/LICENCA-MIT-green)
![Python](https://img.shields.io/badge/Python-3.12-blue)

## Diferenciais

- **Grau de compatibilidade (%)** — mostra quanto da receita você já consegue fazer com o que tem.
- **Receitas por dificuldade** — Muito fácil (≤10 min), Fácil (≤20 min), Média, Chef.
- **Evitar desperdício** — informe ingredientes "maduros"/vencendo e o app prioriza receitas que os usam.
- **Ingredientes vencendo** — diga o que vence cedo e receba sugestões que consomem esses itens.
- **Dietas** — filtros: Sem lactose, Vegano, Low carb, Sem glúten, Proteico, Econômico, Vegetariano.
- **Quanto custa** — calcula o custo estimado do que falta comprar (R$).
- **Modo "Só tenho isso"** — exibe apenas receitas 100% factíveis, sem exigir compras.
- **Foto da geladeira** — stub de detecção de ingredientes a partir de imagem.
- **IA personalizada** — salvamento de preferências em localStorage e re-ranqueamento.

## Stack

- **Backend:** Python + Flask (API `/api/receitas`)
- **Frontend:** HTML + CSS + JavaScript puro, servido como PWA
- **Engine:** algoritmo determinístico de compatibilidade

## Como rodar (local)

```bash
pip install -r requirements.txt
python app.py
```

Acesse: http://127.0.0.1:5000

## Como rodar (com Docker)

```bash
docker build -t cozinha-inteligente .
docker run -p 5000:5000 cozinha-inteligente
```

## Como usar

1. Digite os ingredientes (separados por vírgula) ou clique nas sugestões.
2. Opcional: informe ingredientes vencendo, marque dietas ou ative "Só tenho isso".
3. Clique em **Ver receitas possíveis**.
4. As receitas aparecem ordenadas por compatibilidade, com o que falta e o custo estimado.
5. Use o botão **Copiar lista de compras** para copiar os itens que precisa comprar.

## API

```
GET /api/receitas?ingredientes=ovo,tomate,queijo&sotenho=true&dietas=vegano&vencendo=leite
```

Endpoints disponíveis:
- `/api/receitas` — busca receitas
- `/api/ingredientes-sugeridos` — lista de ingredientes para autocomplete
- `/api/dietas-validas` — dietas suportadas

## Estrutura

```
cozinha-inteligente/
├── app.py              # Flask: serve frontend + API
├── engine.py           # Motor de matching (testável)
├── receitas.json       # dataset (150 receitas)
├── requirements.txt    # dependências de runtime
├── requirements-dev.txt  # dependências de desenvolvimento (pytest)
├── Dockerfile          # build Docker
├── SPEC.md             # especificação técnica
├── README.md
├── .gitignore
├── LICENSE             # MIT
└── static/
    ├── index.html
    ├── style.css
    ├── app.js
    ├── manifest.json
    ├── sw.js
    └── icon.svg
```

## Testes

```bash
pip install pytest
pytest -v
```

## Desenvolvimento

O projeto está dividido em:
- `app.py` — rotas Flask
- `engine.py` — lógica de matching (testável isoladamente)

## Monetização

- **Gratuito:** número limitado de receitas por dia.
- **Premium:** receitas ilimitadas + planejamento semanal.
- **Anúncios** de supermercados e marcas.
- **Lista de compras** integrada.
- **Parcerias** de entrega de ingredientes.
