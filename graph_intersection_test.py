import unittest
import mock
import requests
import graph_intersection

LOGIN = "dummnyemail@mail.com"
PASSWORD = "dummypassword"

ID = graph_intersection.IntersectionSearcher.ID
NAME = graph_intersection.IntersectionSearcher.NAME

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

    def test_get_friends_ids(self):
        self.fbrowser.get = mock.Mock(return_value=self.read_page("test_friends.html"))
        results_should_be = ["755770284", "513948430", "785901949"]
        results = self.fbrowser.get_friends_ids("dummy_url")
        self.assertIn(results_should_be[0], results)
        self.assertIn(results_should_be[1], results)
        self.assertIn(results_should_be[2], results)

class IntersectionSearcherTest(unittest.TestCase):
    def setUp(self):
        browser = mock.Mock()
        browser.get_friends_ids = mock.Mock(return_value=["755770284", "513948430"])
        self.searcher = graph_intersection.IntersectionSearcher(browser)

    def test_get_friends(self):
        requests.get = mock.Mock(return_value={ID:"74353",
                                                NAME:"John Doe"})
        result_should_be = {"123": [{ID:"755770284", NAME:"John Doe"}, {ID:"513948430", NAME:"John Doe"}]}
        self.assertEqual(result_should_be, self.searcher.friend_ids_names)

