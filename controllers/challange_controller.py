from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.spawner_service import SpawnerService
from services.flag_service import FlagService

router = APIRouter()



class Challange(BaseModel):
    teamName: str
    imageName: str

@router.post("/create")
def create_challange(challange: Challange):
    FlagService.create_flag(assigned_team=challange.teamName)
    SpawnerService.spawn_container(image_name=challange.imageName)