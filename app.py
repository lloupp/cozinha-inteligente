#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cozinha Inteligente — "Tem em Casa?"
App web que sugere receitas com base nos ingredientes que o usuário já tem,
priorizando zero desperdício de alimentos.

Autor: Hermes (Eduardo)
"""
import json
import os
from flask import Flask, request, jsonify, send_from_directory
from engine import (
    normalize,
    calcular_receita,
    IngredientesDatabase,
)

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

DIETAS_VALIDAS = {"vegano", "sem lactose", "low carb", "sem gluten", "proteico", "economico", "vegetariano"}

app = Flask(__name__, static_folder="static")
db = IngredientesDatabase(CUSTO_INGREDIENTE)


def carregar_receitas():
    with open(RECEITAS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["receitas"]


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


@app.route("/api/receitas")
def api_receitas():
    raw = request.args.get("ingredientes", "")
    ingredientes = [normalize(x) for x in raw.split(",") if x.strip()]
    so_tenho = request.args.get("sotenho", "false").lower() == "true"
    vencendo = [normalize(x) for x in request.args.get("vencendo", "").split(",") if x.strip()]
    dietas = [normalize(x) for x in request.args.get("dietas", "").split(",") if x.strip()]

    receitas = carregar_receitas()
    resultados = []
    for rec in receitas:
        r = calcular_receita(rec, ingredientes, so_tenho, dietas, vencendo, db)
        if r:
            resultados.append(r)

    resultados.sort(key=lambda x: (x["score"], x["compatibilidade"]), reverse=True)

    return jsonify({
        "total": len(resultados),
        "ingredientes": ingredientes,
        "receitas": resultados,
    })


@app.route("/api/ingredientes-sugeridos")
def api_sugeridos():
    conhecidos = sorted(set(CUSTO_INGREDIENTE.keys()))
    return jsonify(conhecidos)


@app.route("/api/dietas-validas")
def api_dietas_validas():
    return jsonify(sorted(DIETAS_VALIDAS))


if __name__ == "__main__":
    print("Cozinha Inteligente — Tem em Casa?")
    print("Acesse: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)