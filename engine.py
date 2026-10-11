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


def _tokens(texto: str) -> set:
    return set(normalize(texto).split())


# Palavras que NÃO são nome de ingrediente (quantidades, preparos).
_STOPWORDS_NOME = {
    # números/medidas
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "1/2", "1/4", "3/4",
    "xicara", "xicaras", "chavena", "copo", "copos",
    "colher", "colheres", "colherinha", "colherinhas",
    "sopa", "cha", "cafe",
    "lata", "latas", "caixa", "caixas", "caixinha", "caixinhas",
    "pacote", "pacotes", "embalagem", "sache", "saches",
    "unidade", "unidades", "dente", "dentes", "ramo", "ramos",
    "fatia", "fatias", "pedaco", "pedacos", "cubos", "cubo",
    "ml", "l", "litro", "litros", "g", "kg", "grama", "gramas",
    "kilo", "mg", "cc",
    # preparo / qualidade
    "picado", "picada", "picados", "picadas", "ralado", "ralada",
    "fatiado", "fatiada", "cortado", "cortada", "derretido", "derretida",
    "morno", "morna", "quente", "frio", "fria", "gelado", "gelada",
    "opcional", "graus", "aproximadamente", "cerca", "temperatura",
    "ambiente", "bem",
    # preposições/conjunções
    "de", "do", "da", "dos", "das", "e", "ou", "com", "sem", "para",
    "a", "o", "as", "os", "ao", "aos", "no", "na", "em", "um", "uma",
    "1/2", "1/3", "2/3",
}

# Tokens numéricos e frações — regex
import re as _re
_NUM_RE = _re.compile(r"^\d+([.,]\d+)?$|^[0-9]+/[0-9]+$")


def nome_base_ingrediente(texto: str) -> str:
    """Extrai o nome canônico de um ingrediente cru com quantidade/preparo.

    Ex.: "1 caixinha de creme de leite (previamente gelado)" → "creme de leite"
          "200 ml de leite quente" → "leite"
          "alfavaca" (fresco) → "alfavaca"  (preserva nomes reais com 'fresco')
    """
    t = normalize(texto)
    # remove parênteses e conteúdo interno
    t = _re.sub(r"\([^)]*\)", " ", t)
    # separa tokens
    tokens = [tok.strip(".,;:?!\"'()[]") for tok in t.split()]
    # filtra stopwords e números
    limpos = [
        tok for tok in tokens
        if tok and tok not in _STOPWORDS_NOME and not _NUM_RE.match(tok)
    ]
    return " ".join(limpos)[:80]


def _fuzzy_match(a: str, b: str) -> bool:
    """Match inteligente entre dois nomes de ingredientes.

    Regras (todas sobre texto normalizado), por segurança contra falsos
    positivos:
    - igualdade exata
    - um nome contém o outro como substring, quando o menor tem >=4 chars
      (evita 'sal' bater em 'salmao', mas pega 'peito de frango' ⊃ 'frango')
    - interseção de tokens equivalentes (singular/plural/normalizados)
    """
    if not a or not b:
        return False
    if a == b:
        return True
    if len(a) >= 4 and a in b:
        return True
    if len(b) >= 4 and b in a:
        return True
    ta = {_singularizar(t) for t in _tokens(a)}
    tb = {_singularizar(t) for t in _tokens(b)}
    return bool(ta & tb)


_DEF_PLURAIS = [
    ("oes", "ao"), ("aes", "ao"), ("aos", "ao"),
    ("eis", "el"), ("ois", "ol"),
    ("ns", "m"), ("izes", "iz"), ("izes", "iz"),
    ("res", "r"), ("s", ""),
]


def _singularizar(w: str) -> str:
    """Redução aproximada de plural para singular (PT-BR simples)."""
    if len(w) <= 2:
        return w
    for suf, sub in _DEF_PLURAIS:
        if w.endswith(suf) and len(w) > len(suf):
            return w[: -len(suf)] + sub
    return w


def esta_comprado(ing: str, possuidos_norm: List[str]) -> bool:
    """Verifica se o ingrediente está presente nos possuídos."""
    ing_norm = normalize(ing)
    return any(_fuzzy_match(ing_norm, p) for p in possuidos_norm)


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
    ingredientes = rec.get("ingredientes") or []
    if not ingredientes:
        return None

    # Mapeia cada ingrediente cru para seu nome canônico para matching/custo.
    bases = [nome_base_ingrediente(i) for i in ingredientes]
    tem_idx = [i for i, b in enumerate(bases) if b and esta_comprado(b, possuidos_norm)]
    tem = [ingredientes[i] for i in tem_idx]
    falta = [ingredientes[i] for i, b in enumerate(bases) if b and not esta_comprado(b, possuidos_norm)]
    # ingrediente sem base extraível (degenerado) conta como faltando
    falta += [ingredientes[i] for i, b in enumerate(bases) if not b]

    compat = round(100 * len(tem) / len(ingredientes)) if ingredientes else 0

    if so_tenho_isso and falta:
        return None

    rec_dietas = rec.get("dietas", [])
    if dietas:
        if not all(d in rec_dietas for d in dietas):
            return None

    custo_falta = 0.0
    if db:
        custo_falta = sum(db.get_custo(b) for i, b in enumerate(bases) if ingredientes[i] in falta)
    else:
        custo_falta = sum(DEFAULT_CUSTO for _ in falta)

    urgencia = 0
    if vencendo:
        for b in bases:
            if not b:
                continue
            if any(_fuzzy_match(b, normalize(v)) for v in vencendo):
                urgencia += 30

    return {
        "id": rec.get("id"),
        "nome": rec.get("nome") or "Receita sem nome",
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