import argparse
import csv
import cookielib
import mechanize  # pip install mechanize
import requests  # pip install requests
import sys
import urllib

from bs4 import BeautifulSoup


DEFAULT_OUTPUT = "intersection_output.csv"

ACCESS_TOKEN = "CAAIyz6lizZCwBAEH34od2d4IZCHhDnddxiyE8V3Bp3fH4uYtBdpPHUni1NT7SDZAgU7jGil60c2TUPp361ZCqLq733DZAsnT9oXcaDp0XSplee12EYpM97N5I58fsoKhDrABLsht1fLqMwHlMoHcLnoqWRGfTRQosierF1NZC57Fif6DDPmaMQIZA19tHn2eqHZCpxGxXIPMJQZDZD"
BASE_URL = 'https://graph.facebook.com'

def get_command_line_options():
    argparser = argparse.ArgumentParser(
        description='''
        find mutual friends between given persons on Facebook.

        example usage:
        python graph_intersection.py input_csv_file_path''')

    argparser.add_argument('input')
    argparser.add_argument('login')
    argparser.add_argument('password')

    args = argparser.parse_args()
    return args


class IntersectionSearcher(object):
    ID = "id"
    EMAIL = "email"
    NAME = "name"

    def __init__(self, browser):
        self.browser = browser
        self._output_file = DEFAULT_OUTPUT
        self._base_emails_and_ids = []
        self._target_emails_and_ids = []
        self._not_found_emails = []
        self._friends_ids_names = {}

    def read_input_file_and_get_user_ids(self, input_file_path):
        with open(input_file_path, 'rb') as csvfile:
            reader = csv.reader(csvfile.read().splitlines(), delimiter=',')
            for row in reader:
                base_email, target_email = row[0].strip(), row[1].strip()
                self._get_person_id(base_email, self._base_emails_and_ids)
                self._get_person_id(target_email, self._target_emails_and_ids)

    def find_intersections_and_print(self):
        with open(self._output_file, "w") as outfile:
            writer = csv.writer(outfile, delimiter='|')
            for base in self._base_emails_and_ids:
                for target in self._target_emails_and_ids:
                    intersections_list = self._are_friends(base[self.ID], target[self.ID])
                    self.get_friends(target[self.ID])
                    print base[self.EMAIL], " and ", target[self.EMAIL], " intercestions are: ", intersections_list
                    result_row_list = [("%s, %s") % (base[self.EMAIL], target[self.EMAIL])] + intersections_list
                    writer.writerow([x.encode("utf-8") for x in result_row_list])

    def get_friends(self, id):
        user_page_url = self._get_user_info(id)["link"]
        friends_ids = self.browser.get_friends_ids(user_page_url)
        friend_ids_names = []
        for friend_id in friends_ids:
            friend_ids_names.append({self.NAME: self._get_user_info(friend_id)[self.NAME], self.ID: friend_id})
        self.friend_ids_names[id] = friend_ids_names

    @property
    def friend_ids_names(self):
        return self._friends_ids_names

    def _get_user_info(self, id):
        return requests.get(BASE_URL + "/" + id + "?access_token=" + ACCESS_TOKEN).json()

    def _get_person_id(self, email, list_to_append):
        try:
            person_id = browser.get_person_id(email)
            list_to_append.append({self.ID: person_id, self.EMAIL: email})
        except PersonIdNotFoundException:
            print ["FACEBOOK IDs NOT FOUND FOR: " + email]
            self._not_found_emails.append(email)
        return person_id

    def _are_friends(self, id1, id2):
        response = self._make_request("friends", id1, id2)
        if response:
            return [str(True)]
        else:
            return [str(False)]

    def _make_request(self, request, id1, id2):
        query = "/%s/" % id1 + request + "/%s" % id2
        response = requests.get(BASE_URL + query + "?access_token=" + ACCESS_TOKEN).json()
        try:
            return _get_list(response["data"])
        except:
            print "CHECK YOU ACCESS TOKEN"
            sys.exit(1)


class SimpleBrowser(object):
    def get(self, request):
        return requests.get(request).text

    def get_person_id(self, email):
        request = "https://www.facebook.com/search.php?q=" + urllib.quote_plus(email)
        response = self.browser.get(request)
        soup = BeautifulSoup(response)
        try:
            person_name_div = soup.find_all("div", attrs={'class': 'instant_search_title'})[0].find("a")
            onclick_text = person_name_div.attrs["onclick"]
            uid = onclick_text.split('"id":')[-1].split(",")[0]
        except Exception:
            raise PersonIdNotFoundException()
        return uid

    def get_friends(self, user_page_url):
        raise Exception

class FacebookAuthBrowser(object):
    def __init__(self, login, password):
        self._login = login
        self._password = password
        self._login_url = 'https://facebook.com/login'
        self._browser = mechanize.Browser()

        self._browser.set_handle_equiv(True)
        self._browser.set_handle_redirect(True)
        self._browser.set_handle_referer(True)
        self._browser.set_handle_robots(False)
        self._browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        self._browser.addheaders = [('User-agent', 'Chrome')]

        cj = cookielib.LWPCookieJar()
        self._browser.set_cookiejar(cj)

    def login(self):
        self._browser.open(self._login_url)
        self._browser.select_form(nr=0)

        self._browser.form['email'] = self._login
        self._browser.form['pass'] = self._password
        self._browser.submit()

    def get_person_id(self, email):
        request = "https://www.facebook.com/search.php?q=" + urllib.quote_plus(email)
        response = self.get(request)
        split_start = "/ajax/hovercard/user.php?id="
        split_end = '">'
        return response.split(split_start)[1].split(split_end)[0]

    def get_friends_ids(self, user_page_url):
        request = user_page_url + "/friends"
        response = self.get(request)
        split_start = "/ajax/hovercard/user.php?id="
        split_end = '&'

        found_ids = []
        for x in response.split(split_start):
            try:
                found_ids.append(x.split(split_end)[0])
            except:
                continue
        return found_ids[1:]

    def get(self, request):
        return self._browser.open(request).read()


class PersonIdNotFoundException(Exception):
    pass


def _get_list(json_data):
    return_list = []
    for x in json_data:
        return_list.append(x["name"])
        return_list.append(x["id"])
    return return_list


def cut_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""

if __name__ == "__main__":
    args = get_command_line_options()
    browser = FacebookAuthBrowser(args.login, args.password)
    browser.login()
    # browser = SimpleBrowser()
    searcher = IntersectionSearcher(browser)
    searcher.read_input_file_and_get_user_ids(args.input)
    searcher.find_intersections_and_print()

