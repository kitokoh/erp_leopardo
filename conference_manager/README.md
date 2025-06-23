# Conference Manager Module

This module is responsible for managing conferences, including scheduling, note-taking, and client association.

## Features

- Create and schedule conferences.
- Take notes during conferences.
- Associate conferences with existing or new clients.
- List and view conference details.
- Generate conference reports.

## Structure

- `models.py`: Contains the data models (`Client`, `Conference`).
- `database.py`: Handles SQLite database connection and table creation. Data is persisted in a `conference_manager.db` file by default.
- `services.py`: Contains the business logic for conference management, interacting with the SQLite database.
- `tests/`: Contains unit tests for the module, using an in-memory SQLite database.

## Initialisation

Avant la première utilisation, la base de données et ses tables doivent être initialisées.
Si ce module est utilisé dans une application plus large, la fonction `conference_manager.database.init_db()` peut être appelée une fois au démarrage de l'application principale pour s'assurer que le fichier de base de données et les tables sont prêts.
Par exemple:
```python
from conference_manager import database

if __name__ == '__main__': # Dans le script principal de l'application
    database.init_db()
    # ... reste du code de l'application ...
```
Les services utilisent ensuite cette base de données pour toutes les opérations.
Les tests unitaires gèrent leur propre initialisation de base de données en mémoire.

