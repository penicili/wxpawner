from sqlalchemy import Column, Integer, String
from utils.database import Base

class Container(Base):
    __tablename__ = "containers"

    id = Column(Integer, primary_key=True, index=True)
    containerName = Column(String(255), unique=True, index=True, nullable=False)
    