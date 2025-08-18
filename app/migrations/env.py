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
from app.config import CONFIG  # Assuming your main config dict is named CONFIG
from app.db.connection import Base, initialize_engine_and_session, get_db_connection # Import Base and db setup
# Import all your models here so Base.metadata is populated
# Example:
# from app.accounting.models import *
# from app.api.models import *  # If you have models there
# from app.botpress_integration.models import *
# from app.calendar_module.models import *
# from app.client_management.models import * # Assuming models might be here or in subdirs
# from app.conference_manager.models import *
# from app.contact_manager.models import * # Assuming models might be here
# from app.db.models import * # If you have a central db.models or similar
# from app.media_manager.models import *
# from app.project_management.models import * # Assuming models might be here
# from app.recruitment.models import * # Assuming models might be here
# from app.status_manager.status_models import *
# from app.user_profile_management.models import *
# ... and so on for every module that defines SQLAlchemy models

# Ensure all models are loaded by importing them.
# This is a placeholder; you'll need to list all actual model modules.
# For a large application, you might have a helper in db.models to import all.
# For now, let's assume db.connection.Base.metadata will be populated
# by the application's normal import sequence when it initializes the DB.
# However, for autogenerate to work reliably, they must be imported here.

# A more robust way to ensure all models are imported if they are scattered:
# You might need to explicitly import each module containing models.
# For example, if your models are in db/models/user.py, db/models/product.py, etc.
# you would do:
# from app.db.models.user import User
# from app.db.models.product import Product
# For now, we rely on Base being populated when the app runs initialize_engine_and_session.
# This might require manual creation of initial migration scripts if autogenerate misses tables.

# Explicitly import all modules containing SQLAlchemy models that use the central Base
# This is crucial for Alembic's autogenerate feature to detect all tables and changes.
print("Alembic env.py: Importing all application models for metadata detection...")
from app.db.models.clients import client, client_assignedpersonnel, client_freightforwarders, client_transporters, clientcontacts, clientdocumentnotes, clientnotes, clientorder_moneytransferagents, clientprojectproducts, clientvisits
from app.db.models.documents import businessselecteddocuments, client_documents, defaultdocumentnotes, document_category, documenttypes, employee_document, partnerdocuments
from app.db.models.employees import employee
from app.db.models.leave import leave_balance, leave_request, leave_type
from app.db.models.locations import city, country, itemlocations, itemstoragelocations
from app.db.models.misc import (
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
from app.db.models.orders import commande, commandedocumentnotes, commandeitems
from app.db.models.performance import goal, performance_review, review_cycle
from app.db.models.products import product, product_storage_locations, productdimensions, productequivalencies, productmedialinks
from app.db.models.projects import project
from app.db.models.settings import applicationsettings, companycalendarsettings, status_setting
from app.db.models.users import role, rolepermissions, user, user_motivational_messages, user_saved_filters, usercalendarevents, usergoogleaccounts, usersessiontokens
print("Alembic env.py: All models imported.")



print("Alembic env.py: Finished importing application models.")

target_metadata = Base.metadata
# Ensure target_metadata is not None, which can happen if Base wasn't correctly populated
if target_metadata is None:
    print("CRITICAL ERROR in Alembic env.py: target_metadata is None. This usually means Base.metadata was not populated correctly. Ensure all SQLAlchemy models are imported before this line and that they use the central 'Base' from db.connection.")
    # Depending on how critical this is, you might want to raise an error:
    # raise RuntimeError("Alembic target_metadata is None. Model imports might have failed or Base not correctly used.")


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get the application's configuration
    # This assumes CONFIG is already populated when env.py is run.
    # If app_setup.load_config() needs to be called, it should happen before this.
    app_config = CONFIG

    # Determine database URL from application's config
    db_type = app_config.get('database_type', 'sqlite')
    db_url = None

    if db_type == 'sqlite':
        db_path = app_config.get('database_path', 'app_data.db')
        if not os.path.isabs(db_path):
            db_path = os.path.join(project_root, db_path) # project_root defined above
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

    # Update the Alembic config with the dynamically determined URL
    # This makes it available for engine_from_config if needed, or for direct use
    config.set_main_option('sqlalchemy.url', db_url)

    # It's often better to create the engine directly using the app's existing mechanism
    # if it's already configured for SQLAlchemy (like initialize_engine_and_session)
    # However, Alembic's default is engine_from_config.
    # If your initialize_engine_and_session creates and returns the engine, you could use that.
    # For now, let's stick to Alembic's way but ensure it uses our dynamic URL.

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}), # This will now use the db_url from above
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            # compare_type=True, # Uncomment if you want to detect column type changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
