from faker import Faker


class CustomFaker(Faker):
    """Wrap Faker class to add custom methods."""

    pass


fake = CustomFaker("en_US")

__all__ = ["fake"]
