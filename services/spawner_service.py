from typing import Dict, Optional, Any
import uuid
import os
from pathlib import Path
import docker
from docker.errors import ImageNotFound, APIError
from datetime import datetime

from models.Container import Container, ContainerStatus
from utils.database import SessionLocal


class SpawnerError(Exception):
    """Base exception for spawner service errors"""
    pass


class SpawnerService:
    client = None
    challenges_dir = Path("challanges")  # Base directory for challenges

    @staticmethod
    def _ensure_initialized():
        if SpawnerService.client is None:
            SpawnerService.init()

    @staticmethod
    def init():
        """Initialize Docker client and validate challenges directory"""
        try:
            SpawnerService.client = docker.from_env()
        except Exception as e:
            raise SpawnerError(f"Failed to initialize Docker client: {str(e)}")

        if not SpawnerService.challenges_dir.exists():
            raise SpawnerError(f"Challenges directory '{SpawnerService.challenges_dir}' does not exist")

    @staticmethod
    def _build_challenge_image(challenge_path: str) -> str:
        """Build Docker image from challenge directory

        Args:
            challenge_path: Path relative to challenges directory (e.g. 'SSTI/SSTI-Generator')

        Returns:
            str: Name of built image
        """
        full_path = SpawnerService.challenges_dir / challenge_path

        if not full_path.exists():
            raise SpawnerError(f"Challenge path does not exist: {full_path}")

        if not (full_path / "Dockerfile").exists():
            raise SpawnerError(f"Dockerfile not found in {full_path}")

        # Create image name from challenge path (e.g. wxpawner-ssti-generator)
        image_name = f"wxpawner-{challenge_path.lower().replace('/', '-')}"
        
        try:
            SpawnerService._ensure_initialized()
            SpawnerService.client.images.build(
                path=str(full_path),
                tag=image_name,
                rm=True  # Remove intermediate containers
            )
            return image_name
        except Exception as e:
            raise SpawnerError(f"Failed to build image: {str(e)}")

    @staticmethod
    def create_container(team_name: str, challenge_path: str, flag: str) -> Container:
        """Create container from challenge directory

        Args:
            team_name: Name of the team
            challenge_path: Path to challenge (e.g. 'SSTI/SSTI-Generator')
            flag: Flag to inject into container
        """
        try:
            # Build image from challenge directory
            image_name = SpawnerService._build_challenge_image(challenge_path)
            
            # Generate unique container name
            container_name = f"challenge-{team_name}-{uuid.uuid4().hex[:8]}"
            
            SpawnerService._ensure_initialized()
            docker_container = SpawnerService.client.containers.run(
                image=image_name,
                name=container_name,
                detach=True,
                environment={
                    "FLAG": flag,
                    "TEAM": team_name
                }
            )
            
            # Save to database
            db = SessionLocal()
            try:
                container = Container(
                    container_name=container_name,
                    image_name=image_name,
                    status=ContainerStatus.RUNNING,
                    team_name=team_name,
                    flag=flag
                )
                db.add(container)
                db.commit()
                db.refresh(container)
                return container
            finally:
                db.close()
                
        except Exception as e:
            # Cleanup on error
            try:
                if 'docker_container' in locals():
                    docker_container.remove(force=True)
            except:
                pass
            raise SpawnerError(f"Failed to create container: {str(e)}")
