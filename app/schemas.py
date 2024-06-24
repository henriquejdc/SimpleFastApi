from pydantic import BaseModel
from typing import List, Optional


class AddressInput(BaseModel):
    cep: str
    logradouro: str
    complemento: Optional[str] = None
    bairro: str
    localidade: str
    uf: str
    other: List[str] = []


class AddressOutput(BaseModel):
    cep: str
    logradouro: str
    complemento: Optional[str] = None
    bairro: str
    localidade: str
    uf: str 
    other: List[str] = []
