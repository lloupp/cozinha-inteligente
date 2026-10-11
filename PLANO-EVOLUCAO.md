# Plano de Evolução para Cozinha Inteligente

## Visão Geral
Baseado no estado atual do projeto (200 receitas, Docker corrigido, testes passando), este plano foca em evoluções que:
- Aproveitam dados reais (não sintéticos)
- Implementam monetização viável
- Melhoram a experiência do usuário com foco em reduzir desperdício
- Utilizam técnicas de ML/NLP para melhorias relevantes
- Evitam "badges de demo" - tudo deve parecer e funcionar como produto real

---

## Fase 1: Melhorias Imediatas (1-2 semanas)

### 1.1 Sistema de Limite Diário (Base para Freemium)
- **Objetivo**: Implementar o modelo gratuito mencionado no README
- **Ações**:
  - Adicionar campo `last_reset_date` e `daily_usage` no localStorage
  - Limite: 5 receitas por dia para usuários não-logados
  - Mensagem amigável ao atingir limite com convite para criar conta gratuita
  - Reset automático à meia-noite (horário local)
- **Valor**: Cria funnelling para versão premium sem bloquear experiência inicial

### 1.2 Melhoria do Algoritmo de Matching
- **Objetivo**: Aumentar precisão usando dados reais de compatibilidade
- **Ações**:
  - Adicionar pesos por categoria de ingrediente (ex: proteínas têm peso maior que temperos)
  - Implementar penalidade por ingredientes "maduros/vencendo" não utilizados
  - Adicionar bônus por uso de ingredientes que estão vencendo (conforme roadmap existente)
  - Testar com dataset real de substituições culinárias (ex: DataFood Consortium)
- **Valor**: Melhoria direta no core value proposition - sugestões mais úteis

### 1.3 Implementação Básica de Conta Gratuita
- **Objetivo**: Preparar caminho para premium e salvar preferências
- **Ações**:
  - Criar endpoint simples `/api/user/preferences` (GET/POST)
  - Salvar preferências de dieta, restrições e favoritos no localStorage (inicialmente)
  - Interface simples para gerenciar preferências (painel de configurações)
  - Sincronização básica com localStorage (sem backend ainda)
- **Valor**: Base para personalização mencionada no README e caminho para premium

---

## Fase 2: Melhorias de Médio Prazo (3-6 semanas)

### 2.1 Sistema de Planejamento Semanal (Premium Core)
- **Objetivo**: Implementar o recurso premium mencionado
- **Ações**:
  - Criar visão de calendário semanal (visão de grade 7 dias)
  - Permitir arrastar e soltar receitas nos dias
  - Gerar lista de compras consolidada semanal
  - Algoritmo de balanceamento: variar tipos de refeição, considerar leftovers
  - Integração com algoritmo de vencimento: priorizar uso de ingredientes que expiram
- **Valor**: Diferencial claro para plano premium - resolve problema real de planejamento

### 2.2 Integração com Dados Nutricionais Reais
- **Objetivo**: Enriquecer receitas com informações nutricionais verificáveis
- **Ações**:
  - Usar dataset aberto como USDA FoodData Central (dados reais, não sintéticos)
  - Mapear ingredientes das receitas para entradas do USDA
  - Calcular macros e micronutrientes por porção
  - Adicionar filtros: baixo carb, alto proteína, baixo sódio, etc.
  - Exibir informações nutricionais na card da receita
- **Valor**: Aproveita preferência do usuário por dados reais, aumenta utilidade para usuários conscientes de saúde

### 2.3 Melhoria da Funcionalidade "Foto da Geladeira"
- **Objetivo**: Transformar stub em funcionalidade útil (sem prometer IA milagrosa)
- **Ações**:
  - Implementar upload de foto com pré-visualização
  - Usar modelo de visão computacional leve e pré-treinado (ex: MobileNet + transfer learning em dataset de ingredientes)
  - Foco emDetecção de 10-15 ingredientes comuns (ovo, tomate, cebola, alho, etc.)
  - Retornar sugestão de ingredientes detectados para confirmação do usuário
  - Trabalhar com expectativa realista: "detecção assistida" não substituição total
- **Valor**: Implementação honesta de visão computacional, não "demo que não funciona"

### 2.4 Sistema de Lista de Compras Inteligente
- **Objetivo**: Implementar recurso mencionado no README
- **Ações**:
  - Consolidar ingredientes de receitas selecionadas
  - Agrupar por categoria de supermercado (hortifrúti, laticínios, etc.)
  - Marcar ingredientes que o usuário já tem (baseado em seu "estoque")
  - Permitir marcar itens como comprados em tempo real
  - Exportar para WhatsApp/email ou imprimir
  - Integração futura: opção para enviar para entregifys/mercado locais (parceria)
- **Valor**: Resolve ponto de atrito entre sugestão e ação real

---

## Fase 3: Visão de Longo Prazo (2-3 meses)

### 3.1 Parcerias de Dados Receitas
- **Objetivo**: Expandir acervo com dados reais e verificados
- **Ações**:
  - Estabelecer parcerias com blogs de culinária confiáveis (com crédito/linkback)
  - Criar processo de submissão de receitas da comunidade com moderação
  - Implementar sistema de avaliação de receitas pelos usuários
  - Adicionar origem/credito para cada receita (transparência)
  - Possível modelo: receitas premium contribuídas por chefs/ nutricionistas
- **Valor**: Cresce acervo de forma sustentável e aumenta confiança

### 3.2 Algoritmo de Sugestão Contextual
- **Objetivo**: Ir além de matching simples para sugestões verdadeiramente úteis
- **Ações**:
  - Incorporar horário do dia (café da manhã vs jantar)
  - Considerar clima/temperatura (sopas no frio, saladas no calor)
  - Aprender com histórico do usuário (receitas feitas, avaliações)
  - Sugerir com base em eventos locais (feriados, temporadas)
  - Usar técnicas leves de bandit learning para exploração/exploração
- **Valor**: Personalização verdadeira que melhora com o uso

### 3.3 Integração com Serviços de Entrega
- **Objetivo**: Realizar a parceria de entrega mencionada
- **Ações**:
  - Mapear ingredientes para SKUs de parceiros locais (supermercados, feiras)
  - Criar API simples para verificar disponibilidade e preço
  - Permitir "comprar faltantes" com um clique (redirecionamento para parceiro)
  - Receber comissão por indicação (modelo de receita real)
  - Foco inicial em parceiros regionais antes de escalar
- **Valor**: Primeira fonte de receita real baseada em valor entregue

### 3.4 Sistema de Feedback e Aprendizado Contínuo
- **Objetivo**: Fazer o sistema melhorar com uso real
- **Ações**:
  - Coletar feedback implícito (receitas feitas, repetidas, abandonadas)
  - Permitir avaliação explícita (gostou/não gostou, por que)
  - Usar feedback para ajustar pesos do algoritmo de matching
  - Identificar lacunas no acervo (ex: muitos pedidos por receitas veganas que não temos)
  - Gerar relatórios mensais de uso para melhoria contínua
- **Valor**: Cria ciclo virtuoso de melhoria baseado em dados reais de uso

---

## Princípios Orientadores (do User Profile)
1. **Dados REAIS sempre**: Não usar dados sintéticos para ML ou demonstrações
2. **Foco em coding de qualidade**: Qualquer componente de ML/NLP deve ser bem implementado, não apenas "colado"
3. **Nada de badges DEMO**: Toda funcionalidade deve funcionar de forma útil para o usuário final
4. **Monetização clara**: Caminho óbvio para geração de receita sem prejudicar experiência gratuita
5. **Privacidade por design**: Dados do usuário permanecem locais por padrão, com opção de sincronização opcional

---

## Métricas de Sucesso para Cada Fase
- **Fase 1**: % de usuários que atingem limite diário e criam conta gratuita > 15%
- **Fase 2**: Taxa de retenção semanal (usuários que voltam após 7 dias) > 30%
- **Fase 3**: Receita média por usuário ativo > R$ 5,00/mês (via premium ou parcerias)

Este plano equilibra melhorias técnicas valiosas com caminhos claros para sustentabilidade financeira, respeitando as preferências do usuário por dados reais, qualidade de implementação e evitando soluções superficiais. Cada fase entrega valor independente enquanto constrói para a próxima.