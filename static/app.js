// Tem em Casa? — Cozinha Inteligente
// Lógica do frontend: ingredientes, filtros, persistência e chamada à API.

const state = {
  ingredientes: [],
  dietas: [],
  dificuldades: [],
  soTenho: false,
  vencendo: [],
  resultadosAnteriores: [],
};

const RING_C = 150.8;
const STORAGE_KEY = "pref-ingredientes";
const $ = (id) => document.getElementById(id);

function normalizar(s) {
  return String(s || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
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
      el.style.strokeDashoffset = el.getAttribute("data-offset");
    });
  });
}

function renderTags() {
  const box = $("tagsInput");
  const input = $("ingredientField");
  box.querySelectorAll(".tag").forEach((tag) => tag.remove());

  state.ingredientes.forEach((ing, index) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.innerHTML = `${escapeHtml(ing)} <button type="button" aria-label="Remover ${escapeHtml(ing)}">×</button>`;
    tag.querySelector("button").addEventListener("click", () => {
      state.ingredientes.splice(index, 1);
      renderTags();
      renderSugestoes();
    });
    box.insertBefore(tag, input);
  });
}

function addIngrediente(value) {
  const ingrediente = normalizar(value);
  if (ingrediente && !state.ingredientes.includes(ingrediente)) {
    state.ingredientes.push(ingrediente);
    renderTags();
  }
}

let sugeridosDeAPI = [];

async function carregarSugestoes() {
  try {
    const res = await fetch("/api/ingredientes-sugeridos");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    sugeridosDeAPI = await res.json();
  } catch (_error) {
    sugeridosDeAPI = [];
  }
}

function renderSugestoes() {
  const box = $("suggestions");
  box.innerHTML = "";
  const usados = new Set(state.ingredientes);

  sugeridosDeAPI
    .filter((s) => !usados.has(normalizar(s)))
    .slice(0, 12)
    .forEach((s) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "sug";
      btn.textContent = s;
      btn.setAttribute("role", "listitem");
      btn.addEventListener("click", () => {
        addIngrediente(s);
        renderSugestoes();
      });
      box.appendChild(btn);
    });
}

function dificuldadeLabel(d) {
  const map = {
    "muito facil": "Muito fácil",
    facil: "Fácil",
    media: "Média",
    chef: "Chef",
  };
  return map[d] || d;
}

function dificuldadeClass(d) {
  return `dif-${String(d || "").replace(/\s+/g, "-")}`;
}

function stateMsg(kind, title, body) {
  const icon = kind === "error"
    ? `<div class="state-msg__icon state-msg__icon--error" aria-hidden="true">
         <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
           <circle cx="12" cy="12" r="10"/><path d="M12 8v5M12 16h.01"/>
         </svg>
       </div>`
    : `<div class="state-msg__icon" aria-hidden="true">
         <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
           <path d="M4 11h16v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8z"/>
           <path d="M4 11l2-6h12l2 6"/><path d="M9 15h6"/>
         </svg>
       </div>`;
  return `<div class="state-msg">${icon}<h3>${escapeHtml(title)}</h3><p>${escapeHtml(body)}</p></div>`;
}

function renderResultados(data) {
  state.resultadosAnteriores = data.receitas || [];
  const box = $("resultados");
  const copyBtn = $("copiarLista");
  box.innerHTML = "";

  if (!state.resultadosAnteriores.length) {
    copyBtn.hidden = true;
    box.innerHTML = stateMsg(
      "empty",
      "Nada encaixou ainda",
      "Tente mais um ingrediente ou solte os filtros."
    );
    return;
  }

  const header = document.createElement("div");
  header.className = "results-header";
  const total = state.resultadosAnteriores.length;
  header.innerHTML = `<h2>O que dá pra fazer</h2><span class="count">${total} receita${total === 1 ? "" : "s"}</span>`;
  box.appendChild(header);

  state.resultadosAnteriores.forEach((r, idx) => {
    const el = document.createElement("article");
    const completo = r.compatibilidade >= 100;
    const urgente = r.urgencia > 0;
    el.className = `recipe${urgente ? " recipe--urgente" : ""}${completo ? " recipe--completo" : ""}`;
    el.style.animationDelay = `${Math.min(idx, 12) * 0.05}s`;

    const tem = r.tem.length ? r.tem.map(escapeHtml).join(", ") : "—";
    const falta = r.falta.length ? r.falta.map(escapeHtml).join(", ") : "nenhum";
    const custo = r.custo_falta > 0
      ? `~R$ ${Number(r.custo_falta).toFixed(2)} a mais`
      : "Você tem tudo · R$ 0";
    const badges = (r.dietas || [])
      .map((d) => `<span class="badge">${escapeHtml(d)}</span>`)
      .join("");
    const urgencia = urgente ? `<span class="badge urgencia">Use antes de vencer</span>` : "";
    const tempo = Number.isFinite(Number(r.tempo_min)) ? `${r.tempo_min} min` : "Tempo não informado";

    el.innerHTML = `
      <header class="recipe__head">
        <div>
          <h3 class="recipe__title">${escapeHtml(r.nome)}</h3>
          <p class="recipe__meta">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
            </svg>
            ${escapeHtml(tempo)}
          </p>
        </div>
        <div class="compat-ring" aria-label="${r.compatibilidade}% compatível">
          ${compatRingSVG(r.compatibilidade)}
        </div>
      </header>
      <div class="badges">
        <span class="badge ${dificuldadeClass(r.dificuldade)}">${escapeHtml(dificuldadeLabel(r.dificuldade))}</span>
        ${badges}${urgencia}
      </div>
      <div class="recipe__lists">
        <p class="recipe__tem"><span class="label">Tem</span> <span><b>${tem}</b></span></p>
        <p class="recipe__falta"><span class="label">Falta</span> <span><b>${falta}</b></span></p>
        <p class="recipe__custo ${r.custo_falta === 0 ? "zero" : ""}"><span class="label">Custo</span> <span><b>${escapeHtml(custo)}</b></span></p>
      </div>
      <details class="recipe__modo">
        <summary class="modo-summary">Modo de preparo</summary>
        <p class="modo-detail">${escapeHtml(r.modo)}</p>
      </details>
    `;
    box.appendChild(el);
  });

  copyBtn.hidden = false;
  animateRings(box);
}

async function copyText(texto) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(texto);
    return;
  }
  const area = document.createElement("textarea");
  area.value = texto;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  document.execCommand("copy");
  area.remove();
}

function initCopyButton() {
  const btn = $("copiarLista");
  btn.addEventListener("click", async () => {
    const faltantes = new Set();
    state.resultadosAnteriores.slice(0, 10).forEach((r) => {
      (r.falta || []).forEach((item) => faltantes.add(item));
    });

    if (!faltantes.size) {
      btn.textContent = "Você tem tudo!";
      setTimeout(() => { btn.textContent = "Copiar lista de compras"; }, 1800);
      return;
    }

    const texto = `Lista de compras:\n${Array.from(faltantes).sort().map((item) => `- ${item}`).join("\n")}`;
    try {
      await copyText(texto);
      btn.textContent = "Copiado!";
    } catch (_error) {
      btn.textContent = "Não foi possível copiar";
    }
    setTimeout(() => { btn.textContent = "Copiar lista de compras"; }, 1800);
  });
}

function initFilterChips(containerId, attribute, stateKey) {
  const container = $(containerId);
  if (!container) return;

  container.querySelectorAll(`[${attribute}]`).forEach((btn) => {
    const value = normalizar(btn.getAttribute(attribute));
    const sync = () => {
      const active = state[stateKey].includes(value);
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-pressed", String(active));
    };

    sync();
    btn.addEventListener("click", () => {
      if (state[stateKey].includes(value)) {
        state[stateKey] = state[stateKey].filter((item) => item !== value);
      } else {
        state[stateKey] = [...state[stateKey], value];
      }
      sync();
    });
  });
}

function carregarPreferencias() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return;

  try {
    const dados = JSON.parse(raw);
    state.ingredientes = Array.isArray(dados.ingredientes) ? dados.ingredientes.map(normalizar).filter(Boolean) : [];
    state.dietas = Array.isArray(dados.dietas) ? dados.dietas.map(normalizar).filter(Boolean) : [];
    state.dificuldades = Array.isArray(dados.dificuldades) ? dados.dificuldades.map(normalizar).filter(Boolean) : [];
    state.vencendo = Array.isArray(dados.vencendo) ? dados.vencendo.map(normalizar).filter(Boolean) : [];
    state.soTenho = Boolean(dados.soTenho);
  } catch (_error) {
    localStorage.removeItem(STORAGE_KEY);
  }
}

function salvarPreferencias() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    ingredientes: state.ingredientes,
    dietas: state.dietas,
    dificuldades: state.dificuldades,
    vencendo: state.vencendo,
    soTenho: state.soTenho,
  }));
}

function parseInputField() {
  const input = $("ingredientField");
  if (!input.value.trim()) return;
  input.value.split(",").forEach((part) => addIngrediente(part));
  input.value = "";
  renderSugestoes();
}

async function buscar() {
  parseInputField();
  state.vencendo = $("vencendoField").value.split(",").map(normalizar).filter(Boolean);
  state.soTenho = $("soTenho").checked;

  const btn = $("buscarBtn");
  btn.disabled = true;
  btn.classList.add("loading");
  btn.setAttribute("aria-busy", "true");

  const params = new URLSearchParams();
  params.set("ingredientes", state.ingredientes.join(","));
  if (state.soTenho) params.set("sotenho", "true");
  if (state.vencendo.length) params.set("vencendo", state.vencendo.join(","));
  if (state.dietas.length) params.set("dietas", state.dietas.join(","));
  if (state.dificuldades.length) params.set("dificuldade", state.dificuldades.join(","));

  try {
    const res = await fetch(`/api/receitas?${params.toString()}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.erro || `HTTP ${res.status}`);
    renderResultados(data);
    salvarPreferencias();
    $("resultados").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (_error) {
    $("copiarLista").hidden = true;
    $("resultados").innerHTML = stateMsg(
      "error",
      "Não deu pra buscar agora",
      "Verifique a conexão e tente novamente."
    );
  } finally {
    btn.disabled = false;
    btn.classList.remove("loading");
    btn.removeAttribute("aria-busy");
  }
}

function bindEvents() {
  $("ingredientField").addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      addIngrediente(event.target.value);
      event.target.value = "";
      renderSugestoes();
    }
  });

  $("buscarBtn").addEventListener("click", buscar);
  $("soTenho").addEventListener("change", (event) => {
    state.soTenho = event.target.checked;
  });
  $("vencendoField").addEventListener("change", (event) => {
    state.vencendo = event.target.value.split(",").map(normalizar).filter(Boolean);
  });
  $("photoInput").addEventListener("change", (event) => {
    const file = event.target.files[0];
    $("photoNote").textContent = file
      ? "Foto recebida. A detecção automática por imagem ainda não está ativa nesta versão."
      : "";
  });
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  carregarPreferencias();
  $("soTenho").checked = state.soTenho;
  $("vencendoField").value = state.vencendo.join(", ");
  initFilterChips("dietChips", "data-dieta", "dietas");
  initFilterChips("difficultyChips", "data-dificuldade", "dificuldades");
  initCopyButton();
  bindEvents();
  await carregarSugestoes();
  renderTags();
  renderSugestoes();
});
