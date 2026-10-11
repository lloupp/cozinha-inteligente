#!/usr/bin/env python3
"""Testes para o motor de matching do Cozinha Inteligente."""

import pytest
from engine import (
    normalize,
    esta_comprado,
    calcular_receita,
    IngredientesDatabase,
    nome_base_ingrediente,
)

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

    def test_sem_falso_positivo_prefixo_curto(self):
        # 'sal' não deve bater em 'salmao' ou 'salada'
        assert esta_comprado("salmao", ["sal"]) is False
        assert esta_comprado("salada", ["sal"]) is False
        # mas deve bater em 'sal grosso'
        assert esta_comprado("sal grosso", ["sal"]) is True

    def test_plural_simples(self):
        assert esta_comprado("ovos", ["ovo"]) is True
        assert esta_comprado("queijos", ["queijo"]) is True


class TestNomeBaseIngrediente:
    def test_remove_quantidade(self):
        assert nome_base_ingrediente("3 ovos") == "ovos"
        assert nome_base_ingrediente("200 ml de leite") == "leite"

    def test_remove_medida_e_preparo(self):
        assert "creme" in nome_base_ingrediente("1 caixinha de creme de leite")
        assert nome_base_ingrediente("peito de frango") == "peito frango"

    def test_remove_parenteses(self):
        r = nome_base_ingrediente("1 caixinha de leite (use a lata como medida)")
        assert "(" not in r and ")" not in r

    def test_vazio(self):
        assert nome_base_ingrediente("") == ""
        assert nome_base_ingrediente("   ") == ""


class TestCalcularReceita:
    def test_receita_completa(self):
        rec = {
            "id": 1, "nome": "Omelete",
            "ingredientes": ["ovo", "queijo"],
            "dificuldade": "facil", "dietas": [], "modo": "Bata os ovos...",
        }
        result = calcular_receita(rec, ["ovo", "queijo"], False, [], None, None)
        assert result["compatibilidade"] == 100
        assert result["tem"] == ["ovo", "queijo"]
        assert result["falta"] == []
        assert result["custo_falta"] == 0.0

    def test_receita_parcial(self):
        rec = {
            "id": 1, "nome": "Omelete",
            "ingredientes": ["ovo", "queijo", "sal"],
            "dificuldade": "facil", "dietas": [], "modo": "Bata os ovos...",
        }
        result = calcular_receita(rec, ["ovo"], False, [], None, None)
        assert result["compatibilidade"] == 33
        assert result["tem"] == ["ovo"]
        assert "queijo" in result["falta"]
        assert "sal" in result["falta"]

    def test_so_tenho_isso(self):
        rec = {
            "id": 1, "nome": "Omelete",
            "ingredientes": ["ovo", "queijo"],
            "dificuldade": "facil", "dietas": [], "modo": "Bata os ovos...",
        }
        result = calcular_receita(rec, ["ovo"], True, [], None, None)
        assert result is None

    def test_filtro_dieta(self):
        rec = {
            "id": 1, "nome": "Omelete",
            "ingredientes": ["ovo", "queijo"],
            "dificuldade": "facil", "dietas": ["vegano"], "modo": "Bata os ovos...",
        }
        result = calcular_receita(rec, ["ovo", "queijo"], False, ["vegano"], None, None)
        assert result is not None
        result = calcular_receita(rec, ["ovo", "queijo"], False, ["sem lactose"], None, None)
        assert result is None

    def test_urgencia(self):
        rec = {
            "id": 1, "nome": "Banana Split",
            "ingredientes": ["banana", "leite", "acucar"],
            "dificuldade": "facil", "dietas": [], "modo": "Misture...",
        }
        result = calcular_receita(rec, ["leite"], False, [], vencendo=["banana"])
        assert result["urgencia"] > 0
        assert result["score"] > result["compatibilidade"]

    def test_ingredientes_com_quantidade_no_dataset(self):
        rec = {
            "id": 1, "nome": "Bechamel",
            "ingredientes": ["1 litro de leite", "2 colheres de manteiga", "sal"],
            "dificuldade": "media", "dietas": [], "modo": "...",
        }
        result = calcular_receita(rec, ["leite", "manteiga", "sal"], False, [], None, None)
        assert result is not None
        assert result["compatibilidade"] == 100
        assert result["falta"] == []


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
