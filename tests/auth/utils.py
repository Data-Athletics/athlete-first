from app.auth.dtos.token_dto import TokenClaimsDTO
from app.user.models import User


def create_test_user_token(user: User) -> str:
    """Create test access token for a given user"""

    claims = TokenClaimsDTO(sub=str(user.id))
    return claims.encode()
