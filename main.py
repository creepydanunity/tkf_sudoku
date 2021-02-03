import locale
import sys
import webbrowser
from datetime import datetime, date
from sql import SQL
from calendar import mdays
from PyQt5 import QtWidgets, QtCore
from threading import Timer
from docxtpl import DocxTemplate
from apprentice_ui import Student_UI
from login_ui import Ui_Login
from class_selection_ui import Class_select_ui
from teacher_ui import Teacher_UI
from comments_student_ui import comments_stUI
from add_comment_ui import Add_comment_ui
from comments_teacher_ui import Teacher_comm
from plans_ui import Plans
from calendar_plan_ui import Calendar_plan


class Wrong_Mark(Exception):
    pass


def minimum_info():
    webbrowser.open('https://www.school56.org/school/obrazovatelny-minimum-2020')


class Application:
    def __init__(self):
        # Подключение SQL сервера, инициализация UI.
        self.SQL_server, self.app = SQL('Diary'), QtWidgets.QApplication(sys.argv)
        self.cursor, self.entered, self.main_window, self.ui, self.is_student, self.id, self.month_id = \
            self.SQL_server.conn.cursor(), False, QtWidgets.QMainWindow(), \
            Ui_Login(), True, 0, datetime.now().month
        self.ui.setupUi(self.main_window)
        self.main_window.show()
        self.ui.button_enter.clicked.connect(self.login_button_pressed)
        locale.setlocale(locale.LC_ALL, ('RU', 'UTF8'))
        self.main()

    def login_button_pressed(self):
        login_to_test, password_to_test = self.ui.input_ID.text(), self.ui.input_password.text()
        if password_to_test == self.cursor.execute(f'SELECT password FROM users WHERE id = '
                                                   f'{login_to_test}').fetchone()[0] and password_to_test != '':
            self.entered, self.id = True, login_to_test
            if self.cursor.execute(f'SELECT is_student FROM users WHERE id = '
                                   f'{login_to_test}').fetchone()[0] is False:
                self.is_student = False
                self.reconstruct_ui(Class_select_ui())
                self.class_choose()
            else:
                self.reconstruct_ui(Student_UI())
                self.load_student()

    def submit_plan(self, date_data: date):
        message = self.ui.lineEdit.text()
        self.cursor.execute(f'INSERT plans (id, teacher_id, date, class, planned) VALUES (0, {self.id}, '
                            f'CAST(\'{date_data}\' as date), \'{self.school_class}\', \'{message}\')')
        self.SQL_server.conn.commit()
        self.load_teacher(again=True)

    def add_plan(self):
        self.reconstruct_ui(Calendar_plan())
        self.ui.button_enter.clicked.connect(lambda: self.submit_plan(self.ui.calendarWidget.selectedDate().toPyDate()))

    def plans(self):
        self.reconstruct_ui(Plans())
        self.ui.exit_button.clicked.connect(lambda: self.return_to_teacher())
        answer = self.cursor.execute(f'SELECT date, planned FROM plans WHERE (teacher_id = {self.id} '
                                     f'AND CAST(class as varchar) = \'{self.school_class}\')').fetchall()
        self.ui.tableWidget.setColumnCount(1)
        self.ui.tableWidget.setRowCount(len(answer))
        self.ui.add_new_comm.clicked.connect(lambda: self.add_plan())
        self.ui.tableWidget.setHorizontalHeaderLabels(['План'])
        if answer is not None:
            answer = sorted(answer, key=lambda x: x[0])
            self.ui.tableWidget.setVerticalHeaderLabels([str(i[0]) for i in answer])
            self.ui.tableWidget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            for i in range(len(answer)):
                example = QtWidgets.QTableWidgetItem(str(answer[i][1]))
                example.setFlags(QtCore.Qt.ItemIsEnabled)
                self.ui.tableWidget.setItem(i, 0, example)
            self.ui.tableWidget.resizeRowsToContents()

    def return_to_teacher(self, save=False):
        if save is False:
            self.load_teacher(again=True)
        else:
            temp_id = save[0]
            for i in save:
                if i[0] == self.ui.students_combobox.currentText():
                    temp_id = i[1]
                    break
            temp_date = datetime.now()
            temp_char = '\''
            print(str(temp_date)[:19])
            self.cursor.execute(f'INSERT messages (id, id_from, id_to, message, date, readed) VALUES (0, {self.id}, '
                                f'{temp_id}, {temp_char}{self.ui.input_comment.text()}{temp_char}, '
                                f'CAST({temp_char}{str(temp_date)[:19]}{temp_char} as datetime), 0)')
            self.SQL_server.conn.commit()
            self.ui.input_comment.setText('Отправлено!')

    def add_comment_swap(self, students):
        self.reconstruct_ui(Add_comment_ui())
        for i in students:
            self.ui.students_combobox.addItem(i[0])
        self.ui.button_cancel.clicked.connect(lambda: self.return_to_teacher())
        self.ui.button_ok.clicked.connect(lambda: self.return_to_teacher(save=students))

    def class_choose(self):
        answer = self.cursor.execute(f'SELECT lastname, name, surname FROM teachers WHERE id = {self.id}').fetchone()
        self.ui.username.setText(f'{answer[0]} {answer[1]} {answer[2]}')
        answer = self.cursor.execute(f'SELECT classes FROM teachers WHERE id = {self.id}').fetchone()
        classes = answer[0].split(' ')
        for i in classes:
            self.ui.classes__box.addItem(i)
        self.ui.button_enter.clicked.connect(lambda: self.load_teacher())

    def change_class(self):
        self.reconstruct_ui(Class_select_ui())
        self.class_choose()

    def load_teacher(self, again=False):
        if again is False:
            self.school_class = self.ui.classes__box.currentText()
        else:
            self.school_class = self.school_class
        self.reconstruct_ui(Teacher_UI())
        answer = self.cursor.execute(f'SELECT lastname, name, surname FROM teachers WHERE id = {self.id}').fetchone()
        self.ui.username.setText(f'{answer[0]} {answer[1]} {answer[2]}')
        temp_char = "\'"
        answer = self.cursor.execute(f'SELECT name FROM '
                                     f'class_teacher WHERE CAST(class as varchar) = '
                                     f'{temp_char}{self.school_class}{temp_char}').fetchone()
        self.ui.class_ruk_name.setText(answer[0])
        self.ui.ID.setText(f'ID: {self.id}  |  Класс: {self.school_class}')
        self.get_time_teacher()
        self.get_timetable_teacher()
        self.ui.right_pushbutton.clicked.connect(lambda: self.month_swap_t(r=True))
        self.ui.left_pushbutton.clicked.connect(lambda: self.month_swap_t(r=False))
        self.ui.exit.clicked.connect(lambda: self.exit())
        self.ui.class_selection.clicked.connect(lambda: self.change_class())
        self.ui.timetable_link.clicked.connect(lambda: self.link_to_timetable())
        self.ui.minimum_link.clicked.connect(lambda: self.minimum_info_t())
        self.ui.change_mark.clicked.connect(lambda: self.save_marks())
        self.ui.add_comm.clicked.connect(lambda: self.show_messages_teacher())
        self.ui.plans.clicked.connect(lambda: self.plans())
        self.ui.seating.clicked.connect(lambda: self.add_comment_swap(
            [[self.ui.marks.takeVerticalHeaderItem(i).text(), self.ui.marks.item(i, 0).text()]
             for i in range(self.ui.marks.rowCount())]))
        self.reconstruct_teacher_table(datetime.now().month)

    def minimum_info_t(self):
        shared_link = "https://www.school56.org/school/obrazovatelny-minimum-2020/"
        links_to_subjects = {'ИКТ': 'informatika',
                             'История': 'istoriya',
                             'Литература': 'literatura',
                             'Алгебра': 'matematika',
                             'Обществознание': 'obshchestvoznanie',
                             'Русский Язык': 'russkij-yazyk',
                             'Химия': 'khim-bio',
                             'Экономика': 'ekonomika',
                             'Физика': 'fizika'}
        subject = self.ui.month_name.text().split(', ')[1]
        if subject in links_to_subjects:
            webbrowser.open(shared_link + links_to_subjects[subject])
        else:
            webbrowser.open(shared_link)

    def month_swap_t(self, r=False):
        if r:
            self.month_id += 1
            if self.month_id > 12:
                self.month_id = self.month_id - 12
            self.reconstruct_teacher_table(self.month_id)
        else:
            self.month_id -= 1
            if self.month_id < 1:
                self.month_id = self.month_id + 12
            self.reconstruct_teacher_table(self.month_id)

    def reconstruct_teacher_table(self, month: int):
        cols, subjects = mdays[month], ['Русский Язык', 'Литература', 'Алгебра', 'Геометрия',
                                        'Английский Язык', 'ИКТ',
                                        'История', 'Обществознание', 'Физика', 'Химия',
                                        'Биология',
                                        'ОБЖ', 'Физкультура',
                                        'Музыка', 'География',
                                        'Экономика',
                                        'Право']
        temp_char = "\'"
        answer = self.cursor.execute(f'SELECT id FROM students WHERE CAST(class as varchar) = '
                                     f'{temp_char}{self.school_class}{temp_char}').fetchall()
        self.ui.marks.setColumnCount(0)
        self.month_id = month
        self.ui.marks.setRowCount(0)
        self.ui.marks.setColumnCount(cols + 2)
        self.ui.marks.setRowCount(len(answer))
        self.ui.marks.setHorizontalHeaderLabels(['ID'] + [str(i) for i in range(1, cols + 1)] + ['Ср. знач'])
        students = []
        for i in answer:
            answer_2 = self.cursor.execute(f'SELECT name, lastname FROM students WHERE id = {i[0]}').fetchone()
            students.append(answer_2[1] + ' ' + answer_2[0])
        self.ui.marks.setVerticalHeaderLabels([students[i] for i in range(len(students))])
        for i in range(len(students)):
            example = QtWidgets.QTableWidgetItem(str(answer[i][0]))
            example.setFlags(QtCore.Qt.ItemIsEnabled)
            self.ui.marks.setItem(i, 0, example)
            if len(students) < 20:
                self.ui.marks.verticalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        self.ui.marks.resizeColumnsToContents()
        subject_id = subjects.index(self.cursor.execute(f'SELECT object '
                                                        f'FROM teachers WHERE id = {self.id}').fetchone()[0]) + 1
        self.ui.month_name.setText(date(datetime.now().year, self.month_id, 1).strftime("%B")
                                   + ', ' + subjects[subject_id - 1])
        for i in range(len(answer)):
            answer_2 = self.cursor.execute(f'SELECT date, [{subject_id}] '
                                           f'FROM marks WHERE id = {answer[i][0]}').fetchall()
            for j in answer_2:
                if j[0].month == month:
                    if str(j[1]) in ['Н', '5', '4', '3', '2']:
                        example = QtWidgets.QTableWidgetItem(str(j[1]))
                        self.ui.marks.setItem(i, j[0].day, example)
        self.avg_teacher()

    def avg_teacher(self):
        for i in range(self.ui.marks.rowCount()):
            avg = 0.0
            counter = 0
            for j in range(1, self.ui.marks.columnCount() - 1):
                if self.ui.marks.item(i, j) is not None:
                    if self.ui.marks.item(i, j).text() in ['NA', 'Н', 'н', '']:
                        continue
                    avg += float(self.ui.marks.item(i, j).text())
                    counter += 1
            if counter != 0:
                example = QtWidgets.QTableWidgetItem(str(round(avg / counter, 2)))
                example.setFlags(QtCore.Qt.ItemIsEnabled)
                self.ui.marks.setItem(i, self.ui.marks.columnCount() - 1,
                                      example)
            else:
                example = QtWidgets.QTableWidgetItem("NA")
                example.setFlags(QtCore.Qt.ItemIsEnabled)
                self.ui.marks.setItem(i, self.ui.marks.columnCount() - 1,
                                      example)

    def save_marks(self):
        subjects = ['Русский Язык', 'Литература', 'Алгебра', 'Геометрия',
                    'Английский Язык', 'ИКТ',
                    'История', 'Обществознание', 'Физика', 'Химия',
                    'Биология',
                    'ОБЖ', 'Физкультура',
                    'Музыка', 'География',
                    'Экономика',
                    'Право']
        temp_char = '\''
        for i in range(self.ui.marks.rowCount()):
            student_id = int(self.ui.marks.item(i, 0).text())
            for j in range(1, self.ui.marks.columnCount() - 1):
                if self.ui.marks.item(i, j):
                    if self.ui.marks.item(i, j).text() in ['н', 'Н', '2', '3', '4', '5']:
                        temp_date = date(day=j, month=self.month_id, year=datetime.now().year)
                        subject = subjects.index(self.ui.month_name.text().split(', ')[1]) + 1
                        answer = self.cursor.execute(f'SELECT [{subject}] FROM marks WHERE '
                                                     f'(date = CAST({temp_char}{temp_date}{temp_char} as date) '
                                                     f'AND id = {student_id})').fetchone()
                        if answer is None:
                            if self.cursor.execute(f'SELECT id FROM marks WHERE '
                                                   f'(date = CAST({temp_char}{temp_date}{temp_char} as date) '
                                                   f'AND id = {student_id})').fetchone() is None:
                                self.cursor.execute(f'INSERT marks (id, date, [{subject}]) VALUES({student_id}, '
                                                    f'CAST({temp_char}{temp_date}{temp_char} as date), '
                                                    f'{temp_char}{self.ui.marks.item(i, j).text()}{temp_char})')
                                self.SQL_server.conn.commit()
                            else:
                                self.cursor.execute(f'UPDATE marks SET [{subject}] = '
                                                    f'{temp_char}{self.ui.marks.item(i, j).text()}{temp_char} '
                                                    f'WHERE (date = CAST({temp_char}{temp_date}{temp_char} as date) '
                                                    f'AND id = {student_id})')
                                self.SQL_server.conn.commit()
                        else:
                            self.cursor.execute(f'UPDATE marks SET [{subject}] = '
                                                f'{temp_char}{self.ui.marks.item(i, j).text()}{temp_char} '
                                                f'WHERE (date = CAST({temp_char}{temp_date}{temp_char} as date) '
                                                f'AND id = {student_id})')
                            self.SQL_server.conn.commit()
                    else:
                        self.ui.marks.setItem(i, j, QtWidgets.QTableWidgetItem(''))
        self.avg_teacher()

    def get_time_teacher(self):
        if type(self.ui) == Teacher_UI:
            t = Timer(1.0, self.get_time_teacher)
            self.ui.date.setText(datetime.now().strftime("%d.%m.%Y %H:%M"))
            t.start()

    def get_timetable_teacher(self):
        weekdays = ['pn', 'vt', 'sr', 'ch', 'pt', 'sb']
        weekday = datetime.now().weekday()
        answer = self.cursor.execute(f'SELECT {weekdays[weekday]}_first, {weekdays[weekday]}_second, '
                                     f'{weekdays[weekday]}_third, {weekdays[weekday]}_fourth, '
                                     f'{weekdays[weekday]}_fifth, {weekdays[weekday]}_sixth, '
                                     f'{weekdays[weekday]}_seventh, {weekdays[weekday]}_eighth '
                                     f'FROM teacher_timetables WHERE id = {self.id}').fetchone()
        time = '9:00'
        if weekday == 6:
            for i in range(8):
                for j in range(3):
                    self.ui.lessons.setItem(j, i, QtWidgets.QTableWidgetItem('Выходной'))
        else:
            for i in range(len(answer)):
                if answer[i]:
                    t_class, room = answer[i].split('-')
                    self.ui.lessons.setItem(0, i, QtWidgets.QTableWidgetItem(t_class))
                    self.ui.lessons.setItem(2, i, QtWidgets.QTableWidgetItem(room))
                else:
                    self.ui.lessons.setItem(0, i, QtWidgets.QTableWidgetItem('Свободно'))
                    self.ui.lessons.setItem(2, i, QtWidgets.QTableWidgetItem('-'))
                self.ui.lessons.setItem(1, i, QtWidgets.QTableWidgetItem(time))
                hours, minutes = list(map(int, time.split(':')))
                minutes += 55
                if minutes >= 60:
                    minutes -= 60
                    hours += 1
                time = ':'.join(list(map(str, [hours, minutes])))
        self.ui.lessons.resizeColumnsToContents()

    def get_time_student(self):
        if type(self.ui) == Student_UI:
            t = Timer(1.0, self.get_time_student)
            self.ui.date.setText(datetime.now().strftime("%d.%m.%Y %H:%M"))
            answer = self.cursor.execute(f'SELECT readed FROM messages '
                                         f'WHERE id_to = {self.id}').fetchall()
            news = 0
            for i in answer:
                if not i[0]:
                    news += 1
            if news == 0:
                self.ui.news.setText(f'У вас нет новых уведомлений.')
            else:
                self.ui.news.setText(f'У вас {news} новых уведомлений. Прочитайте их в сообщениях.')
            t.start()

    def link_to_timetable(self):
        high = ['https://www.school56.org/images/2020_2021/september/raspisanie/%D0%9F%D0%BE%D0%BD%D0%B5%D0%B4%D0%B5'
                '%D0%BB%D1%8C%D0%BD%D0%B8%D0%BA_%D1%81%D1%82%D0%B0%D1%80%D1%88%D0%B0%D1%8F.pdf',
                'https://www.school56.org/images/2020_2021/september/raspisanie/%D0%92%D1%82%D0%BE%D1%80%D0%BD%D0%B8'
                '%D0%BA_%D1%81%D1%82%D0%B0%D1%80%D1%88%D0%B0%D1%8F.pdf',
                'https://www.school56.org/images/2020_2021/september/raspisanie/%D0%A1%D1%80%D0%B5%D0%B4%D0%B0_%D1%81'
                '%D1%82%D0%B0%D1%80%D1%88%D0%B0%D1%8F.pdf',
                'https://www.school56.org/images/2020_2021/september/raspisanie/%D0%A7%D0%B5%D1%82%D0%B2%D0%B5%D1%80'
                '%D0%B3_%D1%81%D1%82%D0%B0%D1%80%D1%88%D0%B0%D1%8F.pdf',
                'https://www.school56.org/images/2020_2021/september/raspisanie/%D0%9F%D1%8F%D1%82%D0%BD%D0%B8%D1%86'
                '%D0%B0_%D1%81%D1%82%D0%B0%D1%80%D1%88%D0%B0%D1%8F.pdf',
                'https://www.school56.org/images/2020_2021/september/raspisanie/%D0%A1%D1%83%D0%B1%D0%B1%D0%BE%D1%82'
                '%D0%B0_%D1%81%D1%82%D0%B0%D1%80%D1%88%D0%B0%D1%8F.pdf']
        secondary = ['https://www.school56.org/images/2020_2021/september/raspisanie/%D0%BF%D0%BE%D0%BD%D0%B5%D0%B4'
                     '%D0%B5%D0%BB%D1%8C%D0%BD%D0%B8%D0%BA_%D1%81%D1%80%D0%B5%D0%B4%D0%BD%D1%8F%D1%8F.pdf',
                     'https://www.school56.org/images/2020_2021/september/raspisanie/%D0%B2%D1%82%D0%BE%D1%80%D0%BD'
                     '%D0%B8%D0%BA_%D1%81%D1%80%D0%B5%D0%B4%D0%BD%D1%8F%D1%8F.pdf',
                     'https://www.school56.org/images/2020_2021/september/raspisanie/%D1%81%D1%80%D0%B5%D0%B4%D0%B0_'
                     '%D1%81%D1%80%D0%B5%D0%B4%D0%BD%D1%8F%D1%8F.pdf',
                     'https://www.school56.org/images/2020_2021/september/raspisanie/%D1%87%D0%B5%D1%82%D0%B2%D0%B5'
                     '%D1%80%D0%B3_%D1%81%D1%80%D0%B5%D0%B4%D0%BD%D1%8F%D1%8F.pdf',
                     'https://www.school56.org/images/2020_2021/september/raspisanie/%D0%BF%D1%8F%D1%82%D0%BD%D0%B8'
                     '%D1%86%D0%B0_%D1%81%D1%80%D0%B5%D0%B4%D0%BD%D1%8F%D1%8F.pdf',
                     'https://www.school56.org/images/2020_2021/september/raspisanie/%D1%81%D1%83%D0%B1%D0%B1%D0%BE'
                     '%D1%82%D0%B0_%D1%81%D1%80%D0%B5%D0%B4%D0%BD%D1%8F%D1%8F.pdf']
        weekday = datetime.now().weekday()
        class_answer = []
        if type(self.ui) == Student_UI:
            class_answer = self.cursor.execute(f'SELECT class FROM students WHERE id = {self.id}').fetchone()[0]
        elif type(self.ui) == Teacher_UI:
            class_answer = self.school_class
        ans = 0
        for i in range(len(class_answer)):
            if not class_answer[i].isdigit():
                ans = i
                break
        if weekday != 6:
            if int(class_answer[:ans]) in [8, 9, 10, 11]:
                webbrowser.open(high[weekday])
            else:
                webbrowser.open(secondary[weekday])

    def get_timetable_st(self):
        weekday = datetime.now().isoweekday()
        answer = self.cursor.execute(f'SELECT first, second, third, fourth, fifth, sixth, seventh, eighth FROM '
                                     f'timetables WHERE (school IN (SELECT school FROM students WHERE id = {self.id}) '
                                     f'AND class IN (SELECT class FROM students WHERE id = {self.id}) '
                                     f'AND weekday = {weekday})').fetchone()
        time = '9:00'
        if weekday == 7:
            for i in range(8):
                for j in range(3):
                    self.ui.lessons.setItem(j, i, QtWidgets.QTableWidgetItem('Выходной'))
        else:
            for i in range(len(answer)):
                if answer[i] is None:
                    self.ui.lessons.setItem(0, i, QtWidgets.QTableWidgetItem('-'))
                    self.ui.lessons.setItem(2, i, QtWidgets.QTableWidgetItem('-'))
                    self.ui.lessons.setItem(1, i, QtWidgets.QTableWidgetItem(time))
                else:
                    subject, room = answer[i].split('-')
                    self.ui.lessons.setItem(0, i, QtWidgets.QTableWidgetItem(subject))
                    self.ui.lessons.setItem(2, i, QtWidgets.QTableWidgetItem(room))
                    self.ui.lessons.setItem(1, i, QtWidgets.QTableWidgetItem(time))
                hours, minutes = list(map(int, time.split(':')))
                minutes += 55
                if minutes >= 60:
                    minutes -= 60
                    hours += 1
                time = ':'.join(list(map(str, [hours, minutes])))
        self.ui.lessons.resizeColumnsToContents()

    def marks_to_print(self):
        marks, objects = {'Русский Язык': [], 'Литература': [], 'Алгебра': [], 'Геометрия': [], 'Английский Язык': [],
                          'ИКТ': [],
                          'История': [], 'Обществознание': [], 'Физика': [], 'Химия': [], 'Биология': [], 'ОБЖ': [],
                          'Физкультура': [],
                          'Музыка': [], 'География': [], 'Экономика': [],
                          'Право': []}, ['Русский Язык', 'Литература', 'Алгебра', 'Геометрия',
                                         'Английский Язык', 'ИКТ',
                                         'История', 'Обществознание', 'Физика', 'Химия',
                                         'Биология',
                                         'ОБЖ', 'Физкультура',
                                         'Музыка', 'География',
                                         'Экономика',
                                         'Право']
        for i in range(self.ui.marks.rowCount()):
            for j in range(self.ui.marks.columnCount() - 1):
                if self.ui.marks.item(i, j) is not None:
                    if self.ui.marks.item(i, j).text().upper() != 'Н':
                        marks[objects[i]] += [str(self.ui.marks.item(i, j).text())]
        doc = DocxTemplate("scheme.docx")
        temp_result = self.cursor.execute(f'SELECT lastname, name, surname '
                                          f'FROM students WHERE id = {self.id}').fetchall()
        separator = ', '
        context = {'name': temp_result[0][0] + ' ' + temp_result[0][1] + ' ' + temp_result[0][2][0],
                   'month': date(datetime.now().year, self.month_id, 1).strftime("%B"),
                   'o1': separator.join(marks['Русский Язык']),
                   'o2': separator.join(marks['Литература']),
                   'o3': separator.join(marks['Алгебра']),
                   'o4': separator.join(marks['Геометрия']),
                   'o5': separator.join(marks['Английский Язык']),
                   'o6': separator.join(marks['ИКТ']),
                   'o7': separator.join(marks['История']),
                   'o8': separator.join(marks['Обществознание']),
                   'o9': separator.join(marks['Физика']),
                   'o10': separator.join(marks['Химия']),
                   'o11': separator.join(marks['Биология']),
                   'o12': separator.join(marks['ОБЖ']),
                   'o13': separator.join(marks['Физкультура']),
                   'o14': separator.join(marks['Музыка']),
                   'o15': separator.join(marks['География']),
                   'o16': separator.join(marks['Экономика']),
                   'o17': separator.join(marks['Право'])}
        doc.render(context)
        doc.save("final.docx")
        self.ui.all_marks.setText('Готово!')
        t = Timer(3.0, self.change_text_all_marks)
        t.start()

    def change_text_all_marks(self):
        self.ui.all_marks.setText('Выписка оценок')

    def send_msg_student(self):
        self.reconstruct_ui(Add_comment_ui())
        answer = self.cursor.execute(f"SELECT id, classes FROM teachers WHERE (CAST(school as varchar) = "
                                     f"(SELECT school FROM students WHERE id = {self.id}))").fetchall()
        student_school = self.cursor.execute(f"SELECT class FROM students WHERE id = {self.id}").fetchone()[0]
        teachers = {}
        for i in answer:
            temp = i[1].split()
            if student_school in temp:
                answer_2 = self.cursor.execute(f'SELECT name, surname FROM teachers WHERE id = {i[0]}').fetchone()
                self.ui.students_combobox.addItem(answer_2[0] + ' ' + answer_2[1])
                teachers[answer_2[0] + ' ' + answer_2[1]] = i[0]
        self.ui.button_ok.clicked.connect(lambda: self.return_to_student(save=teachers[
            self.ui.students_combobox.currentText()]))
        self.ui.button_cancel.clicked.connect(lambda: self.return_to_student())

        '''
        for i in students:
            self.ui.students_combobox.addItem(i[0])
        self.ui.button_cancel.clicked.connect(lambda: self.return_to_teacher())
        self.ui.button_ok.clicked.connect(lambda: self.return_to_teacher(save=students))
        '''

    def comments_student(self):
        self.reconstruct_ui(comments_stUI())
        self.ui.msg_table.setColumnCount(4)
        header = self.ui.msg_table.horizontalHeader()
        self.ui.msg_table.setHorizontalHeaderLabels(['Дата', 'Отправитель', 'Предмет', 'Сообщение'])
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.ui.msg_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        answer = self.cursor.execute(f'SELECT id_from, message, date, id FROM messages '
                                     f'WHERE id_to = {self.id}').fetchall()
        self.ui.msg_table.setRowCount(len(answer))
        answer = sorted(answer, key=lambda x: x[2])
        for i in range(len(answer)):
            self.ui.msg_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(answer[i][2])))
            answer_2 = self.cursor.execute(f'SELECT name, surname, object FROM teachers WHERE id '
                                           f'= {answer[i][0]}').fetchone()
            self.ui.msg_table.setItem(i, 1, QtWidgets.QTableWidgetItem(' '.join(answer_2[:2])))
            self.ui.msg_table.setItem(i, 2, QtWidgets.QTableWidgetItem(answer_2[2]))
            self.ui.msg_table.setItem(i, 3, QtWidgets.QTableWidgetItem(answer[i][1]))
            self.cursor.execute(f'UPDATE messages SET readed = 1 WHERE id = {answer[i][3]}')
            self.SQL_server.conn.commit()
        self.ui.msg_table.resizeColumnsToContents()
        self.ui.button_exit.clicked.connect(self.return_to_student)
        self.ui.button_action.clicked.connect(self.send_msg_student)

    def return_to_student(self, save=False):
        if save is False:
            self.reconstruct_ui(Student_UI())
            self.load_student()
        else:
            temp_char = '\''
            temp_date = datetime.now()
            self.cursor.execute(f'INSERT messages (id, id_from, id_to, message, date, readed) VALUES (0, {self.id}, '
                                f'{save}, {temp_char}{self.ui.input_comment.text()}{temp_char}, '
                                f'CAST({temp_char}{str(temp_date)[:19]}{temp_char} as datetime), 1)')
            self.SQL_server.conn.commit()
            self.reconstruct_ui(Student_UI())
            self.load_student()

    def exit(self):
        self.reconstruct_ui(Ui_Login())
        self.ui.button_enter.clicked.connect(self.login_button_pressed)

    def show_messages_teacher(self):
        self.reconstruct_ui(Teacher_comm())
        self.ui.button_exit.clicked.connect(lambda: self.return_to_teacher())
        answer = self.cursor.execute(f'SELECT date, id_from, message FROM messages WHERE ('
                                     f'id_to = {self.id})').fetchall()
        answer = sorted(answer, key=lambda x: x[0])
        self.ui.msg_table.setRowCount(len(answer))
        self.ui.msg_table.setColumnCount(3)
        self.ui.msg_table.setHorizontalHeaderLabels(['Дата', 'Отправитель', 'Сообщение'])
        students_from = []
        for i in answer:
            students_from.append(self.cursor.execute(f'SELECT id, name, lastname, class FROM students WHERE id = '
                                                     f'{i[1]}').fetchone())
        for i in range(len(answer)):
            self.ui.msg_table.setItem(i, 1, QtWidgets.QTableWidgetItem(students_from[i][2] + ' ' + students_from[i][1]
                                                                       + ', ' + students_from[i][3]))
            self.ui.msg_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(answer[i][0])))
            self.ui.msg_table.setItem(i, 2, QtWidgets.QTableWidgetItem(answer[i][2]))
        header = self.ui.msg_table.horizontalHeader()
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)

    def load_student(self):
        temp_result = self.cursor.execute(f'SELECT lastname, name, surname, class '
                                          f'FROM students WHERE id = {self.id}').fetchall()
        self.ui.username.setText(temp_result[0][0] + ' ' + temp_result[0][1] + ' ' + temp_result[0][2][0] + '.')
        self.ui.ID.setText(f'ID: {self.id}  |  Класс: {temp_result[0][3]}')
        self.get_time_student()
        self.ui.month_name.setText(datetime.now().strftime("%B"))
        self.ui.marks.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        p = "'" + str(temp_result[0][3]) + "'"
        temp_result = self.cursor.execute(f"SELECT name FROM class_teacher WHERE (CAST(school as varchar) IN ("
                                          f"SELECT school FROM students WHERE id = {self.id}) "
                                          f"AND (CAST(class as varchar) = {p}))").fetchone()
        answer = self.cursor.execute(f'SELECT readed FROM messages '
                                     f'WHERE id_to = {self.id}').fetchall()
        news = 0
        for i in answer:
            if not i[0]:
                news += 1
        if news == 0:
            self.ui.news.setText(f'У вас нет новых уведомлений.')
        else:
            self.ui.news.setText(f'У вас {news} новых уведомлений. Прочитайте их в сообщениях.')
        self.ui.class_ruk_name.setText(temp_result[0])
        self.month_id = datetime.now().month
        self.reconstruct_student_table(self.month_id)
        self.ui.exit.clicked.connect(self.exit)
        self.ui.add_comm.clicked.connect(self.comments_student)
        self.get_timetable_st()
        if datetime.now().month in [9, 10]:
            self.ui.absence.setText('I')
        elif datetime.now().month in [11, 12]:
            self.ui.absence.setText('II')
        elif datetime.now().month in [1, 2, 3]:
            self.ui.absence.setText('III')
        elif datetime.now().month in [4, 5]:
            self.ui.absence.setText('IV')
        else:
            self.ui.absence.setText('Каникулы')
        self.ui.left_pushbutton.clicked.connect(lambda: self.month_swap(False))
        self.ui.right_pushbutton.clicked.connect(lambda: self.month_swap(True))
        self.ui.timetable_link.clicked.connect(self.link_to_timetable)
        self.ui.all_marks.clicked.connect(self.marks_to_print)
        self.ui.minimum_link.clicked.connect(minimum_info)

    def month_swap(self, r=False):
        if r:
            self.month_id += 1
            if self.month_id > 12:
                self.month_id = self.month_id - 12
            self.reconstruct_student_table(self.month_id)
        else:
            self.month_id -= 1
            if self.month_id < 1:
                self.month_id = self.month_id + 12
            self.reconstruct_student_table(self.month_id)

    def avg_mark(self):
        for i in range(self.ui.marks.rowCount()):
            avg = 0.0
            counter = 0
            for j in range(self.ui.marks.columnCount()):
                if self.ui.marks.item(i, j) is not None:
                    if self.ui.marks.item(i, j).text() == 'NA' or self.ui.marks.item(i, j).text().upper() == 'Н':
                        continue
                    avg += float(self.ui.marks.item(i, j).text())
                    counter += 1
            if counter != 0:
                self.ui.marks.setItem(i, self.ui.marks.columnCount() - 1,
                                      QtWidgets.QTableWidgetItem(str(round(avg / counter, 2))))
            else:
                self.ui.marks.setItem(i, self.ui.marks.columnCount() - 1,
                                      QtWidgets.QTableWidgetItem("NA"))

    def reconstruct_student_table(self, month: int):
        cols, a = mdays[month], ['Русский Язык', 'Литература', 'Алгебра', 'Геометрия', 'Английский Язык', 'ИКТ',
                                 'История', 'Обществознание', 'Физика', 'Химия', 'Биология', 'ОБЖ', 'Физкультура',
                                 'Музыка', 'География', 'Экономика',
                                 'Право']
        self.ui.marks.setColumnCount(0)
        self.ui.marks.setRowCount(0)
        self.ui.marks.setColumnCount(cols + 1)
        self.ui.marks.setRowCount(17)
        self.ui.marks.setHorizontalHeaderLabels([str(i) for i in range(1, cols + 1)] + ['Ср. знач'])
        self.ui.marks.setVerticalHeaderLabels([a[i] for i in range(17)])
        self.ui.marks.resizeColumnsToContents()
        self.ui.month_name.setText(date(datetime.now().year, self.month_id, 1).strftime("%B"))
        for i in range(1, 21):
            self.cursor.execute(f"UPDATE marks SET [{i}] = '-1' WHERE [{i}] IS NULL")
        temp_result = self.cursor.execute(f'SELECT date, '
                                          f'{", ".join(["[" + str(i) + "]" for i in range(1, 18)])} '
                                          f'FROM marks WHERE id = {self.id}').fetchall()
        marks = {}
        for i in temp_result:
            marks[str(i[0].day) + '.' + str(i[0].month)] = [j for j in i[1:]]
        for i in marks:
            day, month_2 = i.split('.')
            day, month_2 = int(day), int(month_2)
            if month_2 == month:
                for j in range(self.ui.marks.columnCount() - 1):
                    if self.ui.marks.horizontalHeaderItem(j).text() == str(day):
                        for jj in range(self.ui.marks.rowCount()):
                            if marks[i][jj] != '-1':
                                self.ui.marks.setItem(jj, j, QtWidgets.QTableWidgetItem(marks[i][jj]))
                        break
        self.avg_mark()

    def reconstruct_ui(self, form):
        self.main_window.close()
        self.ui, self.main_window = form, QtWidgets.QMainWindow()
        self.ui.setupUi(self.main_window)
        self.main_window.show()

    def main(self):
        sys.exit(self.app.exec_())


program = Application()
