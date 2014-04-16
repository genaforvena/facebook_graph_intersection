import argparse
import csv
import requests # pip install requests
import urllib

from bs4 import BeautifulSoup


DEFAULT_OUTPUT = "intersection_output.csv"

ACCESS_TOKEN = "CAAIyz6lizZCwBABSKmAFefxEkdRLpjCalG6NHW82vi34Hi3GHe6T2gJkh9tHkgXciCpD88ZBdrGRbXhswHYsrSZBGPZAWFxEwsfOueybXtvKaW4so2ZAdCXOKK17mWphLsy7zJJVZAK7bDsyU28hvhQVDov1mZBabmozjEcI0ANq9Cmm0ftVr5lINPi2aDa4VyUZC6kRJRKk6wZDZD"
BASE_URL = 'https://graph.facebook.com'

def get_command_line_options():
    argparser = argparse.ArgumentParser(
        description='''
        find mutual friends between given persons on Facebook.

        example usage:
        python graph_intersection.py input_csv_file_path''')

    argparser.add_argument('input')

    args = argparser.parse_args()
    return args


class IntersectionSearcher(object):
    ID = "id"
    EMAIL = "email"

    def __init__(self):
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
                    base_person_id, target_person_id = self._get_person_id(base_email), self._get_person_id(target_email)
                    self._base_emails_and_ids.append({self.ID: base_person_id, self.EMAIL: base_email})
                    self._target_emails_and_ids.append({self.ID: target_person_id, self.EMAIL: target_email})
                except PersonIdNotFoundException:
                    print ["FACEBOOK IDs NOT FOUND FOR: " + base_email + " " + target_email]
                    self._not_found_emails(row)

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
        response = requests.get("https://www.facebook.com/search.php?o=2048&init=dir&q=" + urllib.quote_plus(email))
        data = response.text
        soup = BeautifulSoup(data)
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


def _get_list(json_data):
    return_list = []
    for x in json_data:
        return_list.append(x["name"])
        return_list.append(x["id"])
    return return_list


class PersonIdNotFoundException(Exception):
    pass


if __name__ == "__main__":
    args = get_command_line_options()
    searcher = IntersectionSearcher()
    searcher.read_input_file(args.input)
    searcher.find_intersections_and_print()

