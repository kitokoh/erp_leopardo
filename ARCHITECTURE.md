# Application Architecture

This document outlines the refactored architecture of the application, focusing on the Model-View-Controller (MVC) pattern, database management, and overall project structure.

## 1. Directory Structure

The application now follows a more organized, MVC-like directory structure within the `app/` directory:

-   **`app/core/`**: Contains core application logic, such as configuration (`config.py`), application setup (`app_setup.py`), and the main initializer (`initializer.py`). This is the heart of the application's startup process.

-   **`app/models/`**: Contains all SQLAlchemy ORM models, organized into subdirectories based on their domain (e.g., `users`, `clients`, `products`). This is the "Model" part of MVC.

-   **`app/views/`**: Contains the PyQt5 GUI components of the application. This is the "View" part of MVC. It is further subdivided by feature (e.g., `client_management`, `gui`).

-   **`app/services/`**: Contains the business logic and services that act as the "Controller" part of MVC. This includes authentication (`auth/`), API services (`api/`), and other core application services.

-   **`app/db/`**: Contains all database-related code, including:
    -   `connection.py`: The single source of truth for creating database connections and sessions.
    -   `cruds/`: All database access logic (Create, Read, Update, Delete) is encapsulated in these modules. They use the SQLAlchemy ORM.
    -   `seeders/`: Scripts to populate the database with initial data.
    -   `migrations/`: The Alembic migration scripts.

## 2. Database Management

The database schema is now managed exclusively by **Alembic**.

-   **Source of Truth:** The SQLAlchemy models in `app/models/db/` are the definitive source for the database schema. All table creations and modifications should be done by updating the models and then using Alembic to generate a new migration.
-   **Initial Migration:** The migration `a6de7289bbd6_initial_migration.py` is the new initial migration for the entire database. It contains the `CREATE TABLE` statements for all tables in the application.
-   **Initialization:** The function `app.core.initializer.initialize_database()` is the single entry point for setting up the database. It performs the following steps in order:
    1.  Runs `alembic upgrade head` to apply all migrations and create the schema.
    2.  Initializes the SQLAlchemy engine and session factory.
    3.  If the database was newly created, it runs all data seeders from `app/db/seeders/`.

## 3. Data Access Layer

All database interactions should now go through the SQLAlchemy ORM.

-   **No Raw SQL:** Raw SQL queries should be avoided. All database operations should be performed using SQLAlchemy sessions and the ORM models.
-   **CRUD Modules:** The `app/db/cruds/` directory contains modules that encapsulate all database operations for each model. For example, all operations on the `User` model are in `app/db/cruds/users/users_crud.py`.
-   **Session Management:** Database sessions should be obtained by calling `app.db.connection.get_db_connection()`.

## 4. Application Entry Point

-   **`main.py`**: This is the main entry point for the application. It should:
    1.  Load the application configuration.
    2.  Call `app.core.initializer.initialize_database()` to set up the database.
    3.  Launch the login window.
    4.  If the login is successful, launch the main application window.
