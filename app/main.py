from contextlib import asynccontextmanager

import requests

from typing import List, Optional
from pymongo.errors import DuplicateKeyError

from fastapi import FastAPI, Path, Request, status, Query
from fastapi.responses import JSONResponse

from app import schemas
from app.bootstrap.mongodb import install, DB

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    install(app)
    yield


class CepNotFoundException(Exception):
    pass


@app.exception_handler(CepNotFoundException)
async def cep_not_found_handler(request: Request, exc: CepNotFoundException):
    return JSONResponse(status_code=404, content={"message": "Cep não encontrado"})


async def save_address(address: dict):
    try:
        await DB.addresses.insert_one(address)
    except DuplicateKeyError:
        raise CepNotFoundException("Cep já existe")


@app.get("/address", response_model=List[schemas.AddressOutput], response_model_exclude_unset=True)
async def search_addresses(uf: Optional[str] = Query(None, max_length=2, min_length=2)):
    query = {"uf": uf.upper()} if uf else {}
    addresses = await DB.addresses.find(query).to_list(length=100)
    return addresses


@app.get("/address/{cep}", response_model=schemas.AddressOutput)
async def search_address_by_cep(cep: str = Path(..., max_length=9, min_length=8)):
    address = await DB.addresses.find_one({"cep": cep})
    if not address:
        response = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
        address = response.json()

        if "erro" in address:
            raise CepNotFoundException()

        await save_address(address)
    return address


@app.post("/address", response_model=schemas.AddressOutput, status_code=201)
async def create_address(address: schemas.AddressInput):
    try:
        address_dict = address.model_dump()
        await save_address(address_dict)
        return address_dict
    except CepNotFoundException as e:
        return JSONResponse(status_code=409, content={"message": str(e)})


@app.put("/address/{cep}", status_code=status.HTTP_204_NO_CONTENT)
async def update_address(cep: str, address: schemas.AddressInput):
    result = await DB.addresses.update_one(
        {"cep": cep},
        {"$set": address.model_dump()}
    )
    if result.matched_count == 0:
        raise CepNotFoundException()


@app.delete("/address/{cep}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(cep: str):
    result = await DB.addresses.delete_one({"cep": cep})
    if result.deleted_count == 0:
        raise CepNotFoundException()
