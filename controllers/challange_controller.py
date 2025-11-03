from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.spawner_service import SpawnerService
from services.flag_service import FlagService
from typing import Optional
from utils.database import get_db
from models.Container import Container
from sqlalchemy import select

router = APIRouter()

class ChallengeCreate(BaseModel):
    team_name: str
    image_name: str
    flag_str: Optional[str] = None

class FlagSubmit(BaseModel):
    team_name: str
    submitted_flag: str
    container_name: str


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
        
        return {
            "status": "success",
            "container": container.to_dict()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/submit")
def submit_flag(flag_submit: FlagSubmit):
    try:
        # Cek apakah ada container dengan nama tersebut
        with get_db() as db:
            # print (flag_submit)
            stmt = select(Container).where(
                Container.container_name == flag_submit.container_name,
                Container.team_name == flag_submit.team_name
            )
            container: Container | None = db.scalars(stmt).first()
            
            if not container:
                return {"status": "error", "message": "Container or team not found"}
                
            # Check if the submitted flag matches
            stored_flag = str(container.flag)  # Convert SQLAlchemy string to Python string
            if stored_flag == flag_submit.submitted_flag:
                # Stop the container when flag is correct
                SpawnerService.stop_container(flag_submit.container_name)
                return {"status": "correct", "message": "Flag is correct! Container has been stopped."}
            else:
                return {"status": "incorrect", "message": "Flag is incorrect!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/challenges")
def get_challenges():
    try:
        challenges = SpawnerService.get_containers()
        return {"status": "success", "challenges": challenges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

