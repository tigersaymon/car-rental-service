# Car Rental Service API

REST API service for managing car rentals, users, cars, and payments.

## Technologies
* **Python 3.13**
* **Django 6**
* **Django REST Framework**
* **PostgreSQL**
* **Docker** & **Docker Compose**
* **Ruff** (Linter & Formatter)

---

## Installation & Setup

Prerequisites: Ensure **Docker** and **Docker Compose** are installed.

### 1. Clone the repository

    git clone [https://github.com/tigersaymon/car-rental-service.git](https://github.com/tigersaymon/car-rental-service.git)
    cd car_rental_service

### 2. Environment Configuration

Create the .env file from the sample:

    cp .env.sample .env

### 3. Run with Docker

Build and start the containers:

    docker-compose up --build

*Wait for the database connection to be established.*

### 4. Apply Migrations

Open a separate terminal window and run:

    docker-compose exec app python manage.py migrate

### 5. Create Superuser

To access the Django Admin panel:

    docker-compose exec app python manage.py createsuperuser

---

## API Access

* **API Root:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Admin Panel:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Development

We use **Ruff** for code quality. Please run checks before committing.

### Run Tests

    docker-compose exec app python manage.py test

### Linting & Formatting

Check for errors:

    docker-compose exec app ruff check .

Check formatting compliance:

    docker-compose exec app ruff format --check .

Auto-fix formatting:

    docker-compose exec app ruff format .

---

## Git Flow Guidelines

* **main**: Production-ready code.
* **develop**: Main development branch.
* **feat/feature-name**: Feature branches.
* **chore/task-name**: Configuration and maintenance.

All changes must be submitted via **Pull Request** to develop.