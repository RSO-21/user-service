# User Service

User Service is a FastAPI microservice responsible for managing users, their profiles, carts and retrieving user order history in a multi-tenant microservices system.

## Responsibilities

* User management
* Shopping cart for each user
* Fetching user order history via gRPC
* Tenant isolation using PostgreSQL schemas
* Health and readiness checks
* Prometheus metrics exposure

## Tech Stack

* **FastAPI**
* **SQLAlchemy 2.0**
* **PostgreSQL** (schema-per-tenant)
* **gRPC** (Orders Service)
* **Docker**
* **GitHub Actions**
* **pytest**

## Multi-Tenancy

* Tenant is selected by request header:

  ```
  X-Tenant-Id: <tenant_name>
  ```
* If tenant is not provided, it defaults to `public`

## API Endpoints

### Users

* `GET /users`

Lists all users in the current tenant (schema).

* `GET /users/{user_id}`

Returns a single user by ID. In case that user does not exist, it returns 
**404**.

* `PATCH /users/{user_id}`

Partially updates a user. Only fields included in the request body are updated.
In case that user does not exist, it returns **404**.

* `POST /users/{user_id}/cart/{order_id}`

Adds an order ID to the user’s cart.
Duplicates are allowed (same `order_id` can appear multiple times).
In case that user does not exist, it returns **404**.

* `DELETE /users/{user_id}/cart/{order_id}`

Removes **one occurrence** of `order_id` from the user’s cart.
If `order_id` is not present, cart is unchanged.
In case that user does not exist, it returns **404**.

* `DELETE /users/{user_id}/cart` 

Clears the entire user cart by removing all items at once.

### Orders

* `GET /users/{user_id}/orders`

Returns the user’s order history by calling the Orders Service via gRPC.
In case that user does not exist, it returns **404**.
**502** if Orders Service is unavailable or times out.

### Location

* `GET /location/autocomplete?input=<text>`

Returns address suggestions using Google Places Autocomplete API.
The input parameter must contain at least 2 characters.

* `GET /location/place?place_id=<place_id>`

Resolves a Google Place ID into a formatted address and geographic coordinates (latitude and longitude).
Returns **404** if the place cannot be resolved.


### Health

* `GET /health`

Health/readiness endpoint. Verifies database connectivity.
Returns **503** if database is unavailable.

## Testing

Tests cover:

* Tenant isolation
* User operations
* Cart behavior
* gRPC success & failure
* External HTTP calls to Google APIs
* Health checks

Run tests:

```powershell
python -m pytest
```

## CI/CD

On push to `main`:

1. Run tests
2. Build Docker image
3. Push image to Azure Container Registry

Build is blocked if tests fail.