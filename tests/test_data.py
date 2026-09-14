#!/usr/bin/env python3
"""Contratos estruturais para o catálogo de receitas."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_DIETS = {
    "vegano",
    "sem lactose",
    "low carb",
    "sem gluten",
    "proteico",
    "economico",
    "vegetariano",
}
VALID_DIFFICULTIES = {"muito facil", "facil", "media", "chef"}


def load_recipes():
    with (ROOT / "receitas.json").open(encoding="utf-8") as file:
        return json.load(file)["receitas"]


def test_catalog_is_non_empty_and_ids_are_unique():
    recipes = load_recipes()
    assert recipes
    ids = [recipe["id"] for recipe in recipes]
    assert len(ids) == len(set(ids))


def test_recipe_schema_and_allowed_values():
    for recipe in load_recipes():
        assert isinstance(recipe["id"], int) and recipe["id"] > 0
        assert isinstance(recipe["nome"], str) and recipe["nome"].strip()
        assert isinstance(recipe["ingredientes"], list) and recipe["ingredientes"]
        assert all(isinstance(item, str) and item.strip() for item in recipe["ingredientes"])
        assert isinstance(recipe["tempo_min"], int) and recipe["tempo_min"] > 0
        assert recipe["dificuldade"] in VALID_DIFFICULTIES
        assert set(recipe.get("dietas", [])).issubset(VALID_DIETS)
        assert isinstance(recipe["modo"], str) and recipe["modo"].strip()


def test_recipe_ingredients_are_not_duplicated_inside_recipe():
    for recipe in load_recipes():
        normalized = [item.strip().lower() for item in recipe["ingredientes"]]
        assert len(normalized) == len(set(normalized)), recipe["nome"]
