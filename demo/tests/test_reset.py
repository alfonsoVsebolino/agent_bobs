import unittest

from auth.reset import request_reset
from auth.user import get_user


class TestRequestReset(unittest.TestCase):
    def test_reset_known_user(self):
        token = request_reset("u1")
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

    def test_reset_unknown_user(self):
        token = request_reset("missing")
        self.assertIsNone(token)


if __name__ == "__main__":
    unittest.main()
