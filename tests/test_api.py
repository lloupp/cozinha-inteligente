#!/usr/bin/env python3
"""Testes para as rotas Flask."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


class TestAPIs:
    def test_index(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Tem em Casa?" in resp.data
        assert b"difficultyChips" in resp.data

    def test_manifest(self, client):
        resp = client.get("/manifest.json")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["name"] == "Tem em Casa? — Cozinha Inteligente"

    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["receitas"] >= 1

    def test_security_headers(self, client):
        resp = client.get("/")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert "default-src 'self'" in resp.headers["Content-Security-Policy"]

    def test_api_sem_cache(self, client):
        resp = client.get("/api/health")
        assert resp.headers["Cache-Control"] == "no-store"

    def test_api_receitas_vazia(self, client):
        resp = client.get("/api/receitas?ingredientes=")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total" in data
        assert "receitas" in data

    def test_api_receitas_com_ingredientes(self, client):
        resp = client.get("/api/receitas?ingredientes=ovo,tomate")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        for receita in data["receitas"]:
            assert "nome" in receita
            assert "compatibilidade" in receita
            assert "falta" in receita
            assert "custo_falta" in receita

    def test_api_ingredientes_sugeridos(self, client):
        resp = client.get("/api/ingredientes-sugeridos")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert "ovo" in data

    def test_api_dietas_validas(self, client):
        resp = client.get("/api/dietas-validas")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "vegano" in data
        assert "sem lactose" in data

    def test_api_dificuldades_validas(self, client):
        resp = client.get("/api/dificuldades-validas")
        assert resp.status_code == 200
        data = resp.get_json()
        assert set(data) == {"muito facil", "facil", "media", "chef"}

    def test_filtro_so_tenho_isso(self, client):
        resp = client.get("/api/receitas?ingredientes=ovo,queijo,sal&sotenho=true")
        assert resp.status_code == 200
        for receita in resp.get_json()["receitas"]:
            assert receita["falta"] == []
            assert receita["compatibilidade"] == 100

    def test_filtro_dieta_vegano(self, client):
        resp = client.get("/api/receitas?ingredientes=arroz&dietas=vegano")
        assert resp.status_code == 200
        for receita in resp.get_json()["receitas"]:
            assert "vegano" in receita["dietas"]

    def test_filtro_dificuldade(self, client):
        resp = client.get("/api/receitas?ingredientes=ovo&dificuldade=chef")
        assert resp.status_code == 200
        for receita in resp.get_json()["receitas"]:
            assert receita["dificuldade"] == "chef"

    def test_rejeita_filtros_invalidos(self, client):
        resp = client.get("/api/receitas?dietas=inexistente&dificuldade=impossivel")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["dietas_invalidas"] == ["inexistente"]
        assert data["dificuldades_invalidas"] == ["impossivel"]

    def test_sal_nao_vira_salsa_ou_salmao(self, client):
        resp = client.get("/api/receitas?ingredientes=sal")
        assert resp.status_code == 200
        for receita in resp.get_json()["receitas"]:
            assert "salsa" not in receita["tem"]
            assert "salmao" not in receita["tem"]

    def test_leite_nao_vira_leite_de_coco(self, client):
        resp = client.get("/api/receitas?ingredientes=leite")
        assert resp.status_code == 200
        for receita in resp.get_json()["receitas"]:
            assert "leite de coco" not in receita["tem"]
            assert "leite condensado" not in receita["tem"]
