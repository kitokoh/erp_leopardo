import sqlite3
import datetime
import os # Ajout de l'import os

DB_NAME = "user_profile_data.db"

def get_db_connection():
    db_path = os.path.abspath(DB_NAME) # Obtenir le chemin absolu
    print(f"Connecting to database at: {db_path}") # Imprimer le chemin
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # BusinessProfile Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BusinessProfile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, -- Assuming a Users table with INTEGER PK
        name TEXT,
        business_type TEXT CHECK(business_type IN ('B2B', 'B2C')),
        sector_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sector_id) REFERENCES Sectors(id)
        -- FOREIGN KEY (user_id) REFERENCES Users(id) -- Uncomment if you have a Users table
    )
    """)

    # Sectors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Sectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        type_association TEXT CHECK(type_association IN ('B2B', 'B2C', 'BOTH')) NOT NULL
    )
    """)

    # UseCases Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS UseCases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    )
    """)

    # BusinessUseCases Junction Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BusinessUseCases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_profile_id INTEGER NOT NULL,
        use_case_id INTEGER NOT NULL,
        FOREIGN KEY (business_profile_id) REFERENCES BusinessProfile(id) ON DELETE CASCADE,
        FOREIGN KEY (use_case_id) REFERENCES UseCases(id) ON DELETE CASCADE,
        UNIQUE(business_profile_id, use_case_id)
    )
    """)

    # DocumentTypes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS DocumentTypes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    )
    """)

    # BusinessSelectedDocuments Junction Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BusinessSelectedDocuments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_profile_id INTEGER NOT NULL,
        document_type_id INTEGER NOT NULL,
        FOREIGN KEY (business_profile_id) REFERENCES BusinessProfile(id) ON DELETE CASCADE,
        FOREIGN KEY (document_type_id) REFERENCES DocumentTypes(id) ON DELETE CASCADE,
        UNIQUE(business_profile_id, document_type_id)
    )
    """)

    # MenuConfiguration Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MenuConfiguration (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, -- Assuming a Users table
        item_name TEXT NOT NULL,
        item_order INTEGER NOT NULL,
        is_visible BOOLEAN DEFAULT TRUE,
        module_identifier TEXT,
        parent_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES MenuConfiguration(id) ON DELETE CASCADE
        -- FOREIGN KEY (user_id) REFERENCES Users(id) -- Uncomment if you have a Users table
    )
    """)

    # Trigger to update 'updated_at' timestamp on BusinessProfile update
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_business_profile_updated_at
    AFTER UPDATE ON BusinessProfile
    FOR EACH ROW
    BEGIN
        UPDATE BusinessProfile
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.id;
    END;
    """)

    conn.commit()
    conn.close()

def seed_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Seed DocumentTypes
    document_types = [
        ('Facture', 'Document de facturation standard'),
        ('Devis', 'Proposition commerciale détaillée'),
        ('Bon de Commande', 'Document officiel d\'achat par un client'),
        ('Reçu', 'Preuve de paiement'),
        ('Bon de Livraison', 'Document attestant la livraison de marchandises'),
        ('Avoir', 'Note de crédit'),
        ('Facture Proforma', 'Facture préliminaire sans valeur comptable')
    ]
    cursor.executemany("INSERT OR IGNORE INTO DocumentTypes (name, description) VALUES (?, ?)", document_types)

    # Seed Sectors
    sectors = [
        # B2B
        ('Import/Export', 'B2B'),
        ('Fabrication Industrielle', 'B2B'),
        ('Services aux Entreprises', 'B2B'),
        ('Grossiste et Distribution', 'B2B'),
        ('Technologie et Informatique (B2B)', 'B2B'),
        ('Construction (Grands Projets)', 'B2B'),
        ('Logistique et Transport de Marchandises', 'B2B'),
        # B2C
        ('Commerce de Détail (Physique)', 'B2C'),
        ('Restauration et Hôtellerie', 'B2C'),
        ('Services à la Personne (Coiffure, Esthétique, etc.)', 'B2C'),
        ('E-commerce (Vente en ligne aux particuliers)', 'B2C'),
        ('Artisanat (Vente directe)', 'B2C'),
        ('Santé et Bien-être (Praticiens indépendants)', 'B2C'),
        ('Éducation et Formation (Cours particuliers, écoles privées)', 'B2C'),
        # BOTH
        ('Automobile (Vente et Réparation)', 'BOTH'),
        ('Immobilier (Agences)', 'BOTH'),
        ('Conseil (Petites entreprises et Particuliers)', 'BOTH')
    ]
    cursor.executemany("INSERT OR IGNORE INTO Sectors (name, type_association) VALUES (?, ?)", sectors)

    # Seed UseCases
    use_cases = [
        ('Gestion des Clients (CRM)', 'Suivi des interactions, historique, segmentation.'),
        ('Gestion des Commandes', 'Création, suivi, et gestion du cycle de vie des commandes.'),
        ('Facturation et Paiements', 'Émission de factures, suivi des paiements, relances.'),
        ('Gestion des Produits/Services', 'Catalogue produits, gestion des prix, descriptions.'),
        ('Gestion des Stocks', 'Suivi des niveaux de stock, alertes de réapprovisionnement.'),
        ('Production de Documents Commerciaux', 'Génération de devis, bons de commande, factures, etc.'),
        ('Rapports et Analyses de Vente', 'Tableaux de bord, analyse des performances.'),
        ('Gestion de Projet Simplifiée', 'Suivi des tâches et des échéances pour des petits projets.'),
        ('SAV et Support Client', 'Gestion des tickets de support, base de connaissances.'),
        ('Gestion des Fournisseurs', 'Base de données fournisseurs, suivi des achats.')
    ]
    cursor.executemany("INSERT OR IGNORE INTO UseCases (name, description) VALUES (?, ?)", use_cases)

    conn.commit()
    conn.close()
    print("Database tables created and initial data seeded.")

if __name__ == '__main__':
    create_tables()
    seed_data()
    # Example: Add a dummy user profile for testing
    # conn = get_db_connection()
    # cursor = conn.cursor()
    # try:
    #     # Get sector_id for 'E-commerce'
    #     cursor.execute("SELECT id FROM Sectors WHERE name = 'E-commerce (Vente en ligne aux particuliers)'")
    #     sector_row = cursor.fetchone()
    #     if sector_row:
    #         ecommerce_sector_id = sector_row['id']
    #         cursor.execute("""
    #         INSERT INTO BusinessProfile (user_id, name, business_type, sector_id)
    #         VALUES (?, ?, ?, ?)
    #         """, (1, 'My Online Store', 'B2C', ecommerce_sector_id))
    #         profile_id = cursor.lastrowid
    #         print(f"Inserted BusinessProfile with id: {profile_id}")

    #         # Get use_case_id for 'Gestion des Commandes'
    #         cursor.execute("SELECT id FROM UseCases WHERE name = 'Gestion des Commandes'")
    #         use_case_row = cursor.fetchone()
    #         if use_case_row:
    #             command_use_case_id = use_case_row['id']
    #             cursor.execute("""
    #             INSERT INTO BusinessUseCases (business_profile_id, use_case_id)
    #             VALUES (?, ?)
    #             """, (profile_id, command_use_case_id))
    #             print(f"Linked profile {profile_id} to use case {command_use_case_id}")

    #         conn.commit()
    # except sqlite3.IntegrityError as e:
    #     print(f"Error inserting dummy data: {e}")
    # finally:
    #     conn.close()
