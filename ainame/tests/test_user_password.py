import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from models.user import User


class UserPasswordTest(unittest.TestCase):
    def test_valid_hash_verifies_password(self):
        user = User(email="a@example.com", username="tester", password="secret123")

        self.assertTrue(user.check_password("secret123"))
        self.assertFalse(user.check_password("wrong123"))

    def test_invalid_hash_returns_false_instead_of_raising(self):
        user = User(email="a@example.com", username="tester")
        user._password = "not-a-supported-password-hash"

        self.assertFalse(user.check_password("secret123"))

    def test_legacy_plaintext_password_is_rehashed_after_success(self):
        user = User(email="a@example.com", username="tester")
        user._password = "secret123"

        self.assertTrue(user.check_password("secret123"))
        self.assertNotEqual(user._password, "secret123")
        self.assertTrue(user.check_password("secret123"))


if __name__ == "__main__":
    unittest.main()
