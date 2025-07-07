import datetime

class BusinessProfile:
    def __init__(self, id, user_id, business_type, sector_id, name=None, created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id # Assumes a User table exists elsewhere or will be added
        self.name = name
        self.business_type = business_type # 'B2B' or 'B2C'
        self.sector_id = sector_id # FK to Sectors table
        self.created_at = created_at if created_at else datetime.datetime.utcnow()
        self.updated_at = updated_at if updated_at else datetime.datetime.utcnow()

    def __repr__(self):
        return f"<BusinessProfile(id={self.id}, user_id={self.user_id}, name='{self.name}', type='{self.business_type}')>"

class Sector:
    def __init__(self, id, name, type_association): # type_association: 'B2B', 'B2C', or 'BOTH'
        self.id = id
        self.name = name
        self.type_association = type_association

    def __repr__(self):
        return f"<Sector(id={self.id}, name='{self.name}', type_association='{self.type_association}')>"

class UseCase:
    def __init__(self, id, name, description=None):
        self.id = id
        self.name = name
        self.description = description

    def __repr__(self):
        return f"<UseCase(id={self.id}, name='{self.name}')>"

class BusinessUseCase: # Junction table
    def __init__(self, id, business_profile_id, use_case_id):
        self.id = id
        self.business_profile_id = business_profile_id
        self.use_case_id = use_case_id

    def __repr__(self):
        return f"<BusinessUseCase(business_profile_id={self.business_profile_id}, use_case_id={self.use_case_id})>"

class DocumentType:
    def __init__(self, id, name, description=None):
        self.id = id
        self.name = name
        self.description = description

    def __repr__(self):
        return f"<DocumentType(id={self.id}, name='{self.name}')>"

class BusinessSelectedDocument: # Junction table
    def __init__(self, id, business_profile_id, document_type_id):
        self.id = id
        self.business_profile_id = business_profile_id
        self.document_type_id = document_type_id

    def __repr__(self):
        return f"<BusinessSelectedDocument(business_profile_id={self.business_profile_id}, document_type_id={self.document_type_id})>"

class MenuConfiguration:
    def __init__(self, id, user_id, item_name, item_order, is_visible, module_identifier=None, parent_id=None):
        self.id = id
        self.user_id = user_id # Assumes a User table exists
        self.item_name = item_name # e.g., 'Gestion des Clients', 'Paramètres'
        self.item_order = item_order # Integer for ordering
        self.is_visible = is_visible # Boolean
        self.module_identifier = module_identifier # Optional: string to identify the module to launch
        self.parent_id = parent_id # Optional: for sub-menus

    def __repr__(self):
        return f"<MenuConfiguration(user_id={self.user_id}, item_name='{self.item_name}', order={self.item_order})>"

# Example of a User class if you need it for reference, though it might exist elsewhere in your project
# class User:
#     def __init__(self, id, username, email, password_hash, created_at=None, last_login=None):
#         self.id = id
#         self.username = username
#         self.email = email
#         self.password_hash = password_hash # Store hashed passwords only!
#         self.created_at = created_at if created_at else datetime.datetime.utcnow()
#         self.last_login = last_login
#
#     def __repr__(self):
#         return f"<User(id={self.id}, username='{self.username}')>"
