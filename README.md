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

To run this project you need:

* Docker Compose

You will also need a PostgreSQL instance:

* **Local**: provided via Docker Compose
* **Production**: Azure Database for PostgreSQL

---

## 2. Local development with Docker Compose

### 2.1. Environment variables

The service expects a `DATABASE_URL` environment variable.
When using Docker Compose locally, this is already set in `docker-compose.yml` to point to the Postgres container.

You do not need to set anything manually for local Docker use.

### 2.2. Build and run

From the project root (where `docker-compose.yml` is located), run:

```bash
docker-compose up --build
```

This will:

* Start a PostgreSQL container
* Build and start the User service container
* Create the database schema on startup (for development purposes)

The API will then be available at:

* `http://localhost:8000`
* OpenAPI/Swagger UI: `http://localhost:8000/docs`

### 2.3. Stopping the services

To stop:

```bash
docker-compose down
```

To remove volumes (database data) as well:

```bash
docker-compose down -v
```

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

1. Set the `DATABASE_URL` environment variable for the container or deployment, using the Azure connection string format (including `sslmode=require` if needed).
2. Deploy the User microservice container (e.g. Azure Container Apps, App Service, or AKS) and ensure:

   * The container can reach the Azure PostgreSQL instance
   * `DATABASE_URL` is correctly configured in that environment

In this setup you do **not** run the `db` service from `docker-compose.yml` in production.