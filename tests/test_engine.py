#!/usr/bin/env python3
"""Testes para o motor de matching do Cozinha Inteligente."""

import pytest
from engine import normalize, esta_comprado, calcular_receita, IngredientesDatabase

CUSTO_TESTE = {
    "ovo": 1.20, "queijo": 8.00, "leite": 4.50, "arroz": 5.00,
    "tomate": 2.50, "cebola": 1.50, "alho": 1.00, "sal": 1.50,
}


class TestNormalize:
    def test_minusculo_sem_acentos(self):
        assert normalize("OVEO") == "oveo"
        assert normalize("Cenoura") == "cenoura"

    def test_remove_acentos(self):
        assert normalize("coração") == "coracao"
        assert normalize("açaí") == "acai"
        assert normalize("Café") == "cafe"

    def test_strip(self):
        assert normalize("  ovo  ") == "ovo"

    def test_vazio(self):
        assert normalize("") == ""
        assert normalize(None) == ""


class TestEstaComprado:
    def test_match_exato(self):
        assert esta_comprado("ovo", ["ovo", "leite"]) is True

    def test_match_prefixo(self):
        assert esta_comprado("ovo", ["ovo cozido"]) is True

    def test_comprado_comeca_com_ingrediente(self):
        assert esta_comprado("ovo cozido", ["ovo"]) is True

    def test_nao_encontrado(self):
        assert esta_comprado("carne", ["ovo", "leite"]) is False


class TestCalcularReceita:
    def test_receita_completa(self):
        rec = {
            "id": 1,
            "nome": "Omelete",
            "ingredientes": ["ovo", "queijo"],
            "dificuldade": "facil",
            "dietas": [],
            "modo": "Bata os ovos...",
        }
        result = calcular_receita(rec, ["ovo", "queijo"], False, [], None, None)
        assert result["compatibilidade"] == 100
        assert result["tem"] == ["ovo", "queijo"]
        assert result["falta"] == []
        assert result["custo_falta"] == 0.0

    def test_receita_parcial(self):
        rec = {
            "id": 1,
            "nome": "Omelete",
            "ingredientes": ["ovo", "queijo", "sal"],
            "dificuldade": "facil",
            "dietas": [],
            "modo": "Bata os ovos...",
        }
        result = calcular_receita(rec, ["ovo"], False, [], None, None)
        assert result["compatibilidade"] == 33
        assert result["tem"] == ["ovo"]
        assert "queijo" in result["falta"]
        assert "sal" in result["falta"]

    def test_so_tenho_isso(self):
        rec = {
            "id": 1,
            "nome": "Omelete",
            "ingredientes": ["ovo", "queijo"],
            "dificuldade": "facil",
            "dietas": [],
            "modo": "Bata os ovos...",
        }
        result = calcular_receita(rec, ["ovo"], True, [], None, None)
        assert result is None

    def test_filtro_dieta(self):
        rec = {
            "id": 1,
            "nome": "Omelete",
            "ingredientes": ["ovo", "queijo"],
            "dificuldade": "facil",
            "dietas": ["vegano"],
            "modo": "Bata os ovos...",
        }
        result = calcular_receita(rec, ["ovo", "queijo"], False, ["vegano"], None, None)
        assert result is not None

        result = calcular_receita(rec, ["ovo", "queijo"], False, ["sem lactose"], None, None)
        assert result is None

    def test_urgencia(self):
        rec = {
            "id": 1,
            "nome": "Banana Split",
            "ingredientes": ["banana", "leite", "acucar"],
            "dificuldade": "facil",
            "dietas": [],
            "modo": "Misture...",
        }
        result = calcular_receita(rec, ["leite"], False, [], vencendo=["banana"])
        assert result["urgencia"] > 0
        assert result["score"] > result["compatibilidade"]


class TestIngredientesDatabase:
    def test_get_custo_existe(self):
        db = IngredientesDatabase({"ovo": 1.20, "queijo": 8.00})
        assert db.get_custo("ovo") == 1.20
        assert db.get_custo("QUEIJO") == 8.00

    def test_get_custo_nao_existe(self):
        db = IngredientesDatabase({"ovo": 1.20})
        assert db.get_custo("carne") == 4.00

    def test_todos_ingredientes(self):
        db = IngredientesDatabase({"queijo": 8.00, "ovo": 1.20})
        assert db.todos_ingredientes() == ["ovo", "queijo"]