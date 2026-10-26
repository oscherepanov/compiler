from lexer import Lexer
from parser import Parser
from symbol_table import SymbolTable


class SemanticAnalyzer:
    """
       Семантический анализатор.

       Задача — пройти по готовому AST и проверить :

         1. Объявлена ли переменная до её использования.
         2. Нет ли повторного объявления.
         3. Совместимы ли типы в присваивании/инициализации.
         4. Совместимы ли типы в выражениях.
         5. Условие if/while — типа bool.
         6. Вызов функции.

       Побочный результат — заполненная таблица
       символов.
    """

    # Типы, над которыми допустимы арифметические операции (+ - * /).
    NUMERIC = {'integer', 'real'}

    # Создаем пустую таблицу символов
    def __init__(self):
        self.symbol_table = SymbolTable()

    # Обход операторов
    def check_stmt(self, node):
        kind = node[0]

        if kind == 'decl':
            # Нашли декларацию переменных
            _, typ, name, value = node
            self.symbol_table.add(name, typ) # Добавляем переменную в таблицу символов
            if value is not None:
                # Ага, ей присваивается значение
                init_t = self.check_expr(value) # Проверяем на совместимость типов
                if not self.assignable(typ, init_t):
                    raise ValueError(f"Нельзя инициализировать {typ} '{name}' значением типа {init_t}")

        elif kind == 'assign':
            # Присваение значения переменной
            _, name, expr = node
            sym = self.symbol_table.lookup(name)
            if sym is None: # Проверка на существование переменной в таблице символов
                raise ValueError(f"Присваивание необъявленной переменной '{name}'")
            expr_t = self.check_expr(expr) # Проверка на совпадение типов переменной и значения
            if not self.assignable(sym.type, expr_t):
                raise ValueError(f"Нельзя присвоить {expr_t} переменной '{name}' типа {sym.type}")

        elif kind == 'if':
            # Нашли условный оператор
            _, cond, then_body, else_body = node
            cond_t = self.check_expr(cond) # Проверили тип условия - bool ли
            if cond_t != 'bool':
                raise ValueError(f"Условие if должно быть bool, получено {cond_t}")
            for st in then_body:
                # Рекурсивно проверяем основное тело if
                self.check_stmt(st)
            for st in else_body:
                # Рекурсивно проверяем тело else
                self.check_stmt(st)

        elif kind == 'while':
            # Нашли цикл
            _, cond, body = node
            cond_t = self.check_expr(cond) # Проверяем тип условия
            if cond_t != 'bool':
                raise ValueError(f"Условие if должно быть bool, получено {cond_t}")
            for st in body:
                # Рекурсивно проверяем тело цикла
                self.check_stmt(st)

        elif kind == 'fun':
            self.check_expr(node[1]) # Нашли вызов функции, проверим ее

        else:
            raise ValueError(f"Неизвестный statement: {kind}")

    # check_expr возвращает тип выражения:
    def check_expr(self, node):
        kind = node[0]

        if kind == 'num':
            v = node[1]
            # Тип определяется по Python-типу значения: int -> integer,
            # float -> real. Лексер уже привёл "3" к int, "3.14" к float.
            return 'real' if isinstance(v, float) else 'integer' # Проверка значение на число

        #  строковый литерал
        if kind == 'str':
            return 'string'

        #  булев литерал
        if kind == 'bool':
            return 'bool'

        #  ссылка на переменную
        if kind == 'id':
            name = node[1]
            sym = self.symbol_table.lookup(name) # использование переменной до ее объявления
            if sym is None:
                raise ValueError(f"Использование необъявленной переменной '{name}'")
            return sym.type

        # унарный минус
        if kind == 'neg':
            t = self.check_expr(node[1])
            if t not in self.NUMERIC:
                # Если не число, ругаемся
                raise ValueError(f"Унарный минус применим только к числам, получено {t}")
            return t

        # бинарные операции
        if kind == 'binop':
            _, op, lhs, rhs = node
            lt = self.check_expr(lhs)
            rt = self.check_expr(rhs)

            # Разрешена арифметика только над числами
            # integer + integer -> integer
            # integer + real    -> real (расширение)
            # real    + real    -> real
            # Правило: если хоть один операнд real, результат real.
            if op in ('+', '-', '*', '/'):
                if lt not in self.NUMERIC or rt not in self.NUMERIC:
                    raise ValueError(f"Операция '{op}' требует чисел, получено {lt} и {rt}")
                return 'real' if 'real' in (lt, rt) else 'integer'

            # Сравнивать можно:
            #   - одинаковые типы (integer==integer, string==string);
            #   - числа между собой (integer==real, real<integer).
            # Нельзя: string==integer, bool<integer и т.п.
            if op in ('==', '!=', '>', '<', '>=', '<='):
                if lt != rt and not (lt in self.NUMERIC and rt in self.NUMERIC):
                    raise ValueError(f"Сравнение '{op}' между {lt} и {rt} некорректно")
                # Результат любого сравнения — bool.
                return 'bool'

            raise ValueError(f"Неизвестный binop: {op}")

        # логические операции
        if kind in ('and', 'or'):
            lt = self.check_expr(node[1])
            rt = self.check_expr(node[2])
            # Проверяем слева и справа - bool
            if lt != 'bool' or rt != 'bool':
                raise ValueError(f"'{kind}' требует bool с обеих сторон, получено {lt} и {rt}")
            return 'bool'

        # Проверяем вызов функции
        if kind == 'call':
            return self.check_call(node[1], node[2])

        raise ValueError(f"Неизвестное выражение: {kind}")

    # проверка вызова функции
    def check_call(self, name, args):
        # Если не print, то ругаемся
        if name != 'print':
            raise ValueError(f"Неизвестная функция {name}")
        for a in args:
            # проверяем аргументы
            self.check_expr(a)
        return 'void'

    """
           Можно ли значение типа source положить в переменную типа target.

           Разрешено:
             - точное совпадение: integer <- integer, string <- string;
             - расширение:         real    <- integer (5 -> 5.0).

           Запрещено:
             - сужение:            integer <- real    (потеря точности);
             - несовпадение:       string  <- integer и наоборот;
             - что-либо <- void    (void нельзя присвоить).
    """
    @staticmethod
    def assignable(target, source):
        if target == source:
            return True
        if target == 'real' and source == 'integer':
            return True
        return False

    # Запуск анализатора и возвращение таблицу символов
    def analyze(self, ast):
        tag, _, statements = ast
        if tag != 'program':
            raise ValueError("Программа должна начинаться с program")
        for st in statements:
            self.check_stmt(st)
        return self.symbol_table

if __name__ == '__main__':

    lx = Lexer()
    parser = Parser(lx)

    try:
        src = open('example.f').read()

        ast = parser.parse(src)

        semantic_analyzer = SemanticAnalyzer()
        table = semantic_analyzer.analyze(ast)
        table.show()

    except Exception as e:
        print(e)

