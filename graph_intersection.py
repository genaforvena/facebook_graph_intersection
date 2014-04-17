import argparse
import csv
import cookielib
import mechanize #pip install mechanize
import requests # pip install requests
import sys
import urllib

from requests.packages.urllib3 import add_stderr_logger
from bs4 import BeautifulSoup


DEFAULT_OUTPUT = "intersection_output.csv"

ACCESS_TOKEN = "CAAIyz6lizZCwBADl1IWFlikGQrnwHyhoKPWhbUX3PwkZCbwhlQxAut9reXXpmTLTymOdPtF1kJpwxOF4MfIy3w8axZCgAk4KQW6RbBZBxadlqC6jLZAWXdcM8sMzv4VEFDKMrgYnbAXHzGPLfeEz8g6chZC8TeyfCmzVvIVvo8NRSj4YPOKeU2KfmooKl8aCPVcJ3mBGiJQAZDZD"
BASE_URL = 'https://graph.facebook.com'

def get_command_line_options():
    argparser = argparse.ArgumentParser(
        description='''
        find mutual friends between given persons on Facebook.

        example usage:
        python graph_intersection.py input_csv_file_path email@gmail.com password''')

    argparser.add_argument('input')
    argparser.add_argument('login')
    argparser.add_argument('password')

    args = argparser.parse_args()
    return args


class IntersectionSearcher(object):
    ID = "id"
    EMAIL = "email"

    def __init__(self, browser):
        self.browser = browser
        self._output_file = DEFAULT_OUTPUT
        self._base_emails_and_ids = []
        self._target_emails_and_ids = []
        self._not_found_emails = []

    def read_input_file(self, input_file_path):
        with open(input_file_path, 'rb') as csvfile:
            reader = csv.reader(csvfile.read().splitlines(), delimiter=',')
            for row in reader:
                base_email, target_email = row[0].strip(), row[1].strip()

                try:
                    base_person_id = self._get_person_id(base_email)
                    self._base_emails_and_ids.append({self.ID: base_person_id, self.EMAIL: base_email})
                except PersonIdNotFoundException:
                    print ["FACEBOOK IDs NOT FOUND FOR: " + base_email]
                    self._not_found_emails.append(base_email)

                try:
                    target_person_id = self._get_person_id(target_email)
                    self._target_emails_and_ids.append({self.ID: target_person_id, self.EMAIL: target_email})
                except PersonIdNotFoundException:
                    print ["FACEBOOK IDs NOT FOUND FOR: " + target_email]
                    self._not_found_emails.append(target_email)

    def find_intersections_and_print(self):
        with open(self._output_file, "w") as outfile:
            writer = csv.writer(outfile, delimiter='|')
            for base in self._base_emails_and_ids:
                for target in self._target_emails_and_ids:
                    intersections_list = self._get_intersections(base[self.ID], target[self.ID])
                    print base[self.EMAIL], " and ", target [self.EMAIL], " intercestions are: ", intersections_list
                    result_row_list = [("%s, %s") % (base[self.EMAIL], target[self.EMAIL])] + intersections_list
                    writer.writerow([x.encode("utf-8") for x in result_row_list])

    def _get_person_id(self, email):
        request = "https://www.facebook.com/search.php?q=" + urllib.quote_plus(email)
        response = self.browser.get(request)
        soup = BeautifulSoup(response)
        try:
            person_name_div = soup.find_all("div", attrs={'class': 'instant_search_title'})[0].find("a")
            onclick_text = person_name_div.attrs["onclick"]
            id = onclick_text.split('"id":')[-1].split(",")[0]
            return id
        except Exception:
            raise PersonIdNotFoundException()

    def _get_intersections(self, id1, id2):
        query = "/%s/mutualfriends/%s" % (id1, id2)
        response = requests.get(BASE_URL + query + "?access_token=" + ACCESS_TOKEN).json()
        intersections_list = _get_list(response["data"])
        return intersections_list


class FacebookAuthBrowser(object):
    def __init__(self, login, password):
        self._login = login
        self._password = password
        self._login_url = 'https://facebook.com/login'
        # self.session = None
        self._browser = None

    def login(self):
        self._browser = mechanize.Browser()
        cj = cookielib.LWPCookieJar()
        self._browser.set_cookiejar(cj)

        self._browser.set_handle_equiv(True)
        self._browser.set_handle_redirect(True)
        self._browser.set_handle_referer(True)
        self._browser.set_handle_robots(False)
        self._browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        self._browser.addheaders = [('User-agent', 'Chrome')]

        self._browser.open(self._login_url)
        self._browser.select_form(nr=0)

        self._browser.form['email'] = self._login
        self._browser.form['pass'] = self._password

        self._browser.submit()



        # self.session = requests.Session()
        # self.session.headers['User-Agent'] = 'Chrome'
        #
        # login = {'login': self.login, 'password': self.password}
        # login_response = self.session.post(self.url, data=login)
        # for r in login_response.history:
        #     if r.status_code == 401:  # 401 means authentication failed
        #         print 'error!'
        #         sys.exit(1)  # abort

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


if __name__ == "__main__":
    args = get_command_line_options()
    browser = FacebookAuthBrowser(args.login, args.password)
    browser.login()
    searcher = IntersectionSearcher(browser)
    searcher.read_input_file(args.input)
    searcher.find_intersections_and_print()

