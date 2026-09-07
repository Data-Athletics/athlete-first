import uvicorn
from fastapi import APIRouter, FastAPI

from app.observability import router as observability_router

app = FastAPI()
router = APIRouter(prefix="/api/v1")

app.include_router(router)

router.include_router(observability_router, prefix="/observability")


def start():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
