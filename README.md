# 🚗 Car Rental Service API

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?style=flat&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST-Framework-ff1709?style=flat&logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe-Payment-008CDD?style=flat&logo=stripe&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-90%25-brightgreen)

A comprehensive, containerized backend API for a Car Rental application. This system manages the full lifecycle of vehicle rentals—from smart inventory management and scheduling to secure payments and automated notifications.

Designed with a **microservice-ready architecture**, this project implements industry best practices including **atomic transactions**, **asynchronous task processing**, and **S3-compatible storage**.

---

## 🌟 Key Features

### 🔐 Authentication & Security
* **JWT Authentication:** Secure access using `SimpleJWT` (Access/Refresh tokens) with automatic rotation.
* **Google OAuth 2.0:** Integrated social login flow.
* **Role-Based Access Control (RBAC):** Strict separation of permissions between **Customers** (read/book own data) and **Administrators** (manage inventory/users).

### 🚙 Smart Inventory & Rentals
* **Dynamic Availability:** The system automatically filters out cars that are booked for specific dates using complex DB queries.
* **Validation Logic:** Prevents overlapping bookings and ensures valid rental periods.
* **Media Storage (MinIO/S3):** Images are stored in an S3-compatible object storage (MinIO), keeping the application stateless and scalable.

### 💳 Payments (Stripe Integration)
* **Checkout Sessions:** Secure payment processing via Stripe hosted pages.
* **Complex Payment Logic:** Handles standard **Rentals**, **Overdue Fines** (1.5x multiplier), and **Cancellation Fees**.
* **Webhooks:** Asynchronous payment confirmation with **signature verification** to ensure transaction integrity.
* **Robust Error Handling:** Graceful handling of API rate limits and network errors.

### ⚡ Async & Background Tasks (Celery + Redis)
* **Real-time Notifications:** Telegram alerts sent asynchronously to avoid blocking the main thread.
* **Scheduled Tasks (Celery Beat):**
    * Daily checks for overdue rentals (automatically marks status as OVERDUE).
    * Auto-expiration of pending payment sessions.

### 🛠 Infrastructure & Code Quality
* **Dockerized:** Fully isolated environment with `docker-compose`.
* **Code Quality:** Enforced via **Ruff** linter and Pre-commit hooks.
* **Testing:** Comprehensive `APITestCase` suite with **90%+ coverage**, utilizing `boto3` mocking and dynamic date generation.

---

## 🏗 Architecture

The project runs on **6 orchestrated containers**:

1.  **`app`**: Django application (Gunicorn + WhiteNoise).
2.  **`db`**: PostgreSQL database (Persistent volume).
3.  **`redis`**: In-memory message broker for Celery and caching.
4.  **`celery`**: Worker node for processing background tasks (notifications, emails).
5.  **`celery-beat`**: Scheduler for periodic tasks.
6.  **`minio`**: S3-compatible storage server (Mocking AWS S3 locally).

---

## 🚀 Getting Started

### Prerequisites
* Docker & Docker Compose installed.
* A Telegram Bot Token (from `@BotFather`).
* Stripe Account (Test keys).
* Google Cloud Console Credentials (optional, for OAuth).

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/car-rental-service.git](https://github.com/your-username/car-rental-service.git)
    cd car-rental-service
    ```

2.  **Environment Setup:**
    Create a `.env` file from the sample:
    ```bash
    cp .env.sample .env
    ```
    *Open `.env` and populate your credentials (`STRIPE_SECRET_KEY`, `TELEGRAM_BOT_TOKEN`, etc.).*

3.  **Build and Run:**
    ```bash
    docker-compose up --build
    ```

4.  **Apply Migrations & Create Admin:**
    ```bash
    # Open a new terminal tab
    docker-compose exec app python manage.py migrate
    docker-compose exec app python manage.py createsuperuser
    ```

### Accessing the Services
* **API Root:** [http://localhost:8000/api/](http://localhost:8000/api/)
* **Swagger UI:** [http://localhost:8000/api/doc/swagger/](http://localhost:8000/api/doc/swagger/)
* **MinIO Console:** [http://localhost:9001](http://localhost:9001) (User/Pass: `minioadmin` / `minioadmin`)

---

## 📚 API Documentation

The project includes auto-generated interactive documentation via **drf-spectacular**.
Visit `/api/doc/swagger/` to explore endpoints, test requests, and view request/response schemas.

All endpoints are fully documented with:
* Request parameters and filters.
* Success and Error response examples.
* Authentication requirements.

---

## 🧪 Running Tests

Tests are written using `unittest` and `rest_framework.test.APITestCase`. The suite covers Models, Views, Serializers, and Celery Tasks.

To run tests inside the container:
```bash
docker-compose exec app python manage.py test
```

To check test coverage:
```bash
docker-compose exec app coverage run manage.py test
docker-compose exec app coverage report
```

---

## 📂 Project Structure

```text
car_rental_service/
├── car/             # Inventory management (Cars, Images)
├── config/          # Project settings, URLs, ASGI/WSGI
├── notifications/   # Telegram bot integration & Celery tasks
├── payment/         # Stripe logic, Webhooks, Services
├── rental/          # Rental booking logic & validations
├── user/            # Authentication, Profiles, OAuth
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```