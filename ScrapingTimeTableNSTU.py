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

    #TODO: num поменять 
    def __structed_output_from_get_body(self, table):
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
            if type(text) == type(list):
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
            if num >= 4: #Пять подряд элемента образуют строку в исходной таблице
                day.append(line)
                line = []
                num = 0
        result.append(day)
        result[0].insert(0,result[0][0].pop(0)) #Перестановка слова "Понедельник" за пределы вложеного списка (Фуух, оптимизация епт)
        return result

    def __get_full_url_person(self, url):
        """
        Так как в исходной таблице ссылки не полные, приходится их дополнять
        Принимает не полный url
        """
        return self.global_domain+url

    #BUG: разобраться с лишними пустыми строками
    def get_body(self):
        """
        Принимает soup из bs4
        Возвращает само расписание в виде [[день недели [время, Ч/Н, предмет,[(ФИО преподов и сайт),(...)] кабинет],[...],[...]]...]
        """
        try:
            soup_body = self.__soup.findAll("td")[10:]
        except AttributeError:
            print("Не удалось создать парсер")
            return None
        table = []
        regex_strip = r"^\s+|\n|\xa0|;|$\s" #regex выражение поиска всех пробельных знаков 
        num = 0
        for text in soup_body:
            # href = text.findAll("a") #Если есть ссылки, значит, это ссылки преподов
            # if href != []: #Тогда обрабатываем ссылки и втавляем их
            #     table.append(re.sub(regex_strip, '', text.contents[0]))
            #     table.append([(x.text, self.__get_full_url_person(x["href"])) for x in href])
            #     continue
            text = re.sub(regex_strip,'', text.text)  #Убираем лишние пробельные знаки
            text = text.strip()
            # if text == '': #Так как не во всех строчках есть ссылки преподов, для баланса(5 str на строчку) добаляем пустую
            #     table.append(text)
            #     num+=1
            #     if num >= 3:
            #         table.append('')
            #         num = 0
            #     continue
            # else:
            #     num = 0
            table.append(text)
        return self.__structed_output_from_get_body(table)

class JsonTimeTableNSTU(ScrapingTimeTableNSTU):
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
        return [{"name": x[0], "URL": x[1]} for x in lecturers[3]]

    #TODO: Сделать объяснение
    #TODO: lecturers допилить
    def __to_json_day(self, day):
        beg_end_time = self.__split_time(day[0])
        return {
                    "begin": beg_end_time[0],
                    "end": beg_end_time[1],
                    "week": day[1],
                    "lesson": day[2],
                    "lecturers": '',
                    "cabinet number": day[3]
                }
        
    #TODO: Сделать пояснение
    def __to_json_week(self, week):
        return {week[0]: [self.__to_json_day(day) for day in week[1:]]}

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
    with open("test.txt", "w") as f:
        f.write(JsonTimeTableNSTU(URL).fullJson())

if __name__ == '__main__':
    main()

