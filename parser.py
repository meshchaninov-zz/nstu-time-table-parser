from bs4 import BeautifulSoup, Tag
import requests
import re
import codecs

URL = "https://ciu.nstu.ru/student/time_table_view?idgroup=25554&fk_timetable=36218&nomenu=1&print=1"

def get_html(URL):
    return requests.get(URL).text

def parse_today_from_parse_head(soup):
    """This func return today date and week from head soup"""
    MONTHS = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря")
    t_a_w = soup.find("em").text.split()
    return (int(t_a_w[1]), MONTHS.index(t_a_w[2]) + 1, int(t_a_w[3][:-1])), int(t_a_w[6])


def parse_head(html):
    """This func return (today date, week, group, semestr)"""
    soup = BeautifulSoup(html, "lxml")
    soup_head = soup.find("table").find("table")
    today = parse_today_from_parse_head(soup_head)
    group_and_sem = soup_head.find(lambda tag: len(tag.attrs) == 2).text.split()
    group = group_and_sem[1]
    sem = int(group_and_sem[2])
    return today[0], today[1], group, sem

#TODO: next level!
def parse_body(html):
    soup = BeautifulSoup(html, "lxml")
    soup_body = soup.findAll("td")[10:]
    table = [re.sub(r"^\s+|\n|\xa0|$\s+",'', i.text) for i in soup_body]
    WEEK = ("Понедельник", "Вторник","Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")
    EVEN_AND_NOT_EVEN = ("Ч", "Н")
    result = []
    day = []
    line = []
    num = 0
    for text in table:
        text = text.strip()
        if text in WEEK:
            result.append(day)
            day = []
            day.append(text)
            continue
        if line == [] and text in EVEN_AND_NOT_EVEN:
            line.append(day[-1][0])
            num+=1
        line.append(text)
        num+=1
        if num >= 4:
            day.append(line)
            line = []
            num = 0
    result.append(day)
    result.pop(0)
    return result

def main():
    html = get_html(URL)
    print(parse_body(html))

if __name__ == '__main__':
    main()

