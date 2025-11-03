from typing import Dict, Optional, Any, cast
import uuid
from docker import DockerClient
import os
from pathlib import Path
import docker
from docker.errors import ImageNotFound, APIError, NotFound
from datetime import datetime

from models.Container import Container, ContainerStatus
from utils.database import SessionLocal
from sqlalchemy import update


class SpawnerError(Exception):
    """Base exception for spawner service errors"""
    pass


class SpawnerService:
    client: Optional[docker.DockerClient] = None
    challenges_dir = Path("challanges")  # Base directory for challenges

    @staticmethod
    def _ensure_initialized():
        if SpawnerService.client is None:
            SpawnerService.init()
        return cast(DockerClient, SpawnerService.client)

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
            client = SpawnerService._ensure_initialized()
            client.images.build(
                path=str(full_path),
                tag=image_name,
                rm=True  # Remove intermediate containers
            )
            return image_name
        except Exception as e:
            raise SpawnerError(f"Failed to build image: {str(e)}")

    @staticmethod
    def create_container(team_name: str, image: str, flag: str) -> Container:
        try:
            image_name = SpawnerService._build_challenge_image(challenge_path=image)
            container_name = f"challenge-{team_name}-{uuid.uuid4().hex[:8]}"
            
            # Get two available ports - one for container, one for host
            container_port = 5000

            client = SpawnerService._ensure_initialized()

            docker_container = client.containers.run(
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
        
    @staticmethod
    def get_containers():
        """Get all active containers and match them with database records.
        
        Returns:
            list: List of Container objects that exist both in Docker and database
            
        Raises:
            SpawnerError: If Docker client fails or database operation fails
        """
        try:
            client = SpawnerService._ensure_initialized()
            
            # Get all containers from Docker
            docker_containers = {
                container.name: container 
                for container in client.containers.list(all=True)
            }
            
            # Get containers from database and match with Docker
            with SessionLocal() as db:
                db_containers = db.query(Container).all()
                active_containers = []
                
                for db_container in db_containers:
                    docker_container = docker_containers.get(db_container.container_name)
                    if docker_container:
                        # Update container status based on Docker state
                        docker_status = docker_container.status
                        new_status = None
                        if docker_status == 'running':
                            new_status = ContainerStatus.RUNNING.value
                        elif docker_status == 'exited':
                            new_status = ContainerStatus.STOPPED.value
                            
                        if new_status:
                            stmt = update(Container)\
                                .where(Container.container_name == db_container.container_name)\
                                .values(status=new_status)
                            db.execute(stmt)
                            db.refresh(db_container)
                        active_containers.append(db_container)
                
                # Commit any status updates
                db.commit()
                return active_containers
                
        except APIError as e:
            raise SpawnerError(f"Docker API error: {str(e)}")
        except Exception as e:
            raise SpawnerError(f"Failed to get containers: {str(e)}")
            
    @staticmethod
    def stop_container(container_name: str):
        """Stop a running container and update its status in database
        
        Args:
            container_name: Name of the container to stop
            
        Raises:
            SpawnerError: If container not found or stop operation fails
        """
        try:
            client = SpawnerService._ensure_initialized()
            
            # Get container
            container = client.containers.get(container_name)
            
            # Stop container with 10 second timeout
            container.stop(timeout=10)
            
            # Update container status in database
            with SessionLocal() as db:
                # Use SQLAlchemy update to change the status
                result = db.execute(
                    update(Container)
                    .where(Container.container_name == container_name)
                    .values(status=ContainerStatus.STOPPED.value)
                )
                
                if result.rowcount > 0:
                    db.commit()
                    return {"status": "success", "message": f"Container {container_name} stopped"}
                else:
                    raise SpawnerError(f"Container {container_name} not found in database")
                    
        except NotFound:
            raise SpawnerError(f"Container {container_name} not found in Docker")
        except APIError as e:
            raise SpawnerError(f"Docker API error: {str(e)}")
        except Exception as e:
            raise SpawnerError(f"Failed to stop container: {str(e)}")