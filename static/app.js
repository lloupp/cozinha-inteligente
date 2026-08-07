// Tem em Casa? — Cozinha Inteligente
// Lógica do frontend: tags de ingredientes, filtros, foto (stub), chamada à API.

const state = {
  ingredientes: [],
  dietas: [],
  soTenho: false,
  vencendo: [],
  preferencias: [],
  resultadosAnteriores: [],
};

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
  state.resultadosAnteriores = data.receitas || [];

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
  header.innerHTML = `
    <h2>O que dá pra fazer</h2>
    <span class="count">${n} receita${n === 1 ? "" : "s"}</span>
  `;
  box.appendChild(header);

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
    el.setAttribute("data-descricao", escapeHtml(r.nome + " - " + r.modo));

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
      <div class="recipe__modo">
        <summary class="modo-summary">Modo de preparo</summary>
        <p class="modo-detail">${escapeHtml(r.modo)}</p>
      </div>
    `;
    box.appendChild(el);
  });

  animateRings(box);
  rendererizarBotaoCopiar();
}

function rendererizarBotaoCopiar() {
  const btn = $("copiarLista");
  if (!btn) return;

  btn.onclick = () => {
    const todosFaltam = new Set();
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
  const favores = localStorage.getItem("pref-ingredientes");
  if (favores) {
    const dados = JSON.parse(favores);
    state.ingredientes = dados.ingredientes || [];
    state.soTenho = dados.soTenho || false;
    renderTags();
  }
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
  const btn = $("buscarBtn");
  btn.disabled = true;
  btn.classList.add("loading");
  btn.setAttribute("aria-busy", "true");

  const params = new URLSearchParams();
  params.set("ingredientes", state.ingredientes.join(","));
  if (state.soTenho) params.set("sotenho", "true");
  if (state.vencendo.length) params.set("vencendo", state.vencendo.join(","));
  if (state.dietas.length) params.set("dietas", state.dietas.join(","));

  try {
    const res = await fetch(`/api/receitas?${params.toString()}`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    renderResultados(data);
    $("resultados").scrollIntoView({ behavior: "smooth", block: "start" });
    await salvarPreferencias();
  } catch (e) {
    $("resultados").innerHTML = stateMsg(
      "error",
      "Não deu pra buscar agora",
      "Verifique a conexão e tente de novo em instantes."
    );
  } finally {
    btn.disabled = false;
    btn.classList.remove("loading");
    btn.removeAttribute("aria-busy");
  }
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

$("photoInput").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  $("photoNote").textContent = "Analisando imagem…";
  setTimeout(() => {
    const detectados = ["ovo", "tomate", "queijo", "cebola", "arroz"];
    detectados.forEach(addIngrediente);
    $("photoNote").textContent = `Detectado: ${detectados.join(", ")}`;
    renderSugestoes();
  }, 800);
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

document.addEventListener("DOMContentLoaded", async () => {
  await carregarSugestoes();
  await carregarPreferencias();
  initDietaChips();
  renderTags();
  renderSugestoes();
});