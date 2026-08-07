#!/usr/bin/env python3
"""
Módulo de engine de matching para o Cozinha Inteligente.
Funções para normalizar texto, verificar ingredientes e calcular compatibilidade.
"""

from typing import Optional, List, Dict, Any

DEFAULT_CUSTO = 4.00


class IngredientesDatabase:
    """Banco de dados de ingredientes com custos."""

    def __init__(self, custos: Dict[str, float]):
        self._custos = {k.lower(): v for k, v in custos.items()}

    def get_custo(self, nome: str) -> float:
        return self._custos.get(nome.lower(), DEFAULT_CUSTO)

    def todos_ingredientes(self) -> List[str]:
        return sorted(self._custos.keys())


def normalize(texto: str) -> str:
    """Minúsculo e sem acentos para comparação robusta."""
    if not texto:
        return ""
    t = texto.lower().strip()
    repl = {
        "á": "a", "à": "a", "â": "a", "ã": "a", "ä": "a",
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "í": "i", "ì": "i", "î": "i", "ï": "i",
        "ó": "o", "ò": "o", "ô": "o", "õ": "o", "ö": "o",
        "ú": "u", "ù": "u", "û": "u", "ü": "u", "ç": "c",
    }
    for k, v in repl.items():
        t = t.replace(k, v)
    return t


def esta_comprado(ing: str, possuidos_norm: List[str]) -> bool:
    """Verifica se o ingrediente está presente nos possuídos."""
    ing_norm = normalize(ing)
    for p in possuidos_norm:
        if ing_norm == p or ing_norm.startswith(p) or p.startswith(ing_norm):
            return True
    return False


def calcular_receita(
    rec: Dict[str, Any],
    possuidos_norm: List[str],
    so_tenho_isso: bool,
    dietas: List[str],
    vencendo: Optional[List[str]] = None,
    db: Optional[IngredientesDatabase] = None,
) -> Optional[Dict[str, Any]]:
    """
    Calcula a compatibilidade de uma receita com os ingredientes possuídos.
    Retorna dict com os detalhes ou None se incompatível.
    """
    ingredientes = rec.get("ingredientes", [])
    tem = [i for i in ingredientes if esta_comprado(i, possuidos_norm)]
    falta = [i for i in ingredientes if not esta_comprado(i, possuidos_norm)]

    compat = round(100 * len(tem) / len(ingredientes)) if ingredientes else 0

    if so_tenho_isso and falta:
        return None

    rec_dietas = rec.get("dietas", [])
    if dietas:
        if not all(d in rec_dietas for d in dietas):
            return None

    custo_falta = 0.0
    if db:
        custo_falta = sum(db.get_custo(i) for i in falta)
    else:
        custo_falta = sum(DEFAULT_CUSTO for _ in falta)

    urgencia = 0
    if vencendo:
        ven_norm = [normalize(v) for v in vencendo]
        for i in ingredientes:
            in_norm = normalize(i)
            if any(
                in_norm == v or in_norm.startswith(v) or v.startswith(in_norm)
                for v in ven_norm
            ):
                urgencia += 30

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