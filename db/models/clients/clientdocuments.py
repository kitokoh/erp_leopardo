from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Clientdocuments(Base):
    __tablename__ = 'client_documents'
    # = Column(String, primary_key=True)
    # = Column(String, nullable=False)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String, nullable=False)
    # = Column(String, nullable=False)
    # = Column(String, nullable=False)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(Date)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String, ForeignKey('clients.client_id'))
    # = Column(String, ForeignKey('projects.project_id'))
    # = Column(String, ForeignKey('commandes.commande_id'))
    # = Column(String, ForeignKey('templates.template_id'))
    # = Column(String, ForeignKey('users.user_id'))
    # = Column(String, ForeignKey('commandes.commande_id'))
    # = Column(String, ForeignKey('clientdocuments.document_id'))

    client_rel = relationship('Clients')
    project_rel = relationship('Projects')
    commande_rel = relationship('Commandes')
    template_rel = relationship('Templates')
    user_rel = relationship('Users')
    commande_rel = relationship('Commandes')
    clientdocument_rel = relationship('Clientdocuments')

    def __repr__(self):
        return f'<Clientdocuments #={self.#}>'
    client_rel = relationship('Clients')
    project_rel = relationship('Projects')
    template_rel = relationship('Templates')
    user_rel = relationship('Users')
    clientdocument_rel = relationship('Clientdocuments')
    client_rel = relationship('Clients')
    project_rel = relationship('Projects')
    commande_rel = relationship('Commandes')
    template_rel = relationship('Templates')
    user_rel = relationship('Users')
    commande_rel = relationship('Commandes')
    clientdocument_rel = relationship('Clientdocuments')
