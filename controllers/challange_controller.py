from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.spawner_service import SpawnerService
from services.flag_service import FlagService

router = APIRouter()

class ChallengeCreate(BaseModel):
    team_name: str
    image_name: str

@router.post("/create")
def create_challenge(challenge: ChallengeCreate):
    try:
        # Create flag for the team
        flag = FlagService.create_flag(assigned_team=challenge.team_name)
        
        # Create container from challenge directory
        container = SpawnerService.create_container(
            team_name=challenge.team_name,
            challenge_path="SSTI/SSTI-Generator",  # Path relative to challenges dir
            flag=flag["flag"]
        )
        
        return {
            "status": "success",
            "container": container.to_dict()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))