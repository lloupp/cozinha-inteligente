#!/usr/bin/env python3
"""Testes para o motor de matching do Cozinha Inteligente."""

from engine import (
    IngredientesDatabase,
    calcular_receita,
    canonicalize_ingredient,
    dieta_compativel,
    dietas_efetivas,
    esta_comprado,
    normalize,
)


class TestNormalize:
    def test_minusculo_sem_acentos(self):
        assert normalize("Cenoura") == "cenoura"
        assert normalize("Café") == "cafe"

    def test_colapsa_espacos(self):
        assert normalize("  leite   de   coco  ") == "leite de coco"

    def test_vazio(self):
        assert normalize("") == ""
        assert normalize(None) == ""

    def test_canonicaliza_variacoes_seguras(self):
        assert canonicalize_ingredient("ovos") == "ovo"
        assert canonicalize_ingredient("banana madura") == "banana"


class TestEstaComprado:
    def test_match_exato(self):
        assert esta_comprado("ovo", ["ovo", "leite"]) is True

    def test_match_alias_plural(self):
        assert esta_comprado("ovo", ["ovos"]) is True

    def test_qualificador_seguro(self):
        assert esta_comprado("banana", ["banana madura"]) is True

    def test_nao_confunde_prefixos(self):
        assert esta_comprado("salsa", ["sal"]) is False
        assert esta_comprado("salmao", ["sal"]) is False
        assert esta_comprado("leite de coco", ["leite"]) is False
        assert esta_comprado("leite condensado", ["leite"]) is False

    def test_nao_encontrado(self):
        assert esta_comprado("carne", ["ovo", "leite"]) is False


class TestDietas:
    def test_vegano_rejeita_produto_animal(self):
        assert dieta_compativel("vegano", ["tomate", "queijo"]) is False
        assert dieta_compativel("vegano", ["arroz", "tomate"]) is True

    def test_sem_lactose_nao_confunde_leite_de_coco(self):
        assert dieta_compativel("sem lactose", ["leite"]) is False
        assert dieta_compativel("sem lactose", ["leite de coco"]) is True

    def test_sem_gluten_rejeita_trigo(self):
        assert dieta_compativel("sem gluten", ["farinha de trigo"]) is False
        assert dieta_compativel("sem gluten", ["arroz"]) is True

    def test_remove_badge_contraditorio(self):
        rec = {
            "ingredientes": ["macarrao", "queijo"],
            "dietas": ["vegano", "sem lactose", "proteico"],
        }
        assert dietas_efetivas(rec) == ["proteico"]


class TestCalcularReceita:
    def receita(self, **overrides):
        base = {
            "id": 1,
            "nome": "Omelete",
            "ingredientes": ["ovo", "queijo"],
            "tempo_min": 10,
            "dificuldade": "facil",
            "dietas": ["proteico"],
            "modo": "Bata os ovos.",
        }
        base.update(overrides)
        return base

    def test_receita_completa(self):
        result = calcular_receita(
            self.receita(), ["ovo", "queijo"], False, [], None, None
        )
        assert result["compatibilidade"] == 100
        assert result["tem"] == ["ovo", "queijo"]
        assert result["falta"] == []
        assert result["custo_falta"] == 0.0

    def test_receita_parcial(self):
        rec = self.receita(ingredientes=["ovo", "queijo", "sal"])
        result = calcular_receita(rec, ["ovo"], False, [], None, None)
        assert result["compatibilidade"] == 33
        assert result["tem"] == ["ovo"]
        assert result["falta"] == ["queijo", "sal"]

    def test_so_tenho_isso(self):
        result = calcular_receita(self.receita(), ["ovo"], True, [], None, None)
        assert result is None

    def test_filtro_dieta(self):
        rec = self.receita(dietas=["proteico", "sem gluten"])
        assert calcular_receita(rec, ["ovo"], False, ["proteico"]) is not None
        assert calcular_receita(rec, ["ovo"], False, ["vegano"]) is None

    def test_filtro_dieta_rejeita_rotulo_contraditorio(self):
        rec = self.receita(
            ingredientes=["macarrao", "queijo"],
            dietas=["vegano", "sem lactose"],
        )
        assert calcular_receita(rec, [], False, ["vegano"]) is None
        result = calcular_receita(rec, [], False, [])
        assert result["dietas"] == []

    def test_filtro_dificuldade(self):
        rec = self.receita(dificuldade="facil")
        assert calcular_receita(
            rec, ["ovo"], False, [], dificuldades=["facil"]
        ) is not None
        assert calcular_receita(
            rec, ["ovo"], False, [], dificuldades=["chef"]
        ) is None

    def test_urgencia(self):
        rec = self.receita(ingredientes=["banana", "leite", "acucar"])
        result = calcular_receita(rec, ["leite"], False, [], vencendo=["banana madura"])
        assert result["urgencia"] > 0
        assert result["score"] > result["compatibilidade"]

    def test_urgencia_nao_confunde_prefixos(self):
        rec = self.receita(ingredientes=["salsa", "tomate"])
        result = calcular_receita(rec, ["tomate"], False, [], vencendo=["sal"])
        assert result["urgencia"] == 0

    def test_receita_sem_ingredientes_nao_divide_por_zero(self):
        result = calcular_receita(
            self.receita(ingredientes=[]), [], False, []
        )
        assert result["compatibilidade"] == 0

    def test_custo_faltante(self):
        db = IngredientesDatabase({"ovo": 1.20, "queijo": 8.00})
        result = calcular_receita(self.receita(), ["ovo"], False, [], db=db)
        assert result["custo_falta"] == 8.00


class TestIngredientesDatabase:
    def test_get_custo_existe(self):
        db = IngredientesDatabase({"café": 5.00, "queijo": 8.00})
        assert db.get_custo("CAFE") == 5.00
        assert db.get_custo("QUEIJO") == 8.00

    def test_get_custo_nao_existe(self):
        db = IngredientesDatabase({"ovo": 1.20})
        assert db.get_custo("carne") == 4.00

    def test_todos_ingredientes(self):
        db = IngredientesDatabase({"queijo": 8.00, "ovo": 1.20})
        assert db.todos_ingredientes() == ["ovo", "queijo"]
