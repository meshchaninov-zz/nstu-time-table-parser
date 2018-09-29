from bs4 import BeautifulSoup
import requests
import re

class ScrapingTimeTableNSTU:
    """
    Класс для парсинга таблиц расписаний с сайта NSTU, принимает на вход ссылку
    Результат выводит в виде структурированных списков
    """
    def __init__(self, url, parser="lxml"):
        self.url = url
        try:
            self.soup = BeautifulSoup(self._get_html(self.url), parser)
        except TypeError:
            print("Не могу подключиться к интернету")
            self.soup = None
            

    def _get_html(self, URL):
        """
        Возвращает html страницу по ссылке
        """
        try:
            html = requests.get(URL).text
        except requests.exceptions.ConnectionError:
            html = None
        return html

    def _parse_today_from_get_head(self, soup):
        """
        Вспопмогательная функция для get_head
        Принимает на вход soup из bs4, возвращает полный вид даты
        """
        MONTHS = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря")
        t_a_w = soup.find("em").text.split()
        return (int(t_a_w[1]), MONTHS.index(t_a_w[2]) + 1, int(t_a_w[3][:-1])), int(t_a_w[6])


    def get_head(self):
        """
        Принимает soup из bs4
        Возвращает (полный вид дня, номер недели, группа, семестр)
        """
        try:
            soup_head = self.soup.find("table").find("table")
        except AttributeError:
            print("Не удалось создать парсер")
            return None
        today = self._parse_today_from_get_head(soup_head)
        group_and_sem = soup_head.find(lambda tag: len(tag.attrs) == 2).text.split()
        group = group_and_sem[1]
        sem = int(group_and_sem[2])
        return today[0], today[1], group, sem

    def _structed_output_from_get_body(self, table):
        """
        Вспомогательная функция
        Принимает на вход кашу из get_body и приводит её в человеческий вид
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

    def get_body(self):
        """
        Принимает soup из bs4
        Возвращает само расписание в виде [[день недели [время, Ч/Н, предмет, кабинет],[...],[...]]...]
        """
        try:
            soup_body = self.soup.findAll("td")[10:]
        except AttributeError:
            print("Не удалось создать парсер")
            return None
        table = [re.sub(r"^\s+|\n|\xa0|$\s+",'', i.text) for i in soup_body]
        return self._structed_output_from_get_body(table)

def main():
    """
    Мини тесты
    """
    URL = "https://ciu.nstu.ru/student/time_table_view?idgroup=25554&fk_timetable=36218&nomenu=1&print=1"
    sttn = ScrapingTimeTableNSTU(URL)
    print(sttn.get_body())
    print(sttn.get_head())

if __name__ == '__main__':
    main()

