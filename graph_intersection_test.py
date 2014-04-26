import unittest
import mock
import graph_intersection

LOGIN = "ilyailiila@gmail.com"
PASSWORD = "moil13118"

class FacebookAuthBrowserTest(unittest.TestCase):
    def setUp(self):
        self.fbrowser = graph_intersection.FacebookAuthBrowser(LOGIN, PASSWORD)

    def read_page(self, path):
        with open("unittest/" + path) as f:
            return f.read()

    def test_get_person_id(self):
        self.fbrowser.get = mock.Mock(return_value=self.read_page("test_person_id.html"))
        result_id = self.fbrowser.get_person_id("dummymail@mail.com")
        self.assertEqual("553433615", result_id)

    def test_get_friends(self):
        self.fbrowser.get = mock.Mock(return_value=self.read_page("test_friends.html"))
        results_should_be = ["755770284", "513948430", "785901949"]
        results = self.fbrowser.get_friends("dummy_url")
        self.assertIn(results_should_be[0], results)
        self.assertIn(results_should_be[1], results)
        self.assertIn(results_should_be[2], results)
