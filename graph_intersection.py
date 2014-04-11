import argparse
import csv
import requests # pip install requests
import urllib

from bs4 import BeautifulSoup


DEFAULT_OUTPUT = "intersection_output.csv"

ACCESS_TOKEN = "CAAIyz6lizZCwBAOr9jK0720ZB55kO2FUQ53xKIQd8e1IOOOIZA1WzbGuuP93AWET1TTvJ837cjJA3LrLFoRHal9AZB3lMuXqaBC1JMNbca0EuOxauJMH8ozKVMGxiitilCt8jfCdaI2SvaHjZCLBaZBIvARfCKqi3ZCcksbVXsWsfmyisA5naoCmDNZAV2ZB88ECHuvZCBNJcimQZDZD"
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


def get_person_id(email):
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


def get_intersections(id1, id2):
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
    with open(args.input, 'rb') as csvfile, open(DEFAULT_OUTPUT, "w") as outfile:
        reader = csv.reader(csvfile, delimiter=',')
        writer = csv.writer(outfile, delimiter='|')
        for row in reader:
            base_email, tagret_email = row[0].strip(), row[1].strip()
            try:
                base_person_id, tagret_person_id = get_person_id(base_email), get_person_id(tagret_email)
                intersections_list = get_intersections(base_person_id, tagret_person_id)
                result_row_list = [("%s, %s") % (base_email, tagret_email)] + intersections_list
                writer.writerow([x.encode("utf-8") for x in result_row_list])
            except PersonIdNotFoundException:
                writer.writerow(["FACEBOOK IDs NOT FOUND FOR: " + base_email + " " + tagret_email])

