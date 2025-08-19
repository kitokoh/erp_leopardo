from sqlalchemy import Column, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, false
from app.db.connection import Base

class ClientOrderMoneyTransferAgent(Base):
    __tablename__ = 'client_order_money_transfer_agents'
    client_order_money_transfer_agent_id = Column(Text, primary_key=True)
    client_id = Column(Text, ForeignKey('clients.client_id'), nullable=False)
    money_transfer_agent_id = Column(Text, ForeignKey('money_transfer_agents.agent_id'), nullable=False)
    order_id = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_deleted = Column(Boolean, nullable=False, server_default=false())

    client = relationship("Client")
    money_transfer_agent = relationship("MoneyTransferAgent")

    def __repr__(self):
        return f"<ClientOrderMoneyTransferAgent id={self.client_order_money_transfer_agent_id}>"
