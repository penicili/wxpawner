from typing import Dict
class SpawnerService:
    @staticmethod
    def spawn_container(image_name:str)-> Dict[str, str]:
        # Simulasi spawning container
        container_id = "container_" + image_name + "_12345"
        print(f"Spawning container with ID: {container_id}")
        return {"container_id": container_id, "status": "spawned"}