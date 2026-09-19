import sqlalchemy
import sqlalchemy.exc
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.biometrics.decoder import decode_noop_csv
from app.biometrics.services import bulk_upload_noop_data
from app.core.dependencies import AsyncSessionDep
from app.core.dtos import SimpleResponseDTO

biometrics_router = APIRouter()


@biometrics_router.post("/{user_id}", response_model=SimpleResponseDTO)
async def create_biometrics_route(
    db: AsyncSessionDep, user_id: int, file: UploadFile = File(...)
):
    """Create many biometrics rows from a csv upload"""

    if file.filename and not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a CSV file.",
        )

    noop_data = decode_noop_csv(file.file)

    try:
        await bulk_upload_noop_data(db, user_id, noop_data)
    except sqlalchemy.exc.NoReferencedTableError as e:
        if "user_id" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User id does not exist to upload data to.",
            )

    return SimpleResponseDTO(detail="Noop data uploaded", code=201)
