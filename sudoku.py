import os
import pickle
from random import choice, randint


class board:
    def __init__(self, size=3, ai=None):
        if ai is None:
            self.size = size
            self.table = [[((i * size + i // size + j) % (size ** 2) + 1)
                           for i in range(size ** 2)] for j in range(size ** 2)]
        else:
            self.size = size
            self.table = ai

    def get_row_values(self, row: int, game_map: list):
        tmp = set()
        for i in range(self.size ** 2):
            if game_map[row][i] != 0:
                tmp.add(game_map[row][i])
        return tmp

    def get_col_values(self, col: int, game_map: list):
        tmp = set()
        for i in range(self.size ** 2):
            if game_map[i][col] != 0:
                tmp.add(game_map[i][col])
        return tmp

    def get_block_values(self, row: int, col: int, game_map: list):
        tmp = set()
        row_area, col_area = row // self.size, col // self.size
        for i in range(self.size * row_area, self.size * (row_area + 1)):
            for j in range(self.size * col_area, self.size * (col_area + 1)):
                tmp.add(game_map[i][j])
        return tmp

    def find_possible_values(self, row: int, col: int, game_map: list):
        possible_values = {i for i in range(1, self.size ** 2 + 1)}
        possible_values -= self.get_row_values(row, game_map)
        possible_values -= self.get_col_values(col, game_map)
        possible_values -= self.get_block_values(row, col, game_map)
        return possible_values

    def to_solve(self, board=None):
        if board is None:
            board = self.table
        solved = []
        for i in board:
            solved.append(i[:])
        if self.solver(solved):
            self.solver(solved)
            return solved
        return None

    def solver(self, solved):
        global ai
        if ai is True:
            print('Testing this board:')
            for i in solved:
                print(i)
        while True:
            minValue = None
            for row in range(self.size ** 2):
                for col in range(self.size ** 2):
                    if solved[row][col] != 0:
                        """
                        if ai:
                            print(f'{row + 1}, {col + 1} - skip, already filled')
                        """
                        continue
                    possible_Values = self.find_possible_values(row, col, solved)
                    if len(possible_Values) == 0:
                        if ai:
                            print(f'{row + 1}, {col + 1} - failure.')
                        return False
                    elif len(possible_Values) == 1:
                        if ai:
                            print(f'{row + 1}, {col + 1} - found 1 possible value {possible_Values}.')
                        minValue = ((row, col), possible_Values)
                    elif not minValue or len(possible_Values) < len(minValue[1]):
                        if ai:
                            print(f'{row + 1}, {col + 1} - found '
                                  f'{len(possible_Values)} possible values ({possible_Values}). It is better than '
                                  f'previous option.')
                        minValue = ((row, col), possible_Values)
            if not minValue:
                if ai:
                    print('Already solved')
                return True
            elif 1 <= len(minValue[1]):
                if ai:
                    print(f'The best cell at this iteration is '
                          f'{(minValue[0][0] + 1, minValue[0][1] + 1)} with next possible values: '
                          f'{minValue[1]}')
                break
        row, col = minValue[0]
        for value in minValue[1]:
            if ai:
                print(f'Testing {(minValue[0][0] + 1, minValue[0][1] + 1)} with {value}')
            solved_copy = [i[:] for i in solved]
            solved_copy[row][col] = value
            if self.solver(solved_copy):
                for row in range(self.size ** 2):
                    for col in range(self.size ** 2):
                        solved[row][col] = solved_copy[row][col]
                return True
        if ai:
            print('Mission failed. We`ll get`em next time.')
        return False

    def remover(self, n: int):
        diff = 0
        seen = [[0 for i in range(self.size ** 2)] for j in range(self.size ** 2)]
        while diff < n:
            x, y = randint(0, self.size ** 2 - 1), randint(0, self.size ** 2 - 1)
            if seen[x][y] == 0:
                seen[x][y] = 1
                temp = self.table[x][y]
                self.table[x][y] = 0
                if self.solver(self.table):
                    diff += 1
                else:
                    seen[x][y] = 0
                    self.table[x][y] = temp
        for i in range(self.size ** 2):
            for j in range(self.size ** 2):
                if seen[i][j] == 1:
                    self.table[i][j] = 0

    def transpose(self):
        self.table = [[self.table[i][j] for i in range(self.size ** 2)] for j in range(self.size ** 2)]

    def swap_rows(self):
        temp = []
        for i in range(self.size):
            temp.append(i)
        area = choice(temp)
        row_1 = choice(temp)
        temp.remove(row_1)
        row_2 = choice(temp)
        for i in range(self.size ** 2):
            self.table[row_1 + area * self.size][i], self.table[row_2 + area * self.size][i] = \
                self.table[row_2 + area * self.size][i], self.table[row_1 + area * self.size][i]
        temp.clear()

    def swap_cols(self):
        temp = [i for i in range(self.size)]
        area = choice(temp)
        col_1 = choice(temp)
        temp.remove(col_1)
        col_2 = choice(temp)
        for i in range(self.size ** 2):
            self.table[i][col_1 + area * self.size], self.table[i][col_2 + area * self.size] = \
                self.table[i][col_2 + area * self.size], self.table[i][col_1 + area * self.size]
        temp.clear()
        pass

    def swap_row_area(self):
        temp = [i for i in range(self.size)]
        area_1 = choice(temp)
        temp.remove(area_1)
        area_2 = choice(temp)
        for i in range(self.size):
            for j in range(self.size ** 2):
                self.table[i + area_1 * self.size][j], self.table[i + area_2 * self.size][j] = \
                    self.table[i + area_2 * self.size][j], self.table[i + area_1 * self.size][j]

    def check(self, row, col, x):
        if x in self.find_possible_values(row, col, self.table):
            return True
        return False

    def swap_col_area(self):
        temp = [i for i in range(self.size)]
        area_1 = choice(temp)
        temp.remove(area_1)
        area_2 = choice(temp)
        for i in range(self.size ** 2):
            for j in range(self.size):
                self.table[i][j + area_1 * self.size], self.table[i][j + area_2 * self.size] = \
                    self.table[i][j + area_2 * self.size], self.table[i][j + area_1 * self.size]

    def __str__(self):
        if self.size > 3:
            text_board = '-' * ((self.size ** 2 - 1) * 3 + self.size ** 2 * 2 + 4) + '\n'
        else:
            text_board = '-' * ((self.size ** 2 - 1) * 3 + self.size ** 2 + 4) + '\n'
        for i in range(self.size ** 2):
            for j in range(0, (self.size - 1) ** 2, self.size):
                if j == 0:
                    text_board += '| '
                if self.size > 3:
                    text_board += '   '.join(' ' + i if int(i) < 10 else i for i in
                                             list(map(str, self.table[i][j:j + self.size]))) + ' | '
                else:
                    text_board += '   '.join(list(map(str, self.table[i][j:j + self.size]))) + ' | '
            if self.size > 3:
                text_board += '   '.join(' ' + i if int(i) < 10 else i for i in
                                         list(map(str, self.table[i][j + self.size:j + self.size * 2]))) + ' |\n'
            else:
                text_board += '   '.join(list(map(str, self.table[i][j + self.size:j + self.size * 2]))) + ' |\n'
            if (i + 1) % self.size == 0 and i != self.size ** 2 - 1:
                for j in range(self.size - 1):
                    if j == 0:
                        text_board += '+-'
                    if self.size > 3:
                        text_board += '-' * ((self.size - 1) * 3 + self.size * 2) + '-+-'
                    else:
                        text_board += '-' * ((self.size - 1) * 3 + self.size) + '-+-'
                if self.size > 3:
                    text_board += '-' * ((self.size - 1) * 3 + self.size * 2) + '-+\n'
                else:
                    text_board += '-' * ((self.size - 1) * 3 + self.size) + '-+\n'
        if self.size > 3:
            text_board += '-' * ((self.size ** 2 - 1) * 3 + self.size ** 2 * 2 + 4)
        else:
            text_board += '-' * ((self.size ** 2 - 1) * 3 + self.size ** 2 + 4)
        return text_board


def start_game():
    global ai
    ai = False
    mix_funcs = ('swap_rows()', 'swap_cols()', 'swap_col_area()', 'swap_row_area()', 'transpose()')
    files = os.listdir('.')
    temp_files, a = [], 0
    for i in files:
        if i.split('.')[1] == 'pickle':
            temp_files.append(i)
    if temp_files:
        print('У вас найдены некоторые сохранения. Если вы желаете продолжить игру, то '
              'введите название одного из файлов ниже.\nЕсли же нет, то введите 0.')
        for i in temp_files:
            print(i)
        a = input()
    if a == '0':
        game_board = board(int(input('Размер поля (M**2 x M**2). M = ')), None)
        for i in range(1000):
            eval('game_board.' + choice(mix_funcs))
        n = int(input('Сколько ячеек следует \'убрать\': '))
        while n >= game_board.size ** 4:
            print(f'Неверно введено число. Пожалуйста, '
                  f'введите число, меньшее количества ячеек ({game_board.size ** 4}):',
                  end=' ')
            n = int(input())
        game_board.remover(n)
    else:
        with open(a, 'rb') as f:
            game_board = pickle.load(f)
        n = 0
        for i in game_board.table:
            for j in i:
                if j == 0:
                    n += 1
    print(game_board)
    while n > 0:
        temp = input('Введите ваш ход. (Формат: "строка колонка число").\n'
                                   'Если вы хотите сохранить игру - введите любую строку без пробелов.\n').split(' ')
        if len(temp) == 1:
            counter = 1
            while True:
                if os.path.isfile(f'data{counter}.pickle'):
                    counter += 1
                else:
                    break
            with open(f'data{counter}.pickle', 'wb') as f:
                pickle.dump(game_board, f)
            print('Игра успешно сохранена. Удачи!')
            raise SystemExit

        row, col, x = list(map(int, temp))
        row, col = row - 1, col - 1
        if game_board.check(row, col, x):
            n -= 1
            game_board.table[row][col] = x
            if game_board.solver([game_board.table[i][:] for i in range(len(game_board.table))]):
                print('\n', game_board, sep='')
            else:
                return ('К сожалению, вы не сможете решить данное судоку из данного положения. ' +
                        'Вы проиграли. Начать новую игру? (1 - да, 0 - нет)')
        else:
            print('Вы не можете поставить данное число в эту ячейку.')
    return 'Вы выиграли. Начать новую игру? (1 - да, 0 - нет)'


def start_game_mode2():
    global ai
    ai = True
    n = int(input('Поле какого размера вы хотите задать? (M**2 x M**2)\nM = '))
    print(f'\nТеперь введите {n ** 2} строк, содержащих числа через пробел. 0 - пустая клетка.')
    table = []
    for i in range(n ** 2):
        temp_row = list(map(int, input().split()))
        table.append(temp_row)
    game_board = board(n, ai=table)
    game_board.solver(game_board.table)
    print()


while True:
    mode = input('Выберите режим игры:\n1 - Вы решаете судоку\n2 - Компьютер решает судоку\n')
    if mode == '1':
        print(start_game())
        a = input()
        if a == '1':
            print('\n\n')
            continue
        else:
            break
    else:
        start_game_mode2()
