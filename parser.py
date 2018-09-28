from bs4 import BeautifulSoup
import requests

URL = "https://ciu.nstu.ru/student/time_table_view?idgroup=25554&fk_timetable=36218&nomenu=1&print=1"

def get_html(URL):
    return requests.get(URL).text

def parse_head(html):
    soup = BeautifulSoup(html, "lxml")
    soup_head = soup.find("table").find("table")
    today = soup_head.find("em").text.split()
    group_and_sem = soup_head.find(lambda tag: len(tag.attrs) == 2).text.split()
    group = group_and_sem[1]
    sem = group_and_sem[2]
    print(group, sem)
    


def main():
    html = get_html(URL)
    parse_head(html)

if __name__ == '__main__':
    main()

