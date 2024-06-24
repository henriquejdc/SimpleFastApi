import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Variáveis de ambiente
MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")  # Padrão: 'viacep' se não estiver definido

# Inicialização do cliente MongoDB
MONGODB_CLIENT = AsyncIOMotorClient(MONGO_URL)
DB = MONGODB_CLIENT[MONGO_DB_NAME]


def install(app: FastAPI):
    """
    Configura a coleção 'addresses' do banco de dados no aplicativo FastAPI.

    Cria um índice único no campo 'cep' e adiciona a coleção ao objeto 'app'.
    """
    try:
        app.db = DB.get_collection("addresses")
        DB.addresses.create_index([("cep", ASCENDING)], unique=True)
        logger.info(f"Connected to MongoDB and configured the '{MONGO_DB_NAME}.addresses' collection.")
    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
        raise e
