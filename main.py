import logging

from fastapi import FastAPI

from routes.auth.otp import router as otp_router

logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome to PayUp"}


app.include_router(otp_router)
