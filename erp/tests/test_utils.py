from django.test import TestCase

from erp import utils


class UtilsTest(TestCase):
    def test_strip_nonascii(self):
        test_str = "Je vais à la maison."
        self.assertEqual(
            utils.strip_nonascii(test_str),
            "Je vais a la maison."
        )

        french_name = "Jean-François Étienne"
        self.assertEqual(
            utils.strip_nonascii(french_name),
            "Jean-Francois Etienne"
        )

        test_str = "J'aime les œufs."
        self.assertEqual(
            utils.strip_nonascii(test_str),
            "J'aime les oeufs."
        )
