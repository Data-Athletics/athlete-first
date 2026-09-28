from app.user.models import User


def create_biometrics_url(user: User) -> str:
    return f"/biometrics/{user.id}"
