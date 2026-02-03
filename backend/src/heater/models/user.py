from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from heater.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    instances = relationship("Instance", back_populates="user")
