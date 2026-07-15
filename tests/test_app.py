import threading
import unittest

import app


class ProviderLoadingTest(unittest.TestCase):
    def test_provider_menus_load_concurrently(self):
        barrier = threading.Barrier(2)

        class Provider:
            def __init__(self, name):
                self.name = name

            def get_menu(self, day):
                barrier.wait(timeout=1)
                return self.name

        menus = app.get_provider_menus({"first": Provider("first"), "second": Provider("second")}, "Monday")

        self.assertEqual(menus, {"first": "first", "second": "second"})
