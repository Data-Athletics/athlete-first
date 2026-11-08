from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.auth.router import router as auth_router
from app.biometrics.router import biometrics_router
from app.core.config import app_settings
from app.core.database import ModelBase, get_engine
from app.core.dtos import PermissionDeniedResponseDTO, SimpleResponseDTO
from app.core.exceptions import PermissionException
from app.observability import router as observability_router
from app.team.router import router as team_router
from app.user.router import router as user_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Runs on server startup and yields until server shutdown."""

    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)

    yield


app = FastAPI(
    lifespan=lifespan,
    root_path=app_settings.api_prefix,
    title=app_settings.title,
    debug=app_settings.debug,
    responses={
        400: {"model": SimpleResponseDTO},
        403: {"model": PermissionDeniedResponseDTO},
    },
    swagger_ui_parameters={
        "persistAuthorization": app_settings.enable_swagger_persistent_auth
    },
)


router = APIRouter()
app.include_router(router)

router.include_router(
    observability_router, prefix="/observability", tags=["Observability"]
)
router.include_router(user_router, prefix="/user", tags=["User"])
router.include_router(biometrics_router, prefix="/biometrics", tags=["Biometrics"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(team_router, prefix="/team", tags=["Team"])


@app.exception_handler(PermissionException)
async def permission_exception_handler(request: Request, exc: PermissionException):
    """Handle custom permission denied exceptions"""

    content = PermissionDeniedResponseDTO(
        detail=exc.detail, code=exc.status_code, reason=exc.reason
    )

    return JSONResponse(
        headers=exc.headers,
        status_code=exc.status_code,
        content=jsonable_encoder(content.model_dump()),
    )


@app.exception_handler(Exception)
async def handle_exceptions(request: Request, exc: Exception):
    """Catch exceptions and return them in a consistent manner"""

    detail = None
    headers = None
    code = None

    if isinstance(exc, NotImplementedError):
        detail = "Not Implemented"
        code = status.HTTP_501_NOT_IMPLEMENTED
    else:
        detail = "Uncaught exception"
        code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        headers=headers,
        status_code=code,
        content=jsonable_encoder(
            SimpleResponseDTO(detail=detail, code=code).model_dump()
        ),
    )


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=app_settings.allow_origins,
    allow_methods=app_settings.allow_methods,
    allow_headers=app_settings.allow_headers,
    expose_headers=app_settings.expose_headers,
)


@app.get("/", include_in_schema=False)
async def index():
    assert app.docs_url is not None
    return RedirectResponse(app.docs_url)
