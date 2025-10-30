from fastapi import FastAPI, HTTPException
from controllers.challange_controller import router as challange_router
from services.spawner_service import SpawnerService

app = FastAPI()

app.include_router(challange_router,prefix="/challange")

@app.on_event("startup")
def startup_event():
    # Inisialisasi SpawnerService saat aplikasi dimulai
    SpawnerService.init()
    
    
@app.get("/")
def root():
    return {"message": "Hello, World!"}
