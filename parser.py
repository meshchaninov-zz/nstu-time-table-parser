from bs4 import BeautifulSoup, Tag
import requests
import re
import codecs

URL = "https://ciu.nstu.ru/student/time_table_view?idgroup=25554&fk_timetable=36218&nomenu=1&print=1"

def get_html(URL):
    return requests.get(URL).text

def parse_today_from_parse_head(soup):
    """
    Вспопмогательная функция
    Принимает на вход soup из bs4, возвращает полный вид даты
    """
    MONTHS = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря")
    t_a_w = soup.find("em").text.split()
    return (int(t_a_w[1]), MONTHS.index(t_a_w[2]) + 1, int(t_a_w[3][:-1])), int(t_a_w[6])


def parse_head(soup):
    """
    Принимает soup из bs4
    Возвращает (полный вид дня, номер недели, группа, семестр)
    """
    soup_head = soup.find("table").find("table")
    today = parse_today_from_parse_head(soup_head)
    group_and_sem = soup_head.find(lambda tag: len(tag.attrs) == 2).text.split()
    group = group_and_sem[1]
    sem = int(group_and_sem[2])
    return today[0], today[1], group, sem

def structed_output_from_parse_body(table):
    """
    Вспомогательная функция
    Принимает на вход кашу из parse body и приводит её в человеческий вид
    """
    WEEK = ("Вторник","Среда", "Четверг", "Пятница", "Суббота")
    EVEN_AND_NOT_EVEN = ("Ч", "Н")
    result = []
    day = []
    line = []
    num = -1
    for text in table:
        text = text.strip()
        if text in WEEK: #Если встретилось слово из недели, то достиг конец предедущего дня (исключение - Понедельник)
            result.append(day)
            day = []
            day.append(text)
            continue
        if line == [] and text in EVEN_AND_NOT_EVEN:   #Если встретилась Ч или Н, но без времени, то вот
            line.append(day[-1][0])
            num+=1
        line.append(text)
        num+=1
        if num >= 4: #Четыре подряд элемента образуют строку в исходной таблице
            day.append(line)
            line = []
            num = 0
    result.append(day)
    result[0].insert(0,result[0][0].pop(0)) #Перестановка слова "Понедельник" за пределы вложеного списка (Фуух, оптимизация епт)
    return result


def parse_body(soup):
    """
    Принимает soup из bs4
    Возвращает само расписание в виде [[день недели [время, Ч/Н, предмет, кабинет],[...],[...]]...]
    """
    soup_body = soup.findAll("td")[10:]
    table = [re.sub(r"^\s+|\n|\xa0|$\s+",'', i.text) for i in soup_body]
    print(table)
    return structed_output_from_parse_body(table)

def main():
    html = get_html(URL)
    soup = BeautifulSoup(html, "lxml")
    parse_head(soup)
    parse_body(soup)

if __name__ == '__main__':
    main()

