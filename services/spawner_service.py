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
        """Build Docker image from challenge directory"""
        full_path = SpawnerService.challenges_dir / challenge_path

        if not full_path.exists():
            raise SpawnerError(f"Challenge path does not exist: {full_path}")

        # Check entrypoint.sh exists and is readable
        entrypoint_path = full_path / "entrypoint.sh"
        if not entrypoint_path.exists():
            raise SpawnerError(f"entrypoint.sh not found in {full_path}")

        print(f"Building image from path: {full_path}")
        print(f"Files in challenge directory:")


        if not (full_path / "Dockerfile").exists():
            raise SpawnerError(f"Dockerfile not found in {full_path}")

        # Create image name from challenge path
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
    def selectPort() -> int:
        """Select an available port between 8000-9000"""
        used_ports = set()
        SpawnerService._ensure_initialized()
        containers = SpawnerService.client.containers.list()
        for container in containers:
            ports = container.attrs['NetworkSettings']['Ports']
            if ports:
                for port_mappings in ports.values():
                    if port_mappings:
                        for mapping in port_mappings:
                            used_ports.add(int(mapping['HostPort']))

        for port in range(8000, 9000):
            if port not in used_ports:
                return port

        raise SpawnerError("No available ports found")

    @staticmethod
    def create_container(team_name: str, image: str, flag: str) -> Container:
        try:
            image_name = SpawnerService._build_challenge_image(challenge_path=image)
            container_name = f"challenge-{team_name}-{uuid.uuid4().hex[:8]}"
            
            # Get two available ports - one for container, one for host
            container_port = 5000

            SpawnerService._ensure_initialized()

            docker_container = SpawnerService.client.containers.run(
                image=image_name,
                name=container_name,
                detach=True,
                environment={
                    "FLAG": flag,
                    "TEAM": team_name,
                },
                ports={f"{container_port}/tcp": None},
            )
            
            docker_container.reload()
            host_port = next(iter(docker_container.attrs['NetworkSettings']['Ports'].values()))[0]['HostPort']

            # Save to database
            db = SessionLocal()
            try:
                container = Container(
                    container_name=container_name,
                    image_name=image_name,
                    status=ContainerStatus.RUNNING,
                    team_name=team_name,
                    flag=flag,
                    port=f"{host_port}"
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