import asyncio
import os
import pytest

from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING

from app.bootstrap.mongodb import DB
from app.main import app

load_dotenv()


@pytest.fixture(scope="module")
def app_main():
    # Configuração do MongoDB para testes
    client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    app.db = DB.get_collection("addresses")

    yield app

    async def cleanup():
        await client.drop_database(os.getenv("MONGO_DB_NAME"))

    asyncio.run(cleanup())
    client.close()


@pytest.mark.asyncio(scope='session')
async def test_db_available(app_main):
    assert hasattr(app_main, 'db'), "app.db não está definido."


@pytest.mark.asyncio(scope='session')
async def test_search_address(app_main):
    transport = ASGITransport(app=app_main)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Adiciona um endereço para teste
        address_data = {
            "cep": "12432-330",
            "logradouro": "Rua Teste",
            "bairro": "Centro",
            "localidade": "São Paulo",
            "uf": "SP"
        }
        await client.post("/address", json=address_data)

        # Testa a busca pelo endereço criado
        response = await client.get("/address/12432-330")

    assert response.status_code == 200
    assert "cep" in response.json()


@pytest.mark.asyncio(scope='session')
async def test_create_address_conflict(app_main):
    await app_main.db.create_index([("cep", ASCENDING)], unique=True)

    async with AsyncClient(transport=ASGITransport(app=app_main), base_url="http://test") as client:
        address_data = {
            "cep": "12620-311",
            "logradouro": "Rua Teste 2",
            "bairro": "Centro",
            "localidade": "São Paulo",
            "uf": "SP"
        }
        # Primeira tentativa de criação
        response = await client.post("/address", json=address_data)
        assert response.status_code == 201

        # Segunda tentativa de criação com o mesmo CEP
        response = await client.post("/address", json=address_data)
        assert response.status_code == 409
        assert response.json()["message"] == "Cep já existe"


@pytest.mark.asyncio(scope='session')
async def test_search_address_not_found(app_main):
    async with AsyncClient(transport=ASGITransport(app=app_main), base_url="http://test") as client:
        response = await client.get("/address/12420-339")
    assert response.status_code == 404
    assert response.json()["message"] == "Cep não encontrado"


@pytest.mark.asyncio(scope='session')
async def test_create_address(app_main):
    async with AsyncClient(transport=ASGITransport(app=app_main), base_url="http://test") as client:
        address_data = {
            "cep": "12420-331",
            "logradouro": "Rua Teste 2",
            "bairro": "Centro",
            "localidade": "São Paulo",
            "uf": "SP"
        }
        response = await client.post("/address", json=address_data)
    assert response.status_code == 201
    assert response.json()["cep"] == "12420-331"


@pytest.mark.asyncio(scope='session')
async def test_update_address(app_main):
    async with AsyncClient(transport=ASGITransport(app=app_main), base_url="http://test") as client:
        # Adiciona um endereço para teste
        post_address_data = {
            "cep": "12220-330",
            "logradouro": "Rua Teste",
            "bairro": "Centro",
            "localidade": "São Paulo",
            "uf": "SP"
        }
        address_data = {
            "cep": "12220-330",
            "logradouro": "Rua Nova",
            "bairro": "Oeste",
            "localidade": "São Paulo",
            "uf": "SP"
        }
        await client.post("/address", json=post_address_data)
        response = await client.put("/address/12220-330", json=address_data)
    assert response.status_code == 204


@pytest.mark.asyncio(scope='session')
async def test_delete_address(app_main):
    async with AsyncClient(transport=ASGITransport(app=app_main), base_url="http://test") as client:
        # Adiciona um endereço para teste
        address_data = {
            "cep": "12420-330",
            "logradouro": "Rua Teste",
            "bairro": "Centro",
            "localidade": "São Paulo",
            "uf": "SP"
        }
        await client.post("/address", json=address_data)
        response = await client.delete("/address/12420-330")
    assert response.status_code == 204
