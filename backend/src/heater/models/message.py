from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from heater.database import Base
from datetime import datetime

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("instances.id"))
    peer_number = Column(String) # The number we are talking to
    message_type = Column(String) # text, audio, reaction
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    instance = relationship("Instance", back_populates="messages")
