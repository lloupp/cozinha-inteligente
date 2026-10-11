// Tem em Casa? — Cozinha Inteligente
// Lógica do frontend: tags de ingredientes, filtros, foto (stub), chamada à API.

const state = {
  ingredientes: [],
  dietas: [],
  soTenho: false,
  vencendo: [],
  preferencias: [],
  resultadosAnteriores: [],
  geladeira: [],
  buscaOffset: 0,
  buscaLimite: 30,
  buscaTotal: 0,
};

// Acumulador da lista de compras (falta) de todas as páginas carregadas.
const listasFaltaCompleta = new Set();

const RING_C = 150.8;

const $ = (id) => document.getElementById(id);

function normalizar(s) {
  return s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function compatRingSVG(pct) {
  const p = Math.max(0, Math.min(100, Number(pct) || 0));
  const offset = RING_C * (1 - p / 100);
  return `
    <svg viewBox="0 0 56 56" aria-hidden="true">
      <circle class="compat-ring__track" cx="28" cy="28" r="24" />
      <circle class="compat-ring__fill" cx="28" cy="28" r="24"
        style="stroke-dasharray:${RING_C};stroke-dashoffset:${RING_C}"
        data-offset="${offset}" />
    </svg>
    <span class="compat-ring__pct">${Math.round(p)}%</span>
  `;
}

function animateRings(root) {
  requestAnimationFrame(() => {
    root.querySelectorAll(".compat-ring__fill").forEach((el) => {
      const offset = el.getAttribute("data-offset");
      el.style.strokeDashoffset = offset;
    });
  });
}

function renderTags() {
  const box = $("tagsInput");
  box.querySelectorAll(".tag").forEach((t) => t.remove());
  const input = $("ingredientField");
  state.ingredientes.forEach((ing, i) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.innerHTML = `${escapeHtml(ing)} <button type="button" aria-label="Remover ${escapeHtml(ing)}">×</button>`;
    tag.querySelector("button").addEventListener("click", () => {
      state.ingredientes.splice(i, 1);
      renderTags();
      renderSugestoes();
    });
    box.insertBefore(tag, input);
  });
}

function addIngrediente(val) {
  const v = normalizar(val);
  if (v && !state.ingredientes.includes(v)) {
    state.ingredientes.push(v);
    renderTags();
  }
}

let sugeridosDeAPI = [];

async function carregarSugestoes() {
  try {
    const res = await fetch("/api/ingredientes-sugeridos");
    sugeridosDeAPI = await res.json();
  } catch (e) {
    sugeridosDeAPI = [];
  }
}

async function renderSugestoes() {
  const box = $("suggestions");
  box.innerHTML = "";
  const usados = new Set(state.ingredientes);
  const sugeridos = sugeridosDeAPI.filter((s) => !usados.has(s)).slice(0, 12);
  sugeridos.forEach((s) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "sug";
    b.textContent = s;
    b.setAttribute("role", "listitem");
    b.addEventListener("click", () => {
      addIngrediente(s);
      renderSugestoes();
    });
    box.appendChild(b);
  });
}

function dificuldadeLabel(d) {
  const map = {
    "muito facil": "Muito fácil",
    "facil": "Fácil",
    "media": "Média",
    "chef": "Chef",
  };
  return map[d] || d;
}

function dificuldadeClass(d) {
  return "dif-" + String(d || "").replace(/\s+/g, "-");
}

function stateMsg(kind, title, body) {
  const icon =
    kind === "error"
      ? `<div class="state-msg__icon state-msg__icon--error" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="12" cy="12" r="10"/><path d="M12 8v5M12 16h.01"/>
          </svg>
        </div>`
      : `<div class="state-msg__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 11h16v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8z"/>
            <path d="M4 11l2-6h12l2 6"/>
            <path d="M9 15h6"/>
          </svg>
        </div>`;
  return `<div class="state-msg">${icon}<h3>${title}</h3><p>${body}</p></div>`;
}

function renderResultados(data) {
  const box = $("resultados");
  box.innerHTML = "";

  if (!data.receitas || !data.receitas.length) {
    box.innerHTML = stateMsg(
      "empty",
      "Nada encaixou ainda",
      "Tente mais um ingrediente ou solte os filtros. A geladeira ainda tem o que contar."
    );
    return;
  }

  const header = document.createElement("div");
  header.className = "results-header";
  const n = data.receitas.length;
  const totalLabel = data.total != null ? `${data.total} receita${data.total === 1 ? "" : "s"}` : `${n} receita${n === 1 ? "" : "s"}`;
  header.innerHTML = `
    <h2>O que dá pra fazer</h2>
    <span class="count">${totalLabel}</span>
  `;
  box.appendChild(header);

  const list = document.createElement("div");
  list.className = "recipes-list";
  box.appendChild(list);

  data.receitas.forEach((r, idx) => {
    const el = document.createElement("article");
    const completo = r.compatibilidade >= 100;
    const urgente = r.urgencia > 0;
    el.className =
      "recipe" +
      (urgente ? " recipe--urgente" : "") +
      (completo ? " recipe--completo" : "");
    el.style.animationDelay = `${Math.min(idx, 12) * 0.05}s`;
    el.setAttribute("data-compat", r.compatibilidade);
    const desc = r.nome + (r.modo ? " - " + r.modo : "");
    el.setAttribute("data-descricao", escapeHtml(desc));

    const tem = r.tem.length ? r.tem.map(escapeHtml).join(", ") : "—";
    const falta = r.falta.length ? r.falta.map(escapeHtml).join(", ") : "nenhum";
    const custoHtml =
      r.custo_falta > 0
        ? `~R$ ${r.custo_falta.toFixed(2)} a mais`
        : "Você tem tudo · R$ 0";
    const badges = (r.dietas || [])
      .map((d) => `<span class="badge">${escapeHtml(d)}</span>`)
      .join("");
    const urg = urgente
      ? `<span class="badge urgencia">Use antes de vencer</span>`
      : "";

    const modoHtml = r.modo
      ? `<details class="recipe__modo">
        <summary class="modo-summary">Modo de preparo</summary>
        <p class="modo-detail">${escapeHtml(r.modo)}</p>
      </details>`
      : "";

    el.innerHTML = `
      <header class="recipe__head">
        <div>
          <h3 class="recipe__title">${escapeHtml(r.nome)}</h3>
          <p class="recipe__meta">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
            </svg>
            ${r.tempo_min} min
          </p>
        </div>
        <div class="compat-ring" aria-label="${r.compatibilidade}% compatível">
          ${compatRingSVG(r.compatibilidade)}
        </div>
      </header>
      <div class="badges">
        <span class="badge ${dificuldadeClass(r.dificuldade)}">${dificuldadeLabel(r.dificuldade)}</span>
        ${badges}${urg}
      </div>
      <div class="recipe__lists">
        <p class="recipe__tem"><span class="label">Tem</span> <span><b>${tem}</b></span></p>
        <p class="recipe__falta"><span class="label">Falta</span> <span><b>${falta}</b></span></p>
        <p class="recipe__custo ${r.custo_falta === 0 ? "zero" : ""}"><span class="label">Custo</span> <span><b>${custoHtml}</b></span></p>
      </div>
      ${modoHtml}
    `;
    list.appendChild(el);
  });

  // Paginação: botão "carregar mais" quando ainda há resultados.
  if (data.tem_mais) {
    const more = document.createElement("button");
    more.type = "button";
    more.id = "carregarMaisBtn";
    more.className = "btn btn--more";
    more.textContent = `Carregar mais receitas`;
    more.addEventListener("click", () => carregarMais());
    box.appendChild(more);
  }

  // Lista completa para o botão copiar quando tudo tiver sido carregado.
  const somar = data.receitas.map((r) => r.falta || []);
  somar.forEach((f) => f.forEach((i) => (listasFaltaCompleta.add(i))));

  animateRings(box);
  rendererizarBotaoCopiar();
}

function rendererizarBotaoCopiar() {
  const btn = $("copiarLista");
  if (!btn) return;

  btn.onclick = () => {
    const todosFaltam = new Set();
    // usa o acumulador de todas as páginas carregadas
    listasFaltaCompleta.forEach((i) => todosFaltam.add(i));
    // fallback: receitas já exibidas
    state.resultadosAnteriores.forEach((r) => {
      r.falta.forEach((i) => todosFaltam.add(i));
    });

    if (todosFaltam.size === 0) {
      btn.textContent = "Você tem tudo!";
      btn.disabled = true;
      return;
    }

    const texto = `Lista de compras:
${Array.from(todosFaltam).sort().map((i) => `- ${i}`).join("\n")}`;

    navigator.clipboard.writeText(texto).then(() => {
      const original = btn.textContent;
      btn.textContent = "Copiado!";
      btn.disabled = true;
      setTimeout(() => {
        btn.textContent = original;
        btn.disabled = false;
      }, 2000);
    });
  };
}

async function carregarPreferencias() {
  carregarGeladeira();
  const favores = localStorage.getItem("pref-ingredientes");
  if (favores) {
    try {
      const dados = JSON.parse(favores);
      state.ingredientes = dados.ingredientes || [];
      state.soTenho = dados.soTenho || false;
    } catch (e) {
      state.ingredientes = [];
    }
  }
  // Se não há ingredientes salvos mas há geladeira, usa o inventário na busca.
  if (!state.ingredientes.length && state.geladeira.length) {
    state.ingredientes = state.geladeira.map((it) => it.nome);
  }
  renderTags();
  atualizarFridgeHint();
}

// ---------- Minha Geladeira (inventário persistente) ----------

function carregarGeladeira() {
  try {
    const raw = localStorage.getItem("geladeira-inventario");
    const dados = raw ? JSON.parse(raw) : [];
    state.geladeira = Array.isArray(dados)
      ? dados.filter((it) => it && typeof it.nome === "string")
      : [];
  } catch (e) {
    state.geladeira = [];
  }
}

function salvarGeladeira() {
  localStorage.setItem("geladeira-inventario", JSON.stringify(state.geladeira));
  atualizarFridgeHint();
}

function itensVencendo() {
  return state.geladeira
    .filter((it) => typeof it.venceDias === "number" && it.venceDias <= 3)
    .map((it) => it.nome);
}

function validadeInfo(dias) {
  if (typeof dias !== "number") return null;
  if (dias <= 1) return { classe: "validade--hoje", texto: dias === 0 ? "vence hoje" : "vence amanhã" };
  if (dias <= 3) return { classe: "validade--logo", texto: `vence em ${dias} dias` };
  return { classe: "validade--ok", texto: `vence em ${dias} dias` };
}

function renderGeladeira() {
  const list = $("fridgeList");
  if (!list) return;
  list.innerHTML = "";

  const count = $("fridgeCount");
  count.textContent = `${state.geladeira.length} item${state.geladeira.length === 1 ? "" : "s"} na geladeira`;
  $("fridgeClearBtn").hidden = !state.geladeira.length;

  if (!state.geladeira.length) {
    list.innerHTML = `<p class="fridge-empty">Sua geladeira está vazia. Adicione o que você tem em casa para buscar receitas sem redigitar tudo.</p>`;
    return;
  }

  const ordenado = state.geladeira
    .map((it, i) => ({ ...it, _i: i }))
    .sort((a, b) => {
      const va = typeof a.venceDias === "number" ? a.venceDias : Infinity;
      const vb = typeof b.venceDias === "number" ? b.venceDias : Infinity;
      return va - vb;
    });

  ordenado.forEach((it) => {
    const info = validadeInfo(it.venceDias);
    const el = document.createElement("div");
    el.className = "fridge-item";
    el.innerHTML = `
      <span class="fridge-item__nome">${escapeHtml(it.nome)}</span>
      ${info ? `<span class="validade ${info.classe}">${escapeHtml(info.texto)}</span>` : `<span class="validade">sem validade</span>`}
      <button type="button" class="fridge-item__remover" aria-label="Remover ${escapeHtml(it.nome)}">×</button>
    `;
    el.querySelector("button").addEventListener("click", () => removeDaGeladeira(it._i));
    list.appendChild(el);
  });
}

function addNaGeladeira(nome, dias) {
  const v = normalizar(nome);
  if (!v) return;
  if (state.geladeira.some((it) => it.nome === v)) return;
  const item = { nome: v, venceDias: null };
  const parsed = parseInt(dias, 10);
  if (!isNaN(parsed) && parsed >= 0) item.venceDias = parsed;
  state.geladeira.push(item);
  salvarGeladeira();
  renderGeladeira();
  renderFridgeSugestoes();
  if (!state.ingredientes.includes(v)) {
    state.ingredientes.push(v);
    renderTags();
    renderSugestoes();
  }
}

function removeDaGeladeira(index) {
  const [removido] = state.geladeira.splice(index, 1);
  salvarGeladeira();
  renderGeladeira();
  renderFridgeSugestoes();
  if (removido) {
    const i = state.ingredientes.indexOf(removido.nome);
    if (i >= 0) {
      state.ingredientes.splice(i, 1);
      renderTags();
      renderSugestoes();
    }
  }
}

function renderFridgeSugestoes() {
  const box = $("fridgeSuggestions");
  if (!box) return;
  box.innerHTML = "";
  const usados = new Set(state.geladeira.map((it) => it.nome));
  sugeridosDeAPI.filter((s) => !usados.has(s)).slice(0, 10).forEach((s) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "sug";
    b.textContent = "+ " + s;
    b.setAttribute("role", "listitem");
    b.addEventListener("click", () => addNaGeladeira(s, $("fridgeDias").value));
    box.appendChild(b);
  });
}

function atualizarFridgeHint() {
  const hint = $("fridgeHint");
  if (!hint) return;
  const n = state.geladeira.length;
  hint.hidden = n === 0;
  $("fridgeHintCount").textContent = n;
}

function initTabs() {
  const tabBuscar = $("tabBuscar");
  const tabGeladeira = $("tabGeladeira");
  const cards = { tabBuscar: $("buscarCard"), tabGeladeira: $("geladeiraCard") };
  function ativar(tab) {
    [tabBuscar, tabGeladeira].forEach((t) => {
      const ativo = t === tab;
      t.classList.toggle("tab--active", ativo);
      t.setAttribute("aria-selected", ativo);
      cards[t.id].hidden = !ativo;
    });
    $("resultados").hidden = tab === tabGeladeira;
  }
  tabBuscar.addEventListener("click", () => ativar(tabBuscar));
  tabGeladeira.addEventListener("click", () => ativar(tabGeladeira));
  $("fridgeHintLink")?.addEventListener("click", () => ativar(tabGeladeira));
}

async function salvarPreferencias() {
  const dados = {
    ingredientes: state.ingredientes,
    soTenho: state.soTenho,
  };
  localStorage.setItem("pref-ingredientes", JSON.stringify(dados));
}

async function buscar() {
  parseInputField();
  state.buscaOffset = 0;
  listasFaltaCompleta.clear();
  await buscarPagina(false);
}

async function carregarMais() {
  state.buscaOffset += state.buscaLimite;
  await buscarPagina(true);
}

async function buscarPagina(append) {
  const btn = $("buscarBtn");
  btn.disabled = true;
  btn.classList.add("loading");
  btn.setAttribute("aria-busy", "true");

  const params = new URLSearchParams();
  params.set("ingredientes", state.ingredientes.join(","));
  params.set("limite", String(state.buscaLimite));
  params.set("offset", String(state.buscaOffset));
  if (state.soTenho) params.set("sotenho", "true");
  const vencendoTotal = [...new Set([...state.vencendo, ...itensVencendo()])];
  if (vencendoTotal.length) params.set("vencendo", vencendoTotal.join(","));
  if (state.dietas.length) params.set("dietas", state.dietas.join(","));

  try {
    const res = await fetch(`/api/receitas?${params.toString()}`);
    if (!res.ok) {
      let msg = "Verifique a conexão e tente de novo em instantes.";
      try {
        const err = await res.json();
        if (err && err.erro) msg = err.erro;
      } catch (_) {}
      throw new Error(msg);
    }
    const data = await res.json();
    state.buscaTotal = data.total || 0;
    if (append) {
      // Acrescenta resultados aos já existentes.
      appendResultados(data);
    } else {
      state.resultadosAnteriores = data.receitas || [];
      renderResultados(data);
    }
    $("resultados").scrollIntoView({ behavior: "smooth", block: "start" });
    await salvarPreferencias();
  } catch (e) {
    $("resultados").innerHTML = stateMsg(
      "error",
      "Não deu pra buscar agora",
      e.message || "Verifique a conexão e tente de novo em instantes."
    );
  } finally {
    btn.disabled = false;
    btn.classList.remove("loading");
    btn.removeAttribute("aria-busy");
  }
}

function appendResultados(data) {
  // Acumula as receitas no estado e re-renderiza mantendo o que já havia.
  const existentes = state.resultadosAnteriores || [];
  const junto = existentes.concat(data.receitas || []);
  state.resultadosAnteriores = junto;
  renderResultados({
    receitas: junto,
    total: data.total,
    tem_mais: data.tem_mais,
  });
}

function parseInputField() {
  const raw = $("ingredientField").value;
  if (raw.trim()) {
    raw.split(",").forEach((s) => addIngrediente(s.trim()));
    $("ingredientField").value = "";
    renderSugestoes();
  }
}

function initDietaChips() {
  const chipsDiv = $("dietChips");
  if (!chipsDiv) return;

  const dietaLabels = {
    "vegano": "Vegano",
    "sem lactose": "Sem lactose",
    "low carb": "Low carb",
    "sem gluten": "Sem glúten",
    "proteico": "Proteico",
    "economico": "Econômico",
    "vegetariano": "Vegetariano",
  };

  const currentDiets = new Set(state.dietas);

  Object.entries(dietaLabels).forEach(([value, label]) => {
    const existing = chipsDiv.querySelector(`[data-dieta="${value}"]`);
    if (!existing) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      btn.setAttribute("data-dieta", value);
      btn.textContent = label;
      btn.addEventListener("click", () => {
        const isActive = currentDiets.has(value);
        if (isActive) {
          currentDiets.delete(value);
          btn.classList.remove("active");
        } else {
          currentDiets.add(value);
          btn.classList.add("active");
        }
        btn.setAttribute("aria-pressed", btn.classList.contains("active"));
        state.dietas = Array.from(currentDiets);
      });
      chipsDiv.appendChild(btn);
    }
  });

  state.dietas.forEach((d) => {
    const chip = chipsDiv.querySelector(`[data-dieta="${d}"]`);
    if (chip) {
      chip.classList.add("active");
      chip.setAttribute("aria-pressed", "true");
    }
  });
}

$("ingredientField").addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === ",") {
    e.preventDefault();
    addIngrediente(e.target.value);
    e.target.value = "";
    renderSugestoes();
  }
});

$("buscarBtn").addEventListener("click", buscar);

$("soTenho").addEventListener("change", (e) => {
  state.soTenho = e.target.checked;
});

$("vencendoField").addEventListener("change", (e) => {
  state.vencendo = e.target.value.split(",").map(normalizar).filter(Boolean);
});

$("fridgeAddBtn").addEventListener("click", () => {
  addNaGeladeira($("fridgeName").value, $("fridgeDias").value);
  $("fridgeName").value = "";
});

$("fridgeName").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    addNaGeladeira($("fridgeName").value, $("fridgeDias").value);
    e.target.value = "";
  }
});

$("fridgeClearBtn").addEventListener("click", () => {
  if (!confirm("Remover todos os itens da geladeira?")) return;
  state.geladeira = [];
  salvarGeladeira();
  renderGeladeira();
  renderFridgeSugestoes();
  atualizarFridgeHint();
});

$("photoInput").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  $("photoNote").textContent = "Processando ingredientes da foto…";
  setTimeout(() => {
    const detectados = ["ovo", "tomate", "queijo", "cebola", "arroz"];
    detectados.forEach(addIngrediente);
    $("photoNote").textContent = `Ingredientes identificados: ${detectados.join(", ")}. Revise e ajuste se necessário.`;
    renderSugestoes();
  }, 800);
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

document.addEventListener("DOMContentLoaded", async () => {
  initTabs();
  await carregarSugestoes();
  await carregarPreferencias();
  initDietaChips();
  renderTags();
  renderSugestoes();
  renderGeladeira();
  renderFridgeSugestoes();
});