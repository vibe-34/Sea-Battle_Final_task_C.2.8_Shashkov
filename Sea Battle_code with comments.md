import pyautogui
from random import randint


class Name:
    """ Класс определяющий имена игроков. Пользователь сам задает своё имя, после прочтений/не прочтений правил игры """
    user_1 = None
    user_2 = 'Джек Воробей'


class Dot:
    """ Класс точка. Принимает параметры X и Y. Сравнивает между собой два объекта (две точки) и определяет
        есть ли точка в списке точек кораблей или простреленных точек. """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        """ Сравнение между собой двух объектов (две точки). """
        return self.x == other.x and self.y == other.y  # 1 аргумент - то что сравнивают, 2 аргумент - с чем сравнивают

    def __repr__(self):
        """ Вывод точек в консоль, для проверки - есть ли точка в списке. """
        return f'Dot({self.x}, {self.y})'  # например: есть ли точка в списке кораблей


class BoardException(Exception):
    """ Общий класс исключений, содержит в себе все исключения. """
    pass


class BoardOutException(BoardException):
    """ Исключение при стрельбе за пределы игрового поля. """

    def __str__(self):
        return "Ваше орудие не на столько дальнобойное!"


class BoardUsedException(BoardException):
    """ Исключение при повторной стрельбе в одну точку. """

    def __str__(self):
        return "Ядро в одну воронку не попадает."


class BoardWrongShipException(BoardException):
    """ Собственное исключение, для размещения кораблей """
    pass


class Ship:
    """ Класс корабля. Определяет его размер (количество палуб), ориентацию (вертикальный, горизонтальный),
        было ли попадание в корабль """

    def __init__(self, bow, deck, orient):
        self.bow = bow                                   # координата носа корабля
        self.deck = deck                                 # количество палуб (длина корабля)
        self.orient = orient       # параметр, который задает ориентацию корабля (если 0-вертикальный, 1-горизонтальный)
        self.lives = deck                                # уровень корабля

    @property
    def dots(self):
        """ Метод, который определяющий свойство корабля. """
        ship_dots = []                                   # список точек корабля
        for i in range(self.deck):             # проходимся по списку корабля, от 0 по всем палубам (длины корабля) -1
            cur_x = self.bow.x                           # получаем список наших точек (данные точки - это нос корабля)
            cur_y = self.bow.y
            if self.orient == 0:                         # вертикальное размещение
                cur_x += i                         # от носа корабля сдвигаемся на i точек, что бы описать весь корабль
            elif self.orient == 1:                       # горизонтальное размещение
                cur_y += i
            ship_dots.append(Dot(cur_x, cur_y))          # формируем список точек корабля
        return ship_dots

    def shoten(self, shot):
        """ Метод, показывает, попали мы в цель или нет"""
        return shot in self.dots


class Board:
    """ Класс игрового поля. Определяет характеристики доски, размер, скрытие доски противника, состояние сетки поля
        (занята клетка, кораблем или в неё сделан выстрел). В случае поражения корабля, обводит его по контуру.
        Сравнение количества пораженных кораблей с первоначальным числом (для выявления победного исхода). """

    def __init__(self, hid=False, size=10):
        self.size = size                                  # аргумент размера поля
        self.hid = hid                                    # аргумент скрытия поля
        self.count = 0                                    # количество пораженных кораблей
        self.field = [["◌"] * size for _ in range(size)]  # состояние сетки поля, ◌-клетка не занята и не сделан выстрел
        self.busy = []                                    # список занятых точек или кораблем или после выстрела
        self.ships = []                                   # список кораблей доски

    def __str__(self):
        """ Печать доски при вызове класса. """
        res = ""                                          # в данную переменную записываем нашу доску
        res += "⚓| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |"
        for i, row in enumerate(self.field):              # проходимся по строкам доски, достаем индекс i
            res += f"\n{i + 0} | " + " | ".join(row) + " |"  # {i + 0} выводим номер строки и через | клетки строки
        if self.hid:                                      # в случае скрытия кораблей на доске
            res = res.replace(Color("■", 34).my_color(), "◌")  # все символы корабля "■" заменяем на пустые символы "◌"
        return res

    def out(self, d):
        """ Определяет, нахождение точки, за пределами доски"""
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))  # отрицание, что координаты лежат от 0 до size

    def contour(self, ship, verb=False):
        """ Для ограничения совмещения кораблей между собой при расстановке. """
        near = [(-1, -1), (-1, 0), (-1, 1),             # список содержит сдвиги, относительно нас,  точка (0, 0)
                (0, -1), (0, 0), (0, 1),
                (1, -1), (1, 0), (1, 1)]                # это все точки, вокруг той, в которой мы находимся
        for d in ship.dots:                             # берем каждую точку корабля
            for dx, dy in near:                         # точкой корабля проходимся по списку точек вокруг себя
                cur = Dot(d.x + dx, d.y + dy)  # и сдвигаем исходную точку на dx и dy (1-ю и 2-ю переменную из кортежа)
                if not (self.out(cur)) and cur not in self.busy:  # если точка не выходит за границы и еще не занята
                    if verb:          # параметр говорит о необходимости ставить точки вокруг корабля при его поражении
                        self.field[cur.x][cur.y] = "●"  # то на её месте ставим знак "●"
                    self.busy.append(cur)               # и добавляем в список занятых

    def add_ship(self, ship):
        """ Для размещения кораблей. """
        for d in ship.dots:
            if self.out(d) or d in self.busy:     # проверка, что каждая точка корабля не выходит за границы и не занята
                raise BoardWrongShipException()         # если это не так, то выбрасываем исключение
        for d in ship.dots:                             # пройдемся по точкам корабля
            self.field[d.x][d.y] = Color("■", 34).my_color()   # и в каждую точку поставим знак "■"
            self.busy.append(d)                         # и запишем эти точки в список занятых точек
        self.ships.append(ship)                         # добавляем в список своих кораблей
        self.contour(ship)                              # и обводим его по контуру

    def shot(self, d):
        """ Делает выстрел, определяет его характер (попал, мимо, подбил """
        if self.out(d):                                 # проверка выхода точки за границы
            raise BoardOutException()                   # если выходит, выбрасываем исключение
        if d in self.busy:                              # проверка на занятость точки
            raise BoardUsedException()                  # если занята, выбрасываем исключение
        self.busy.append(d)                             # если точка не была занята, то добавляем её в список занятых
        for ship in self.ships:          # проходимся по точкам корабля и проверяем принадлежит эта точка к ним или нет
            if ship.shoten(d):                          # вызов метода shoten, если корабль был прострелен этой точкой
                ship.lives -= 1                         # то уровень корабля уменьшается на -1
                self.field[d.x][d.y] = Color("X", 31).my_color()      # и на это место ставится знак "X" красного цвета
                if ship.lives == 0:                     # если уровень корабля становится 0
                    self.count += 1                     # то прибавляем 1 к счетчику уничтоженных кораблей
                    self.contour(ship, verb=True)       # обводим его точками по контуру
                    print(Color('Уничтожен!', 31).my_color())
                    return False                        # возвращаем False, что дальше ход делать не нужно
                else:
                    print(Color('Пробитие палубы!', 31).my_color())
                    return True        # если корабль не был уничтожен, возвращаем True, что нужно сделать следующий ход
        self.field[d.x][d.y] = "●"                      # если попадания не было, то ставим знак "●"
        print(Color('Промах, перезаряжай!', 31).my_color())
        return False                                    # возвращаем False, что дальше ход делать не нужно

    def begin(self):
        """ Перед игрой, обнуляем список занятых точек т.к. он был занят при расстановке кораблей, а теперь он нужен
            для сохранения точек прострелов"""
        self.busy = []

    def defeat(self):
        """ Сравнение кол. пораженных кораблей с кол. кораблей доски. """
        return self.count == len(self.ships)


class Player:
    """ Класс игрока. Передача двух досок, запрос координат выстрела, через потомков """

    def __init__(self, board, enemy):
        self.board = board
        self.enemy = enemy

    def ask(self):
        """ Метод, должен быть у потомков этого класса, в случае вызова, выбрасываем исключение"""
        raise NotImplementedError()

    def move(self):
        """ В бесконечном цикле пытаемся сделать выстрел. """
        while True:
            try:
                target = self.ask()                     # просим ПК или игрока, дать координаты цели
                repeat = self.enemy.shot(target)        # если выстрел успешный
                return repeat                           # то возвращаем то, что нужно сделать еще один выстрел
            except BoardException as e:  # если точка выстрела не допустима, выбрасываем исключение и цикл продолжается
                print(e)


class AI(Player):
    """ Класс игрока AI, генерация случайных точек выстрела. """

    def ask(self):
        d = Dot(randint(0, 9), randint(0, 9))           # у ПК генерируем случайным образом две точки от 0 до 9
        print(f"Задать координаты! Огонь!: {d.x + 1} {d.y + 1}")
        return d


class User(Player):
    """ Класс игрока, пользователь. Получение координат выстрела и проверка на корректность их ввода. """

    def ask(self):
        while True:
            cords = input("Задать координаты! Огонь!: ").split()  # запрос координат у игрока
            if len(cords) != 2:                                   # проверка на ввод двух координат
                print(" Введите 2 координаты! ")
                continue
            x, y = cords
            if not (x.isdigit()) or not (y.isdigit()):            # проверка, что это числа
                print(" Введите числа! ")
                continue
            x, y = int(x), int(y)
            return Dot(x, y)              # Возвращаем нашу точку, вычитая единицу т.к. индексация с нуля, а игроку с 1


class Color:
    """ Принимает два аргумента: текст и номер цвета. Возвращает окрашенный текст."""

    def __init__(self, pos, color):
        self.color = color
        self.pos = pos

    def my_color(self):
        return f"\033[{self.color}m{self.pos}\033[0;0m"


class Game:
    """ """

    def __init__(self, size=10):                         # задаем размер доски
        self.size = size
        pl = self.random_board()                         # генерируем доску для пользователя
        co = self.random_board()                         # генерируем доску для AI
        co.hid = True                                    # для AI скрываем корабли при помощи параметра hid
        self.ai = AI(co, pl)                             # создаем игрока AI
        self.us = User(pl, co)                           # создаем игрока пользователь

    def random_place(self):
        """ Рандомная расстановка кораблей"""
        lens = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]            # список длин кораблей
        board = Board(size=self.size)                    # создаем доску
        attempts = 0                                     # количество попыток расставить корабли
        for length in lens:                # для каждой длины корабля, в бесконечном цикле будем пытаться его поставить
            while True:
                attempts += 1
                if attempts > 2000:                      # 2000 попыток на расстановку кораблей
                    return None                          # в случае не удачи 2000 раз, выводим сообщение None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), length, randint(0, 1))
                try:
                    board.add_ship(ship)                 # добавление корабля на игровое поле
                    break
                except BoardWrongShipException:
                    pass
        board.begin()
        return board

    def random_board(self):
        """ Гарантированный метод вывода игрового поля. """
        board = None
        while board is None:                             # бесконечный цикл пока нет игрового поля
            board = self.random_place()
        return board

    @staticmethod
    def greet():
        """ Приветствие. """
        print()
        print('*' * 13, Color("Морской бой", 32).my_color(), '*' * 13)
        print('         Добро пожаловать друзья !')
        print()

        decision = input('Хотите прочитать правила?: ').lower()
        while decision != 'да' and decision != 'нет':
            print('Введите корректный ответ ДА или НЕТ')
            decision = input('Хотите прочитать правила?: ').lower()
        if decision == 'да':
            res = pyautogui.confirm(text=f'* Два противника, Вы и {Name.user_2}\n'  # Модальное окно
                                         '* Задача поразить все корабли противника.\n'
                                         '* Первый ход делает игрок.\n'
                                         '* Для хода, необходимо ввести координаты поля, X и Y\n'
                                         '* Координаты вводятся через пробел (пример: 1 2)\n'
                                         '** 1 вводим X - это строка\n'
                                         '** 2 вводим Y - это столбец\n',
                                    title='Правила игры «Морской бой»',
                                    buttons=['Начнем игру', 'В другой раз'])
            if res == 'В другой раз':
                print()
                print('Очень жаль, что вы передумали.\n''До новых встреч.')
                exit()
        elif decision == 'нет':
            print('Тогда начнем!')
            print()

    @staticmethod
    def acquaintance():
        """ Знакомство с игроком. """
        print('*' * 43)
        print()
        Name.user_1 = input('Представься, морской волк: ')
        print(f'{Name.user_1}, ваш противник {Name.user_2}')
        print()
        print('*' * 43)

    def print_boards(self):
        """ Вывод игровых досок. """
        print("-" * 43)
        print()
        print(f"Акватория - {Name.user_1}")
        print(self.us.board)                              # выводим доску пользователя
        print("-" * 43)
        print()
        print(f"Акватория - {Name.user_2}")
        print(self.ai.board)                              # выводим доску ПК
        print("-" * 43)

    def loop(self):
        """ Бесконечный игровой цикл, продолжается до победы. Определяет чей ход и кто одержал победу. """
        num = 0                                           # номер хода
        while True:
            self.print_boards()
            if num % 2 == 0:                              # если номер хода четный
                print(f'Стреляет {Name.user_1}!')         # ходит пользователь
                repeat = self.us.move()                   # записываем результат выстрела пользователя
            else:
                print(f'Стреляет {Name.user_2}!')         # иначе ходит AI
                repeat = self.ai.move()                   # записываем результат выстрела AI
            if repeat:                                    # если результат "попадание", то можно сделать еще один ход
                num -= 1                                  # значение num уменьшаем на 1, что бы сделать еще один ход

            if self.ai.board.defeat():                 # проверка на количество пораженных кораблей игроком на доске AI
                self.print_boards()                       # вывод доски после победного выстрела
                print('-' * 43)
                print(f'Выиграл {Name.user_1}!')
                break

            if self.us.board.defeat():                 # проверка на количество пораженных кораблей AI на доске игрока
                self.print_boards()                       # вывод доски после победного выстрела
                print('-' * 43)
                print(f'Выиграл {Name.user_2}!')
                break
            num += 1                                      # если количество уничтоженных кораблей < 10 прибавляем 1

    def start(self):
        self.greet()
        self.acquaintance()
        self.loop()


g = Game()
g.start()