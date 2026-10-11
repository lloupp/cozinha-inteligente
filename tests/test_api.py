#!/usr/bin/env python3
"""Testes para as rotas Flask."""

import pytest
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestAPIs:
    def test_index(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Tem em Casa?" in resp.data

    def test_manifest(self, client):
        resp = client.get("/manifest.json")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["name"] == "Tem em Casa? — Cozinha Inteligente"

    def test_api_receitas_vazia(self, client):
        resp = client.get("/api/receitas?ingredientes=")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "total" in data
        assert "receitas" in data

    def test_api_receitas_com_ingredientes(self, client):
        resp = client.get("/api/receitas?ingredientes=ovo,tomate")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["total"] >= 1
        for r in data["receitas"]:
            assert "nome" in r
            assert "compatibilidade" in r
            assert "falta" in r
            assert "custo_falta" in r

    def test_api_ingredientes_sugeridos(self, client):
        resp = client.get("/api/ingredientes-sugeridos")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert "ovo" in data

    def test_api_dietas_validas(self, client):
        resp = client.get("/api/dietas-validas")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "vegano" in data
        assert "sem lactose" in data

    def test_filtro_so_tenho_isso(self, client):
        resp = client.get("/api/receitas?ingredientes=ovo,queijo,sal&sotenho=true")
        data = json.loads(resp.data)
        for r in data["receitas"]:
            assert r["falta"] == []
            assert r["compatibilidade"] == 100

    def test_filtro_dieta_vegano(self, client):
        resp = client.get("/api/receitas?ingredientes=arroz&dietas=vegano")
        data = json.loads(resp.data)
        recs = data["receitas"]
        for r in recs:
            assert "vegano" in r["dietas"]

    def test_paginacao(self, client):
        resp = client.get("/api/receitas?ingredientes=&limite=10")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data["receitas"]) == 10
        assert data["total"] > 10
        assert data["tem_mais"] is True
        resp2 = client.get("/api/receitas?ingredientes=&limite=10&offset=10")
        data2 = json.loads(resp2.data)
        assert data2["offset"] == 10

    def test_dieta_invalida(self, client):
        resp = client.get("/api/receitas?ingredientes=ovo&dietas=keto")
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "erro" in data

    def test_limite_invalido_usa_default(self, client):
        resp = client.get("/api/receitas?ingredientes=ovo&limite=abc")
        assert resp.status_code == 200