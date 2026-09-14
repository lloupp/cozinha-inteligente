#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cozinha Inteligente — API Flask e frontend PWA."""

from functools import lru_cache
import json
import os

from flask import Flask, jsonify, request, send_from_directory

from engine import IngredientesDatabase, calcular_receita, normalize

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEITAS_PATH = os.path.join(BASE_DIR, "receitas.json")

CUSTO_INGREDIENTE = {
    "ovo": 1.20, "queijo": 8.00, "leite": 4.50, "arroz": 5.00, "feijao": 7.00,
    "tomate": 2.50, "cebola": 1.50, "alho": 1.00, "oleo": 6.00, "sal": 1.50,
    "acucar": 3.50, "farinha de trigo": 4.00, "fermento": 2.00, "batata": 4.00,
    "cenoura": 2.50, "banana": 1.00, "maca": 3.00, "alface": 2.00, "limao": 1.50,
    "pimenta": 3.00, "massa de lasanha": 9.00, "molho de tomate": 5.00,
    "carne moida": 18.00, "presunto": 7.00, "creme de leite": 5.00,
    "macarrao": 4.50, "peito de frango": 15.00, "tapioca": 6.00,
    "polvilho": 7.00, "manteiga": 8.00, "brocolis": 4.00, "espinafre": 3.50,
    "leite de coco": 6.00, "curry": 9.00, "pao": 8.00, "leite de vaca": 4.50,
    "leite condensado": 7.00, "coco": 5.00, "amido de milho": 3.50, "maracuja": 4.00,
    "chocolate": 6.50, "biscoito": 4.00, "goiabada": 6.00, "costela": 22.00,
    "figado": 9.00, "carne": 20.00, "mandioca": 4.50, "bacon": 10.00,
    "tilapia": 15.00, "bacalhau": 35.00, "sardinha": 6.00, "peixe": 18.00,
    "laranja": 2.50, "salsa": 1.50, "abobrinha": 3.00, "couve": 2.50,
    "linguica": 12.00, "abobora": 4.00, "gengibre": 3.00, "salmao": 40.00,
    "azeite": 20.00, "camarao": 35.00, "pimentao": 3.50, "coentro": 1.50,
    "atum": 8.00, "grao de bico": 8.00, "cogumelo": 12.00, "quinoa": 18.00,
    "pepino": 2.50, "aveia": 6.00, "milho": 4.00, "requeijao": 7.00,
    "tofu": 10.00, "shoyu": 8.00, "gergelim": 6.00, "lentilha": 9.00,
    "batata doce": 4.50, "berinjela": 3.50, "abacate": 4.00, "tortilla": 8.00,
    "alecrim": 2.50, "manjericao": 2.50, "nozes": 15.00, "trigo para quibe": 6.00,
    "hortela": 2.00, "repolho": 3.00, "amendoim": 6.00, "ervilha": 4.00,
    "canela": 3.00, "mel": 12.00, "morango": 6.00, "iogurte": 5.00,
    "granola": 9.00, "acai": 10.00, "cream cheese": 9.00, "geleia": 7.00,
    "gelatina": 3.00, "maionese": 7.00, "flocos de milho": 5.00, "acafrao": 4.00,
    "fatia de pão": 8.00, "pao francês": 5.00, "café": 4.00,
}

DIETAS_VALIDAS = {
    "vegano", "sem lactose", "low carb", "sem gluten",
    "proteico", "economico", "vegetariano",
}
DIFICULDADES_VALIDAS = {"muito facil", "facil", "media", "chef"}

app = Flask(__name__, static_folder="static")
db = IngredientesDatabase(CUSTO_INGREDIENTE)


@lru_cache(maxsize=1)
def carregar_receitas():
    """Carrega e valida a estrutura mínima do catálogo uma única vez."""
    with open(RECEITAS_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    receitas = payload.get("receitas")
    if not isinstance(receitas, list):
        raise RuntimeError("receitas.json deve conter uma lista em 'receitas'")
    return receitas


def _csv_param(nome):
    return [
        normalize(item)
        for item in request.args.get(nome, "").split(",")
        if item.strip()
    ]


def _invalidos(valores, permitidos):
    return sorted(set(valores) - permitidos)


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(self), microphone=(), geolocation=()",
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
    )
    if request.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")


@app.route("/sw.js")
def sw():
    return send_from_directory("static", "sw.js")


@app.route("/icon.svg")
def icon():
    return send_from_directory("static", "icon.svg")


@app.route("/style.css")
def style():
    return send_from_directory("static", "style.css")


@app.route("/app.js")
def app_js():
    return send_from_directory("static", "app.js")


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "receitas": len(carregar_receitas())})


@app.route("/api/receitas")
def api_receitas():
    ingredientes = _csv_param("ingredientes")
    vencendo = _csv_param("vencendo")
    dietas = _csv_param("dietas")
    dificuldades = _csv_param("dificuldade")
    so_tenho = request.args.get("sotenho", "false").lower() == "true"

    dietas_invalidas = _invalidos(dietas, DIETAS_VALIDAS)
    dificuldades_invalidas = _invalidos(dificuldades, DIFICULDADES_VALIDAS)
    if dietas_invalidas or dificuldades_invalidas:
        return jsonify({
            "erro": "Filtros inválidos",
            "dietas_invalidas": dietas_invalidas,
            "dificuldades_invalidas": dificuldades_invalidas,
        }), 400

    resultados = []
    for rec in carregar_receitas():
        resultado = calcular_receita(
            rec,
            ingredientes,
            so_tenho,
            dietas,
            vencendo=vencendo,
            db=db,
            dificuldades=dificuldades,
        )
        if resultado:
            resultados.append(resultado)

    resultados.sort(
        key=lambda item: (item["score"], item["compatibilidade"]),
        reverse=True,
    )

    return jsonify({
        "total": len(resultados),
        "ingredientes": ingredientes,
        "receitas": resultados,
    })


@app.route("/api/ingredientes-sugeridos")
def api_sugeridos():
    return jsonify(db.todos_ingredientes())


@app.route("/api/dietas-validas")
def api_dietas_validas():
    return jsonify(sorted(DIETAS_VALIDAS))


@app.route("/api/dificuldades-validas")
def api_dificuldades_validas():
    return jsonify(sorted(DIFICULDADES_VALIDAS))


if __name__ == "__main__":
    print("Cozinha Inteligente — Tem em Casa?")
    print("Acesse: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
