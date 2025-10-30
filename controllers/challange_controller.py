from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.spawner_service import SpawnerService
from services.flag_service import FlagService
from typing import Optional
from utils.database import get_db
from models.Flag import Flag
from models.Container import Container

router = APIRouter()

class ChallengeCreate(BaseModel):
    team_name: str
    image_name: str
    flag_str: Optional[str] = None

@router.post("/create")
def create_challenge(challenge: ChallengeCreate):
    try:
        # Create flag for the team
        flag = FlagService.create_flag(assigned_team=challenge.team_name, flagStr=challenge.flag_str)
        
        
        # Create container from challenge directory
        container = SpawnerService.create_container(
            team_name=challenge.team_name,
            image =challenge.image_name,
            flag=flag["flag"]
        )
        
        # save ke db
        with get_db() as db:
            flag = Flag(
                flagString = flag["flag"],
                assignedTeam = challenge.team_name,
                containerId = container.image_name
            )
        
        return {
            "status": "success",
            "container": container.to_dict()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/submit")
def submit_flag(team_name: str, submitted_flag: str):
    try:
        # Verify the submitted flag
        pass
    except:
        pass