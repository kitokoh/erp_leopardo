from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import os
import sys

# Add the project root directory to sys.path
# This allows Alembic to find your application's modules
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

# Now you can import your app's modules
from app.core.config import CONFIG
from app.db.connection import Base

# Explicitly import all modules containing SQLAlchemy models
print("Alembic env.py: Importing all application models for metadata detection...")
from app.models.db.clients import client, client_assignedpersonnel, client_freightforwarders, client_transporters, clientcontacts, clientdocumentnotes, clientnotes, clientorder_moneytransferagents, clientprojectproducts, clientvisits
from app.models.db.documents import businessselecteddocuments, client_documents, defaultdocumentnotes, document_category, documenttypes, employee_document, partnerdocuments
from app.models.db.employees import employee
from app.models.db.leave import leave_balance, leave_request, leave_type
from app.models.db.locations import city, country, itemlocations, itemstoragelocations
from app.models.db.misc import (
    activitylog, assetassignments, assetmedialinks, businessprofile,
    businessusecases, candidateprogress, candidates, companies,
    company_expenses, company_factures, companyassets, companypersonnel,
    companypersonnelcontacts, contactlistmembers, contactlists, contacts,
    contactsynclog, coverpages, coverpagetemplates, emailreminders,
    entitycontacts, experiencemedia, experiencerelatedentities,
    experiences, experiencetags, freightforwarders, importantdates,
    internalstockitems, interviews, invoices, jobopenings, kpis,
    licenses, media_items, menuconfiguration, moneytransferagents,
    motivational_messages, partnercategories, partnercategorylink,
    partnercontacts, partners, passwordresettokens, permissions,
    proforma_invoice_items, proforma_invoices, recruitmentsteps,
    referents, regions, reportconfigfields, reportconfigfilters,
    reportconfigurations, savtickets, scheduledemails, sectors,
    smtpconfigs, tags, tasks, teammembers, templatecategories,
    templates, transporters, usecases
)
from app.models.db.orders import commande, commandedocumentnotes, commandeitems
from app.models.db.performance import goal, performance_review, review_cycle
from app.models.db.products import product, product_storage_locations, productdimensions, productequivalencies, productmedialinks
from app.models.db.projects import project
from app.models.db.settings import applicationsettings, companycalendarsettings, status_setting
from app.models.db.users import role, rolepermissions, user, user_motivational_messages, user_saved_filters, usercalendarevents, usergoogleaccounts, usersessiontokens
print("Alembic env.py: All models imported.")


print("Alembic env.py: Finished importing application models.")

target_metadata = Base.metadata
if target_metadata is None:
    print("CRITICAL ERROR in Alembic env.py: target_metadata is None. This usually means Base.metadata was not populated correctly. Ensure all SQLAlchemy models are imported before this line and that they use the central 'Base' from db.connection.")
    raise RuntimeError("Alembic target_metadata is None. Model imports might have failed or Base not correctly used.")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    app_config = CONFIG
    db_type = app_config.get('database_type', 'sqlite')
    db_url = None

    if db_type == 'sqlite':
        db_path = app_config.get('database_path', 'app_data.db')
        if not os.path.isabs(db_path):
            db_path = os.path.join(project_root, db_path)
        db_url = f"sqlite:///{db_path}"
    elif db_type == 'postgresql':
        pg_user = app_config.get('postgresql_user')
        pg_password = app_config.get('postgresql_password')
        pg_host = app_config.get('postgresql_host')
        pg_port = app_config.get('postgresql_port')
        pg_dbname = app_config.get('postgresql_dbname')
        if not all([pg_user, pg_password, pg_host, pg_port, pg_dbname]):
            raise ValueError("Missing required PostgreSQL connection parameters in config for Alembic.")
        db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_dbname}"
    else:
        raise ValueError(f"Unsupported database_type for Alembic: {db_type}")

    config.set_main_option('sqlalchemy.url', db_url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
