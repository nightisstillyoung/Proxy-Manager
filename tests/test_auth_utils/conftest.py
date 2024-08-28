import pytest
import random
import string

uppercase_chars = string.ascii_uppercase
lowercase_chars = string.ascii_lowercase
digits = string.digits
special_chars = string.punctuation


def random_password(min_length: int = 8, max_length: int = 64) -> str:
    """Generates random password"""
    length = random.randint(min_length, max_length)

    characters = uppercase_chars + lowercase_chars + digits + special_chars

    return ''.join(random.choices(characters, k=length))


@pytest.fixture
def passwords() -> list[str]:
    return [random_password() for _ in range(0, 5)]
