from sqlalchemy import Column, Integer, String, DateTime
from utils.database import Base
import docker
from datetime import datetime

class ContainerStatus:
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    REMOVED = "removed"

class Container(Base):
    __tablename__ = "containers"

    id = Column(Integer, primary_key=True, index=True)
    container_name = Column(String(255), unique=True, index=True, nullable=False)
    image_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default=ContainerStatus.CREATING)
    team_name = Column(String(100), nullable=False)
    port = Column(Integer, nullable=True)  # External port if exposed
    flag = Column(String(255), nullable=True)  # Challenge flag if applicable
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        """Convert container record to dictionary for API responses"""
        return {
            "id": self.id,
            "container_name": self.container_name,
            "image_name": self.image_name,
            "status": self.status,
            "team_name": self.team_name,
            "port": self.port,
            "created_at": str(self.created_at)
        }