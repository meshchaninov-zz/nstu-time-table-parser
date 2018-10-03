from bs4 import BeautifulSoup
import json
import requests
import re

class ScrapingTimeTableNSTU:
    """
    Класс для парсинга таблиц расписаний с сайта NSTU, принимает на вход ссылку на таблицу для печати
    Результат выводит в виде структурированных списков

    Вид вывода:

    get_head:
    (
        "Полная дата (П: (8, 11, 2018))"
        "Номер недели (П: 7)"
        "Группа (П: "ИВ-53")
        "Семестр (П: 2)
    )
    
    get_body
    [
        [ "День недели",
            [
                "Периуд времени (П: "08:30 - 10:00")",
                "Четная/Нечетная недел (Ч/Н)",
                "Название предмета (П: "Базы данных и экспертные системы ")
                "Список преподов и ссылка на них (П: [('Хайленко Е. А.', 'ciu.nstu.ru/kaf/persons/26006'), ('Стасышина Т. Л.', 'ciu.nstu.ru/kaf/persons/1914')]))
                "Номер кабинета (П: "1-310")
            ],
            [...]
        ], [...]
    ]
    Если в раписании пусто в ячейке, выдает ''

    *П - пример
    """
    def __init__(self, url, parser="lxml"):
        self.url = url
        self.LESSONS_PER_DAY = 7
        try:
            self.__soup = BeautifulSoup(self.__get_html(self.url), parser)
        except TypeError:
            print("Не могу подключиться к интернету")
            self.__soup = None
        self.global_domain = "ciu.nstu.ru"
            

    def __get_html(self, URL):
        """
        Возвращает html страницу по ссылке
        """
        try:
            html = requests.get(URL).text
        except requests.exceptions.ConnectionError:
            html = None
        return html

    def __parse_today_from_get_head(self, soup):
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
            soup_head = self.__soup.find("table").find("table")
        except AttributeError:
            print("Не удалось создать парсер")
            return None
        today = self.__parse_today_from_get_head(soup_head)
        group_and_sem = soup_head.find(lambda tag: len(tag.attrs) == 2).text.split()
        group = group_and_sem[1]
        sem = int(group_and_sem[2])
        return today[0], today[1], group, sem

    def __get_full_url_person(self, url):
        """
        Так как в исходной таблице ссылки не полные, приходится их дополнять
        Принимает не полный url
        """
        return self.global_domain+url

    #TODO: добавить описание
    def __n_elements_to_one_list(self, line, n):
        return [line[n*k:n*(k+1)] for k in range(len(line) // n)]

    #TODO: описание
    def __del_excess_whitesapce(self, string):
        return re.sub(r"^\s+|\n|\xa0|$\s+", '', string)

    #TODO: описание
    def __soup_to_href_and_name(self, soup):
        hrefs = [(href.text, self.__get_full_url_person(href["href"])) for href in soup.findAll("a")]
        name = self.__del_excess_whitesapce(soup.text.split(";")[0])
        return [name, hrefs]
        
    #TODO: описание
    def __soup_line_to_structure(self, soup_line):
        soup_line[2] = self.__soup_to_href_and_name(soup_line[2])
        return list(map(lambda x: self.__del_excess_whitesapce(x.text) if type(x) != list else x, soup_line))

    #TODO: описание изменить
    def get_body(self):
        """
        Принимает soup из bs4
        Возвращает само расписание в виде [[день недели [время, Ч/Н, предмет,[(ФИО преподов и сайт),(...)] кабинет],[...],[...]]...]
        """
        try:
            soup_body = self.__soup.findAll("tr")[5:]
        except AttributeError:
            print("Не удалось создать парсер")
            return None
        all_lines = map(lambda x: x.findAll("td"), soup_body)
        all_lines = filter(lambda x: len(x) != 1, all_lines)
        all_lines = list(map(lambda x: self.__soup_line_to_structure(x), all_lines))
        all_lines = self.__n_elements_to_one_list(all_lines, self.LESSONS_PER_DAY)
        return all_lines

#TODO: полное описание
class JsonTimeTableNSTU(ScrapingTimeTableNSTU):
    #TODO: status не нужен
    def __init__(self, url, parser="lxml"):
        self.__status = None #Получилось ли получить раписание
        self.__WEEK = ("Ч", "Н", "Л") #константы для определения четной/нечетной/любой недели
        try:
            super().__init__(url, parser)
            self.status = "OK"
        except:
            self.status = "ERROR"
    
    def __split_time(self, time):
        """
        разделяет промежуток времени на две строки
        П: "8:30 - 10:00" -> "8:30", "10:00"
        """
        return time.split("-")
    
    def __date_to_ISO_format(self, date):
        """
        Переводит дату в соответситвии с ISO 8601 (YYYY-MM-DD)
        Принимает картеж (D, M, Y), переводит в строку "YYYY-MM-DD"
        П: (2,9,2018) -> "2018-09-02"
        """
        return "{2:04d}-{1:02d}-{0:02d}".format(date[0],date[1],date[2])

    #TODO: Сделать объяснение
    def __to_json_lecturers(self, lecturers):
        return [{"name": x[0], "URL": x[1]} for x in lecturers]

    #TODO: Сделать объяснение
    def __to_json_day(self, day):
        beg_end_time = self.__split_time(day[0])
        return {
                    "begin": beg_end_time[0],
                    "end": beg_end_time[1],
                    "week": day[1],
                    "lesson": day[2][0],
                    "lecturers": self.__to_json_lecturers(day[2][1]),
                    "cabinet number": day[3]
                }
        
    #TODO: Сделать пояснение
    def __to_json_week(self, week):
        return [self.__to_json_day(day) for day in week]

    #TODO: Сделать пояснение
    def __to_json_time_table(self, time_table):
        return [self.__to_json_week(x) for x in time_table]

    #TODO: Сделать пояснение
    #BUG: Не работает русский язык
    def fullJson(self):
        head = self.get_head()
        body = self.get_body()
        return json.dumps(
            {
                "date": self.__date_to_ISO_format(head[0]),
                "week number": head[1],
                "group": head[2],
                "semestr": head[3],
                "time table": self.__to_json_time_table(body)
            }
        )


def main():
    """
    Мини тесты
    """
    URL = "https://ciu.nstu.ru/student/time_table_view?idgroup=25554&fk_timetable=36218&nomenu=1&print=1"
    # sttn = ScrapingTimeTableNSTU(URL)
    # print(sttn.get_body())
    jttn = JsonTimeTableNSTU(URL)
    d = jttn.get_body()
    print(jttn.fullJson())
    # with open("test.txt", "w") as f:
    #     f.write(JsonTimeTableNSTU(URL).fullJson())

if __name__ == '__main__':
    main()

