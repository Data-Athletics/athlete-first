import uvicorn
from fastapi import APIRouter, FastAPI

from app.constants import APP_PREFIX
from app.observability import router as observability_router

app = FastAPI(
    docs_url=APP_PREFIX + "/docs",
    openapi_url=APP_PREFIX + "/openapi.json",
)
router = APIRouter(prefix=APP_PREFIX)

app.include_router(router)

router.include_router(observability_router, prefix="/observability")


def start():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
