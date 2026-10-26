from lexer import Lexer
from parser import Parser
from semantic_anylizer import SemanticAnalyzer
from symbol_table import SymbolTable

"""
    Одна команда трехадресного кода в виде четвёрки.

    Формат: (op, arg1, arg2, result).

      op     — операция
      arg1   — первый операнд
      arg2   — второй операнд
      result — куда положить результат
"""
class Quad:
    def __init__(self, op, arg1=None, arg2=None, result=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __repr__(self):
        return f"({self.op!r}, {self.arg1!r}, {self.arg2!r}, {self.result!r})"

# Генератор трехадресного кода из AST.
class TACGenerator:
    def __init__(self):
        self.symtab = None # Таблица символов
        self.code: list[Quad] = [] # Храним трехадресный код
        self.tmp_count = 0 # Счетчик временных переменных
        self.label_count = 0 # Счетчик меток

    # Добавить команду в конец списка.
    def emit(self, op, arg1=None, arg2=None, result=None):
        self.code.append(Quad(op, arg1, arg2, result))

    # Сгенерировать новое имя временной переменной
    def new_tmp(self):
        self.tmp_count += 1
        return f"t{self.tmp_count}"

    # Сгенерировать новую метку
    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    # Генерация ТАК для всей программы. В конце
    def generate(self, ast, symbol_table: SymbolTable):
        self.symtab = symbol_table
        _, name, statements = ast
        # Плоский обход верхнего уровня. Каждый оператор генерирует свой участок ТАК через gen_stmt.
        for st in statements:
            self.gen_stmt(st)
        return self.code

    # Генерация операторов
    def gen_stmt(self, node):
        kind = node[0]

        if kind == 'decl':
            #  Объявление без инициализации не порождает команд.
            _, typ, name, init = node
            if init is not None:
                val = self.gen_expr(init) # Генерируем код для значение. Может же быть сложным.
                # Копируем значение инициализатора в переменную.
                # val — либо константа, либо имя # темпа, либо имя другой переменной.
                self.emit('=', val, None, name)

        elif kind == 'assign':
            # Присваение переменной значения
            _, name, expr = node
            val = self.gen_expr(expr)  # Генерируем код для значение. Может же быть сложным.
                # Копируем значение инициализатора в переменную.
                # val — либо константа, либо имя темпа, либо имя другой переменной.
            self.emit('=', val, None, name)

        elif kind == 'if':
            _, cond, then_body, else_body = node

            # Схема разворота if/else в ТАК:
            #
            #   ifFalse cond goto L_else
            #   <then_body>
            #   goto L_end
            # L_else:
            #   <else_body>
            # L_end:
            #
            # Даже если else_body пуст, метка L_else нужна: на неё
            # прыгает ifFalse при ложном условии.

            l_else = self.new_label() # Создаем метку на else
            l_end  = self.new_label() # Создаем метку на end
            self.gen_cond_jump(cond, false_label=l_else)  # Условный переход: прыгаем в L_else, если cond ложно.

            # Генерируем код для тела if
            for st in then_body:
                self.gen_stmt(st)

            # Генерируем прыжок на end
            self.emit('goto', None, None, l_end)

            # Добавляем метку к коду
            self.emit('label', None, None, l_else)

            # Генерируем код для тела else
            for st in else_body:
                self.gen_stmt(st)

            # Добавляем метку к коду после if
            self.emit('label', None, None, l_end)

        elif kind == 'while':
            # Схема разворота while в ТАК:
            #
            # L_start:
            #   ifFalse cond goto L_end
            #   <body>
            #   goto L_start
            # L_end:
            #
            # Условие проверяется ДО тела — стандартная семантика
            # while (в отличие от do-while).

            _, cond, body = node
            l_start = self.new_label() # Создаем метку для L_start
            l_end   = self.new_label() # Создаем метку для L_end

            self.emit('label', None, None, l_start) # Генерируем метку
            self.gen_cond_jump(cond, false_label=l_end) # Генерируем прыжок за цикл, если условие ложно

            # Генерируем код для тела цикла
            for st in body:
                self.gen_stmt(st)

            self.emit('goto', None, None, l_start) # Генерируем прыжок в начала цсловия цикла
            self.emit('label', None, None, l_end) # Генерируем метку для конца цикла

        elif kind == 'call':
            _, name, args = node
            # Аргументы кладутся в стек параметров командами param.
            for a in args:
                self.emit('param', self.gen_expr(a), None, None)
            # Генерируем команду вызова фунцкии
            self.emit('call', name, len(args), None)

        elif kind == 'fun':
            # Ничего не генерируем нового, только вызов функции
            self.gen_expr(node[1])

        else:
            raise ValueError(f"Неизвестный statement: {kind}")

    # Генерация выражений
    # gen_expr возвращает имя результата:
    #    - для константы — само значение;
    #    - для переменной — её имя;
    #    - для операции — имя последнего темпа.
    def gen_expr(self, node):
        kind = node[0]

        # Возвращаем значение как есть — в Quad'ах константы
        # хранятся прямо в arg1/arg2/result.
        if kind in ('num', 'str', 'bool'):
            return node[1]

        # Возвращаем имя: в ТАК переменная адресуется по имени.
        if kind == 'id':
            return node[1]

        # бинарная операция
        if kind == 'binop':
            _, op, lhs, rhs = node

            # Дети вычисляются первыми — их значения нужны как
            # операнды текущей операции. Порядок обхода = порядок
            # вычисления в исходнике (слева направо).

            a = self.gen_expr(lhs) # Генерируем команды для левого операнда
            b = self.gen_expr(rhs) # Генерируем команды для правого операнда
            t = self.new_tmp() # Создаем новую временную переменную
            self.emit(op, a, b, t) # Генерируем команду для данной операции
            return t

        if kind == 'neg':
            a = self.gen_expr(node[1]) # Генерируем код для операнда
            t = self.new_tmp() # Создаем новую временную переменную
            self.emit('uminus', a, None, t)  # Генерируем команду для унарного минуса
            return t

        if kind in ('and', 'or'):
            a = self.gen_expr(node[1]) # Генерируем команды для левого операнда
            b = self.gen_expr(node[2]) # Генерируем команды для правого операнда
            t = self.new_tmp() # Создаем новую временную переменную
            self.emit(kind, a, b, t) # Генерируем команду для данной операции
            return t

        if kind == 'call':
            _, name, args = node
            for a in args:
                self.emit('param', self.gen_expr(a), None, None)
            # Результат call нужен — кладём в темп.
            t = self.new_tmp()
            self.emit('call', name, len(args), t)
            return t

        raise ValueError(f"Неизвестное выражение: {kind}")

    # Генерация условного перехода
    def gen_cond_jump(self, cond, false_label):
        if cond[0] == 'binop' and cond[1] in ('==', '!=', '>', '<', '>=', '<='):
            _, op, lhs, rhs = cond
            a = self.gen_expr(lhs) # Генерируем код для левого операнда
            b = self.gen_expr(rhs) # Генерируем код для правого операнда

            # Инверсия операция если условие ложное, то противоположное сравнение — истинное
            inv = {'==': '!=', '!=': '==', '>': '<=',
                   '<': '>=', '>=': '<', '<=': '>'}
            self.emit('ifTrue', (inv[op], a, b), None, false_label) # Добавляем ТАК
        else:
            v = self.gen_expr(cond) # Генерируем код выражения
            self.emit('ifFalse', v, None, false_label) # Добавляем ТАК

# Человекочитаемый ТАК
def format_quad(q, idx=None):
    prefix = f"{idx:3}: " if idx is not None else ""
    op, a1, a2, r = q.op, q.arg1, q.arg2, q.result

    if op == 'label':
        return f"{prefix}{r}:"
    if op == 'goto':
        return f"{prefix}goto {r}"
    if op == 'ifFalse':
        return f"{prefix}ifFalse {a1} goto {r}"
    if op == 'ifTrue':
        if isinstance(a1, tuple):
            rel, x, y = a1
            return f"{prefix}if {x} {rel} {y} goto {r}"
        return f"{prefix}ifTrue {a1} goto {r}"
    if op == 'param':
        return f"{prefix}param {a1}"
    if op == 'call':
        call = f"call {a1}, {a2}"
        return f"{prefix}{r} = {call}" if r else f"{prefix}{call}"
    if op == 'return':
        return f"{prefix}return"
    if op == '=':
        return f"{prefix}{r} = {a1}"
    if op == 'uminus':
        return f"{prefix}{r} = -{a1}"
    return f"{prefix}{r} = {a1} {op} {a2}"

# Преобразуем весь код в читабельный формат
def print_tac(code):
    for i, q in enumerate(code):
        print(format_quad(q, i))

if __name__ == '__main__':

    lx = Lexer()
    parser = Parser(lx)

    try:

        src = open('example.f').read()

        ast = parser.parse(src)

        semantic_analyzer = SemanticAnalyzer()
        table = semantic_analyzer.analyze(ast)
        table.show()

        tac_generator = TACGenerator()
        code = tac_generator.generate(ast, table)

        print_tac(code)
    except Exception as e:
        print(e)