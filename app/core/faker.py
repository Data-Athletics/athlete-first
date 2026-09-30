import random
from typing import get_args

from faker import Faker

from app.user.models import UserSex


class CustomFaker(Faker):
    """Wrap Faker class to add custom methods."""

    def username(self):
        """Alias for `user_name()`, generate a fake username"""

        return self.user_name()

    def height(self):
        """Returns random height in inches"""

        return random.uniform(6, 96)

    def weight(self):
        """Returns random weight in pounds"""

        return random.uniform(5, 1000)

    def sex(self) -> UserSex:
        """Returns random user sex"""

        literalStrs = get_args(UserSex)
        return random.choice(literalStrs)

    def age(self):
        """Returns random user age in years"""

        return random.randint(1, 115)


fake = CustomFaker("en_US")

__all__ = ["fake"]
