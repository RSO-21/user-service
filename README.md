# user-service

This repository contains a **User microservice** for a microservices-based web application.
It is responsible for managing user data and exposing REST APIs to other services.

The service provides APIs for:

* Creating new users
* Updating existing users
* Fetching user details and listing users
* Fetching a user’s **order history**

  * Currently mocked (fake data), later intended to call a separate Orders microservice

And communication with a **PostgreSQL** database (locally via Docker, in production via Azure PostgreSQL)

---

## 1. Prerequisites

To run this project you need Docker/Compose plus access to a PostgreSQL instance (Azure or local).

Create a `.env` file with the shared database credentials (same format used by the other services in the platform):

```env
PGHOST=your_postgres_host
PGUSER=your_postgres_user
PGPASSWORD=your_postgres_password
PGPORT=5432
PGDATABASE=rso
```

---

## 2. Running with Docker

This service is usually launched via the shared `dev-stack/docker-compose.yml`, which mounts the `.env` file and connects to the shared Postgres instance. To run it on its own:

```bash
docker build -t user-service .
docker run --env-file .env -p 8004:8000 user-service
```

Swagger UI will be available at `http://localhost:8004/docs` in this standalone mode.

---

## 3. Running locally without Docker (optional)

If you prefer to run everything on your host machine:

1. Start a local PostgreSQL instance and create a database.
2. Set the `DATABASE_URL` environment variable in your shell to point to that database, for example:

```bash
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/user_service_db"
```

3. Install Python dependencies (from `requirements.txt`):

```bash
pip install -r requirements.txt
```

4. Run the application with an ASGI server (e.g. Uvicorn):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will again be available at `http://localhost:8000` and docs at `/docs`.

---

## 4. Connecting to Azure PostgreSQL (production)

In production you will usually use **Azure Database for PostgreSQL** instead of the local Postgres container.

Steps:

1. Set the PG variables (or inject `DATABASE_URL` constructed from them) for the container or deployment, including `sslmode=require` if needed.
2. Deploy the User microservice container (e.g. Azure Container Apps, App Service, or AKS) and ensure:

   * The container can reach the Azure PostgreSQL instance
  * The PG env vars resolve to your Azure credentials

In this setup you do **not** run a sidecar Postgres container; everything points to the managed Azure database.