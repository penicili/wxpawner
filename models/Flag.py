from sqlalchemy import Column, Integer, String
from utils.database import Base

class Flag(Base):
    __tablename__ = "flags"

    id = Column(Integer, primary_key=True, index=True)
    flagString = Column(String(255), unique=True, index=True, nullable=False)
    assignedTeam = Column(String(100), nullable=True)
    containerId = Column(String(100), nullable=True)