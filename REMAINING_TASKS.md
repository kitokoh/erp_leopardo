# Tâches restantes

Voici la liste des erreurs restantes à corriger, basées sur la sortie du test de fumée (`run_import_smoketest.py`).

## Erreurs de type "Module Not Found" ou "ImportError"

Ces erreurs indiquent des problèmes avec les chemins d'importation, souvent à cause de la restructuration du projet.

- **`app.sendmail`**: `No module named 'app.db.cruds.misc.smtp_configs_crud'` (Corrigé, mais à vérifier après les autres changements)
- **`app.lite.lite_handler`**: `No module named 'html_to_pdf_util'`
- **`app.lite.lite_modal`**: `No module named 'html_to_pdf_util'`
- **`app.admin.template_edit_dialog`**: `cannot import name 'clients_crud' from 'db.cruds'`
- **`app.admin.template_management_widget`**: `cannot import name 'clients_crud' from 'db.cruds'`
- **`app.license_management.manager`**: `cannot import name 'licenses_crud' from 'db.cruds'`
- **`app.invoicing.final_invoice_data_dialog`**: `cannot import name 'clients_crud' from 'db.cruds'`
- **`app.visage.main`**: `No module named 'face_app'`
- **`app.accounting.api`**: `No module named 'api'`
- **`app.scripts.migrate_entity_contacts`**: `No module named 'db.cruds.contacts_crud'`

## Erreurs de Syntaxe (`SyntaxError`, `IndentationError`, etc.)

Ces erreurs sont des problèmes dans le code lui-même.

- **`app.pagedegrde`**: `SyntaxError: expected 'except' or 'finally' block (pagedegrde.py, line 660)` (Corrigé, mais à vérifier)
- **`app.contact_manager.contacts_manager_widget`**: `IndentationError: unexpected indent (contacts_manager_widget.py, line 462)`
- **`app.invoicing.invoice_details_dialog`**: `SyntaxError: invalid syntax (invoice_details_dialog.py, line 196)`
- **`app.invoicing.manual_invoice_dialog`**: `SyntaxError: invalid syntax (manual_invoice_dialog.py, line 235)`
- **`app.invoicing.invoice_management_widget`**: `SyntaxError: invalid syntax (invoice_management_widget.py, line 357)`

## Erreurs de Nom (`NameError`)

Ces erreurs indiquent l'utilisation d'une variable ou d'un module non défini.

- **`app.contact_manager.google_settings_dialog`**: `NameError: name 'os' is not defined`
- **`app.contact_manager.contact_list_widget`**: `NameError: name 'os' is not defined`

## Erreurs d'Attribut (`AttributeError`)

- **`app.migrations.env`**: `AttributeError: module 'alembic.context' has no attribute 'config'`

## Erreurs liées à l'environnement ou aux fichiers manquants

- **Multiples fichiers de traduction**: `FileNotFoundError: [Errno 2] No such file or directory: 'translations/ts/app_*.ts'`. Ces erreurs peuvent probablement être ignorées pour le moment.
- **`app.camera_management.camera_management_widget`**: `libpulse-mainloop-glib.so.0: cannot open shared object file`. C'est une erreur de bibliothèque système, probablement pas à corriger dans le code Python directement.

## Approche suggérée

1.  **Corriger les `NameError` et `IndentationError`** car ils sont souvent rapides à résoudre (imports manquants, copier-coller incorrects).
2.  **Corriger les `SyntaxError`** dans les fichiers de facturation (`invoicing`).
3.  **S'attaquer aux `ImportError` et `ModuleNotFoundError`**. Cela nécessitera de trouver l'emplacement correct des modules (par exemple `html_to_pdf_util`, `clients_crud`, etc.) et de corriger les chemins d'importation. C'est la tâche la plus longue.
4.  **Examiner l'`AttributeError`** dans `app.migrations.env`. Cela peut être lié à une mauvaise configuration d'Alembic.
5.  Une fois toutes les erreurs corrigées, relancer le test de fumée pour s'assurer que tout est en ordre.
6.  Enfin, tenter de lancer l'application principale (`python app/run_gui_app.py`).
