import unittest

from brain.context import ContextManager


class TestContextManager(unittest.TestCase):
    def test_rewrite_uses_last_person_for_pronouns(self) -> None:
        context = ContextManager()
        context.update("Who is Elon Musk?", "Elon Musk is a business magnate.")

        self.assertEqual(context.rewrite("How old is he?"), "How old is Elon Musk?")


if __name__ == "__main__":
    unittest.main()
