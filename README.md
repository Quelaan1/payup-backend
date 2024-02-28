# payup-backend


# step 1: install poetry globally

install poetry

```ps
curl -sSL https://install.python-poetry.org | python3 -
```

# step 2: configure poetry

optional: to create venv in project root

```ps
poetry config virtualenvs.in-project true
```



run from folder root : will create virtual environment in the project root

```ps
poetry install
```



### create .env file and copy pastr from .env.sample

get certs to connect to cockroach_db instance

# step 3: To run db-migrations

run in a new terminal A

```ps
poetry run db-migrations
```

# step 4: start uvicorn server

run in a separate terminal B

```ps
uvicorn payup_backend.main:app --reload
```
