from fastapi import FastAPI, HTTPException
from controllers.challange_controller import router as challange_router

app = FastAPI()

app.include_router(challange_router,prefix="/challange")

@app.get("/")
def root():
    return {"message": "Hello, World!"}
