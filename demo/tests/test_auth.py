import unittest

from auth.user import get_user, login
from auth.profile import update_profile
from auth.utils import hash_password, validate_email


class TestGetUser(unittest.TestCase):
    def test_get_user_found(self):
        user = get_user("u1")
        self.assertIsNotNone(user)
        self.assertIn("email", user)

    def test_get_user_not_found(self):
        self.assertIsNone(get_user("missing"))


class TestLogin(unittest.TestCase):
    def test_login_success(self):
        user = login("alice@example.com", "password123")
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "alice@example.com")

    def test_login_failure_wrong_password(self):
        self.assertIsNone(login("alice@example.com", "wrongpassword"))

    def test_login_failure_unknown_email(self):
        self.assertIsNone(login("nobody@example.com", "password123"))


class TestUpdateProfile(unittest.TestCase):
    def test_update_profile(self):
        user = update_profile("u1", "Alice")
        self.assertIsNotNone(user)
        self.assertEqual(user["name"], "Alice")

    def test_update_profile_missing_user(self):
        self.assertIsNone(update_profile("unknown", "Ghost"))


class TestHashPassword(unittest.TestCase):
    def test_same_input_same_output(self):
        self.assertEqual(hash_password("secret"), hash_password("secret"))

    def test_different_inputs_differ(self):
        self.assertNotEqual(hash_password("aaa"), hash_password("bbb"))


class TestValidateEmail(unittest.TestCase):
    def test_valid_email(self):
        self.assertTrue(validate_email("user@example.com"))

    def test_invalid_email_no_at(self):
        self.assertFalse(validate_email("notanemail"))

    def test_invalid_email_no_domain(self):
        self.assertFalse(validate_email("user@"))


if __name__ == "__main__":
    unittest.main()
