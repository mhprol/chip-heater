from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from heater.database import Base
from datetime import datetime

class WarmingSession(Base):
    __tablename__ = "warming_sessions"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("instances.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    messages_sent = Column(Integer, default=0)
    status = Column(String, default="active") # active, completed, failed
