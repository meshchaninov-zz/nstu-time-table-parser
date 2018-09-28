from bs4 import BeautifulSoup
import requests

URL = "https://ciu.nstu.ru/student/time_table_view?idgroup=25554&fk_timetable=36218&nomenu=1&print=1"

def get_html(URL):
    return requests.get(URL).text

def parse_today_from_parse_head(soup):
    MONTHS = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря")
    t_a_w = soup.find("em").text.split()
    return ((int(t_a_w[1]), MONTHS.index(t_a_w[2]) + 1, int(t_a_w[3][:-1])), int(t_a_w[6]))

def parse_head(html):
    soup = BeautifulSoup(html, "lxml")
    soup_head = soup.find("table").find("table")
    today = parse_today_from_parse_head(soup_head)
    group_and_sem = soup_head.find(lambda tag: len(tag.attrs) == 2).text.split()
    group = group_and_sem[1]
    sem = int(group_and_sem[2])
    return today, group, sem 

def main():
    html = get_html(URL)
    print(parse_head(html))

if __name__ == '__main__':
    main()

