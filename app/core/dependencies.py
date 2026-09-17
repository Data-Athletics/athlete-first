from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession as AsyncAlchSession

from app.core.database import get_db_session

AsyncSessionDep = Annotated[AsyncAlchSession, Depends(get_db_session)]
"""
Gets and returns a connection to the database using SQLAlchemy.
"""
