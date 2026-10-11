#!/usr/bin/env python3
"""Testes de integridade do dataset receitas.json.

Protege a base de receitas (carregada em produção pela API) contra
regressões de estrutura: JSON válido, campos obrigatórios presentes
e ids únicos.
"""

import json
import os

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECEITAS_PATH = os.path.join(BASE_DIR, "receitas.json")


@pytest.fixture(scope="module")
def receitas():
    with open(RECEITAS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "receitas" in data, "JSON deve ter a chave 'receitas'"
    return data["receitas"]


def test_dataset_nao_vazio(receitas):
    assert isinstance(receitas, list)
    assert len(receitas) > 0


def test_campos_obrigatorios(receitas):
    obrigatorios = ("id", "nome", "ingredientes", "modo")
    for rec in receitas:
        for campo in obrigatorios:
            assert rec.get(campo), (
                f"Receita id={rec.get('id')!r} sem campo obrigatorio '{campo}'"
            )


def test_ingredientes_sao_listas_nao_vazias(receitas):
    for rec in receitas:
        ingredientes = rec.get("ingredientes")
        assert isinstance(ingredientes, list)
        assert len(ingredientes) > 0, f"Receita id={rec.get('id')!r} sem ingredientes"


def test_ids_unicos(receitas):
    ids = [rec.get("id") for rec in receitas]
    assert len(ids) == len(set(ids)), "Existem ids de receita duplicados"
