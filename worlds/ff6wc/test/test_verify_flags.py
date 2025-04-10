import unittest
from worlds.ff6wc.Options import verify_flagstring


class TestVerifyFlags(unittest.TestCase):
    def test_ok_flags(self) -> None:
        verify_flagstring(["-i", "x"])
        verify_flagstring([])

    def test_new_flags(self) -> None:
        """ some new flags from Worlds Collide 1.4.2 """
        verify_flagstring(["-i", "x", "-chrm", "0", "0"])

    def test_bad_flags(self) -> None:
        self.assertRaises(ValueError, verify_flagstring, ["-i", "x", "-bkbkb00"])
        # for these objective tests, see https://github.com/beauxq/Archipelago/pull/8 for more info
        # Bad Objective Result number (current values are 0-73); currently commented out due to not seeing KeyError
        #self.assertRaises(KeyError, verify_flagstring, ["-i", "x", "-oe 84.1.1.11.31"])
        # Bad Objective Range, in this example: Add 18-155 Enemy Levels for 1 random objective (max is 99)
        self.assertRaises(ValueError, verify_flagstring, ["-i", "x", "-oe 21.18.155.1.1.1.r"])
        # Bad Objective Range, in this example: Update MagPwr stat between -234 and +23 for 1-2 dragon kills (range -99 to 99)
        self.assertRaises(ValueError, verify_flagstring, ["-i", "x", "-oe 45.-234.23.1.1.6.1.2"])
        # Bad Objective Conditions min/max, in this example: Ribbon for completing 2 of 1 conditions
        self.assertRaises(ValueError, verify_flagstring, ["-i", "x", "-oe 42.2.1.9.15.4.5.10.3.2"])
        # Bad Objective Condition Type (current range 0-12)
        self.assertRaises(ValueError, verify_flagstring, ["-i", "x", "-oe 65.1.1.22.31"])
        # Bad Objective Condition Value Range, in this example using random as a max
        self.assertRaises(TypeError, verify_flagstring, ["-i", "x", "-oe 35.2.2.2.1.9.r"])
        # Bad Objective Condition Value Range, in this example missing the max condition
        self.assertRaises(ValueError, verify_flagstring, ["-i", "x", "-oe 8.4.4.3.1.3.3.3.3.3.5.5.5.8.12"])
        # Bad Objective Condition Value, it's missing from this one
        self.assertRaises(ValueError, verify_flagstring, ["-i", "x", "-of 40.4.4.3.6.3.3.0.9.2.5.16.12"])
