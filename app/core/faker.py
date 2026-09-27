from faker import Faker


class CustomFaker(Faker):
    """Wrap Faker class to add custom methods."""

    def username(self):
        """Alias for `user_name()`, generate a fake username"""

        return self.user_name()


fake = CustomFaker("en_US")

__all__ = ["fake"]
