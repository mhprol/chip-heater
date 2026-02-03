from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from heater.database import Base
from datetime import datetime

class Instance(Base):
    __tablename__ = "instances"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, unique=True)  # Evolution instance name
    phone_number = Column(String, nullable=True)
    status = Column(String, default="disconnected")  # connected, disconnected, warming

    # Warming config
    warming_enabled = Column(Boolean, default=False)
    daily_limit = Column(Integer, default=50)
    private_delay_min = Column(Integer, default=300)   # seconds
    private_delay_max = Column(Integer, default=1800)
    group_delay_min = Column(Integer, default=600)
    group_delay_max = Column(Integer, default=3600)
    schedule_start = Column(String, default="08:00")
    schedule_end = Column(String, default="22:00")

    # Stats
    messages_today = Column(Integer, default=0)
    messages_total = Column(Integer, default=0)
    warming_started_at = Column(DateTime, nullable=True)
    last_active_at = Column(DateTime, nullable=True)

    # Proxy (optional)
    proxy_url = Column(String, nullable=True)

    user = relationship("User", back_populates="instances")
    messages = relationship("Message", back_populates="instance")
