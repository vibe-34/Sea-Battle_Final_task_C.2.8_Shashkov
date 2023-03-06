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
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        """ Вывод точек в консоль, для проверки - есть ли точка в списке. """
        return f'Dot({self.x}, {self.y})'


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
        self.bow = bow
        self.deck = deck
        self.orient = orient
        self.lives = deck

    @property
    def dots(self):
        """ Метод, который определяющий свойство корабля. """
        ship_dots = []
        for i in range(self.deck):
            cur_x = self.bow.x
            cur_y = self.bow.y
            if self.orient == 0:
                cur_x += i
            elif self.orient == 1:
                cur_y += i
            ship_dots.append(Dot(cur_x, cur_y))
        return ship_dots

    def shoten(self, shot):
        """ Метод, показывает, попали мы в цель или нет"""
        return shot in self.dots


class Board:
    """ Класс игрового поля. Определяет характеристики доски, размер, скрытие доски противника, состояние сетки поля
        (занята клетка, кораблем или в неё сделан выстрел). В случае поражения корабля, обводит его по контуру.
        Сравнение количества пораженных кораблей с первоначальным числом (для выявления победного исхода). """

    def __init__(self, hid=False, size=10):
        self.size = size
        self.hid = hid
        self.count = 0
        self.field = [["◌"] * size for _ in range(size)]
        self.busy = []
        self.ships = []

    def __str__(self):
        """ Печать доски при вызове класса. """
        res = ""
        res += "⚓| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |"
        for i, row in enumerate(self.field):
            res += f"\n{i + 0} | " + " | ".join(row) + " |"
        if self.hid:
            res = res.replace(Color("■", 34).my_color(), "◌")
        return res

    def out(self, d):
        """ Определяет, нахождение точки, за пределами доски"""
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))

    def contour(self, ship, verb=False):
        """ Для ограничения совмещения кораблей между собой при расстановке. """
        near = [(-1, -1), (-1, 0), (-1, 1),
                (0, -1), (0, 0), (0, 1),
                (1, -1), (1, 0), (1, 1)]
        for d in ship.dots:
            for dx, dy in near:
                cur = Dot(d.x + dx, d.y + dy)
                if not (self.out(cur)) and cur not in self.busy:
                    if verb:
                        self.field[cur.x][cur.y] = "●"
                    self.busy.append(cur)

    def add_ship(self, ship):
        """ Для размещения кораблей. """
        for d in ship.dots:
            if self.out(d) or d in self.busy:
                raise BoardWrongShipException()
        for d in ship.dots:
            self.field[d.x][d.y] = Color("■", 34).my_color()
            self.busy.append(d)
        self.ships.append(ship)
        self.contour(ship)

    def shot(self, d):
        """ Делает выстрел, определяет его характер (попал, мимо, подбил """
        if self.out(d):
            raise BoardOutException()
        if d in self.busy:
            raise BoardUsedException()
        self.busy.append(d)
        for ship in self.ships:
            if ship.shoten(d):
                ship.lives -= 1
                self.field[d.x][d.y] = Color("X", 31).my_color()
                if ship.lives == 0:
                    self.count += 1
                    self.contour(ship, verb=True)
                    print(Color('Уничтожен!', 31).my_color())
                    return False
                else:
                    print(Color('Пробитие палубы!', 31).my_color())
                    return True
        self.field[d.x][d.y] = "●"
        print(Color('Промах, перезаряжай!', 31).my_color())
        return False

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
                target = self.ask()
                repeat = self.enemy.shot(target)
                return repeat
            except BoardException as e:
                print(e)


class AI(Player):
    """ Класс игрока AI, генерация случайных точек выстрела. """

    def ask(self):
        d = Dot(randint(0, 9), randint(0, 9))
        print(f"Задать координаты! Огонь!: {d.x + 1} {d.y + 1}")
        return d


class User(Player):
    """ Класс игрока, пользователь. Получение координат выстрела и проверка на корректность их ввода. """

    def ask(self):
        while True:
            cords = input("Задать координаты! Огонь!: ").split()
            if len(cords) != 2:
                print(" Введите 2 координаты! ")
                continue
            x, y = cords
            if not (x.isdigit()) or not (y.isdigit()):
                print(" Введите числа! ")
                continue
            x, y = int(x), int(y)
            return Dot(x, y)


class Color:
    """ Принимает два аргумента: текст и номер цвета. Возвращает окрашенный текст."""

    def __init__(self, pos, color):
        self.color = color
        self.pos = pos

    def my_color(self):
        return f"\033[{self.color}m{self.pos}\033[0;0m"


class Game:
    """ """

    def __init__(self, size=10):
        self.size = size
        pl = self.random_board()
        co = self.random_board()
        co.hid = True
        self.ai = AI(co, pl)
        self.us = User(pl, co)

    def random_place(self):
        """ Рандомная расстановка кораблей"""
        lens = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        board = Board(size=self.size)
        attempts = 0
        for length in lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), length, randint(0, 1))
                try:
                    board.add_ship(ship)
                    break
                except BoardWrongShipException:
                    pass
        board.begin()
        return board

    def random_board(self):
        """ Гарантированный метод вывода игрового поля. """
        board = None
        while board is None:
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
            res = pyautogui.confirm(text=f'* Два противника, Вы и {Name.user_2}\n'
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
        print(self.us.board)
        print("-" * 43)
        print()
        print(f"Акватория - {Name.user_2}")
        print(self.ai.board)
        print("-" * 43)

    def loop(self):
        """ Бесконечный игровой цикл, продолжается до победы. Определяет чей ход и кто одержал победу. """
        num = 0
        while True:
            self.print_boards()
            if num % 2 == 0:
                print(f'Стреляет {Name.user_1}!')
                repeat = self.us.move()
            else:
                print(f'Стреляет {Name.user_2}!')
                repeat = self.ai.move()
            if repeat:
                num -= 1

            if self.ai.board.defeat():
                self.print_boards()
                print('-' * 43)
                print(f'Выиграл {Name.user_1}!')
                break

            if self.us.board.defeat():
                self.print_boards()
                print('-' * 43)
                print(f'Выиграл {Name.user_2}!')
                break
            num += 1

    def start(self):
        self.greet()
        self.acquaintance()
        self.loop()


g = Game()
g.start()
