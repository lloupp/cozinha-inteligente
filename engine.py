#!/usr/bin/env python3
"""Motor determinístico de matching do Cozinha Inteligente."""

from typing import Any, Dict, List, Optional
import unicodedata

DEFAULT_CUSTO = 4.00
URGENCY_BOOST = 30

# Variações explícitas evitam o antigo matching por prefixo, que fazia
# "sal" casar com "salsa"/"salmao" e "leite" com "leite de coco".
INGREDIENT_ALIASES = {
    "ovos": "ovo",
    "tomates": "tomate",
    "cebolas": "cebola",
    "bananas": "banana",
    "batatas": "batata",
    "cenouras": "cenoura",
    "macas": "maca",
    "limoes": "limao",
    "pimentoes": "pimentao",
}

TRAILING_QUALIFIERS = {
    "cozido",
    "cozida",
    "cozidos",
    "cozidas",
    "fresco",
    "fresca",
    "frescos",
    "frescas",
    "maduro",
    "madura",
    "maduros",
    "maduras",
}


def normalize(texto: str) -> str:
    """Normaliza caixa, acentos e espaços para comparação consistente."""
    if not texto:
        return ""
    texto = " ".join(str(texto).strip().lower().split())
    decomposed = unicodedata.normalize("NFKD", texto)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def canonicalize_ingredient(texto: str) -> str:
    """Converte variações seguras de um ingrediente para uma forma canônica."""
    normalized = normalize(texto)
    if not normalized:
        return ""

    parts = normalized.split()
    while len(parts) > 1 and parts[-1] in TRAILING_QUALIFIERS:
        parts.pop()
    normalized = " ".join(parts)
    return INGREDIENT_ALIASES.get(normalized, normalized)


class IngredientesDatabase:
    """Banco simples de custos estimados por ingrediente."""

    def __init__(self, custos: Dict[str, float]):
        self._custos = {normalize(k): v for k, v in custos.items()}

    def get_custo(self, nome: str) -> float:
        return self._custos.get(normalize(nome), DEFAULT_CUSTO)

    def todos_ingredientes(self) -> List[str]:
        return sorted(self._custos.keys())


def esta_comprado(ing: str, possuidos_norm: List[str]) -> bool:
    """Verifica presença sem falsos positivos por prefixo."""
    ingrediente = canonicalize_ingredient(ing)
    possuidos = {canonicalize_ingredient(p) for p in possuidos_norm if p}
    return bool(ingrediente) and ingrediente in possuidos


def calcular_receita(
    rec: Dict[str, Any],
    possuidos_norm: List[str],
    so_tenho_isso: bool,
    dietas: List[str],
    vencendo: Optional[List[str]] = None,
    db: Optional[IngredientesDatabase] = None,
    dificuldades: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Calcula compatibilidade, filtros, custo faltante e prioridade por vencimento."""
    ingredientes = rec.get("ingredientes", [])
    tem = [i for i in ingredientes if esta_comprado(i, possuidos_norm)]
    falta = [i for i in ingredientes if not esta_comprado(i, possuidos_norm)]

    compat = round(100 * len(tem) / len(ingredientes)) if ingredientes else 0
    if so_tenho_isso and falta:
        return None

    rec_dietas = {normalize(d) for d in rec.get("dietas", [])}
    dietas_norm = {normalize(d) for d in dietas if d}
    if dietas_norm and not dietas_norm.issubset(rec_dietas):
        return None

    dificuldades_norm = {normalize(d) for d in (dificuldades or []) if d}
    if dificuldades_norm and normalize(rec.get("dificuldade", "")) not in dificuldades_norm:
        return None

    custo_falta = sum(
        (db.get_custo(i) if db else DEFAULT_CUSTO)
        for i in falta
    )

    urgencia = 0
    vencendo_norm = {
        canonicalize_ingredient(v) for v in (vencendo or []) if v
    }
    if vencendo_norm:
        for ingrediente in ingredientes:
            if canonicalize_ingredient(ingrediente) in vencendo_norm:
                urgencia += URGENCY_BOOST

    return {
        "id": rec["id"],
        "nome": rec["nome"],
        "compatibilidade": compat,
        "tem": tem,
        "falta": falta,
        "custo_falta": round(custo_falta, 2),
        "tempo_min": rec.get("tempo_min"),
        "dificuldade": rec.get("dificuldade"),
        "dietas": rec.get("dietas", []),
        "modo": rec.get("modo", ""),
        "urgencia": urgencia,
        "score": compat + urgencia,
    }
