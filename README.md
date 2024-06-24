# SimpleFastApi

Projeto simples de fastapi de CEPs


No terminal:
```
python3 -m venv venv
source venv/bin/activate
```


Na venv ativa:
```
pip install -r requirements.txt 
```

Mongo:
Necessário criar um database e trocar na .env os dados

```
sudo apt-get install -y mongodb
mongosh
use 'db_name'
```

Iniciar:
```
uvicorn app.main:app --reload
```


Testes Unitários:
``` 
MONGO_DB_NAME='db_name'_test pytest tests/
```
