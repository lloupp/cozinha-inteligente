# Cozinha Inteligente — App "Tem em Casa?"

App web (PWA) que recebe ingredientes do usuário (digitação ou foto da geladeira) e sugere receitas com base no que já se tem em casa, priorizando **zero desperdício**.

## Stack (escolha pragmática, sem build complexo)
- Frontend: HTML + CSS + JavaScript puro (vanilla), servido como PWA (manifest + service worker para uso offline).
- Backend: Python (Flask) com uma API simples `/api/receitas`.
- Dados: arquivo JSON local `receitas.json` com ~30-50 receitas (id, nome, ingredientes[], tempo_min, dificuldade, dietas[], custo_estimado).
- Engine de matching: algoritmo de compatibilidade em Python (não precisa de LLM em runtime — é determinístico e rápido).

## Funcionalidades obrigatórias (MVP)
1. **Entrada de ingredientes**: campo de texto (tags) + botão "tirar foto" (upload de imagem; a detecção por IA da foto pode ser um stub que lista ingredientes mockados, mas a UI deve existir e funcionar o fluxo).
2. **Sugestão de receitas** com **grau de compatibilidade %** (quantos dos ingredientes da receita o usuário já tem). Ordenar por compatibilidade desc.
3. **Lista do que falta** por receita (ingredientes não possuídos) + **custo estimado do que falta** (R$).
4. **Filtros de dieta**: sem lactose, vegano, low carb, sem glúten, proteico, econômico.
5. **Filtro de dificuldade**: muito fácil (<=10min), fácil (<=20min), média, chef.
6. **Modo "Só tenho isso"**: mostra apenas receitas 100% factíveis (todos os ingredientes possuídos), sem exigir compras.
7. **Ingredientes vencendo**: campo opcional "vence em X dias" que prioriza receitas usando aquele ingrediente.
8. **Evitar desperdício**: se usuário informa "banana madura", sugerir receitas que usam banana no topo.

## Diferenciais (implementar ao menos a UI + lógica básica)
- Grau de compatibilidade visual (barra de progresso %).
- Receitas por dificuldade (badges coloridos).
- Filtros de dieta (chips toggláveis).
- Custo estimado do que falta (R$).
- Modo "Só tenho isso".
- IA personalizada (stub: salvar preferências em localStorage — ex: gosta de massas, evita peixe, cozinha p/ 2, tem air fryer — e usar para re-ranquear).
- Upload de foto da geladeira (stub de detecção: retorna ingredientes mockados, mas o fluxo funciona).

## Monetização (apenas documentar em README, não implementar pagamento)
- Gratuito: N receitas/dia.
- Premium: ilimitado + planejamento semanal.
- Anúncios de supermercado + lista de compras + parcerias de entrega.

## Entregáveis
- `app.py` (Flask, serve frontend + API).
- `receitas.json` (dataset de receitas brasileiras/práticas).
- `static/index.html`, `static/style.css`, `static/app.js` (PWA, manifest, sw.js).
- `README.md` (como rodar: `pip install flask`, `python app.py`, abrir localhost:5000; seção de monetização).
- `requirements.txt`.

## Qualidade
- Código limpo, comentado em PT-BR.
- App deve rodar de fato (`python app.py` sobe e a API `/api/receitas?ingredientes=ovo,tomate,queijo` retorna JSON válido).
- Teste manual: chamar a API com ingredientes de exemplo e confirmar compatibilidade calculada corretamente.
- Este é um PROJETO DEMONSTRAÇÃO para prospecção — NÃO colocar badge "DEMO" ou "placeholder" visível; deve parecer um app real e polido.
