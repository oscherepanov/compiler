import ply.lex as lex

# Класс - лексический анализатор
class Lexer:

    # Зарезервированные слова языка
    reserved = ('PROGRAM', 'ENDPROGRAM', 'WHILE', 'ENDWHILE', 'IF', 'ELSE', 'ENDIF',
                'INTEGER', 'REAL', 'STRING', 'TRUE', 'FALSE', 'OR', 'AND')

    # Полный список токенов
    tokens = reserved + ('INT_CONST', 'REAL_CONST', 'STRING_CONST', 'PLUS', 'MULT', 'MINUS',
                         'DIV', 'ASSIGN', 'LEFT_BR', 'RIGHT_BR', 'SEMICOLON', 'COMMA',
                         'EQ', 'NOT_EQ', 'GT', 'LT', 'GE', 'LE', 'ID')

    # Символы, которые лексер молча пропускает, не порождая токенов
    t_ignore = ' \t\r'

    # Оператор равенства
    def t_EQ(self, t):
        r'=='
        return t

    # Оператор неравенства
    def t_NOT_EQ(self, t):
        r'!='
        return t

    # Оператор больше или равно
    def t_GE(self, t):
        r'>='
        return t

    # Оператор меньше или равно
    def t_LE(self, t):
        r'<='
        return t

    # Оператор присваения
    def t_ASSIGN(self, t):
        r'='
        return t

    # Оператор больше
    def t_GT(self, t):
        r'>'
        return t

    # Оператор меньше
    def t_LT(self, t):
        r'<'
        return t

    # Оператор сложения
    def t_PLUS(self, t):
        r'\+'
        return t

    # Оператор унарный или бинарный минус
    def t_MINUS(self, t):
        r'-'
        return t

    # Оператор умножения
    def t_MULT(self, t):
        r'\*'
        return t

    # Оператор деления
    def t_DIV(self, t):
        r'/'
        return t

    # Левая круглая скобка
    def t_LEFT_BR(self, t):
        r'\('
        return t

    # Правая круглая скобка
    def t_RIGHT_BR(self, t):
        r'\)'
        return t

    # Разделитель - точка с запятой
    def t_SEMICOLON(self, t):
        r';'
        return t

    # Разделитель - запятая
    def t_COMMA(self, t):
        r','
        return t

    # Разделитель - точка
    def t_DOT(self, t):
        r'\.'
        return t

    # Вещественная константа
    def t_REAL_CONST(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t

    # Целая константа
    def t_INT_CONST(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    # Строковая константа
    def t_STRING_CONST(self, t):
        r'\"([^\\\n]|(\\.))*?\"'
        t.value = t.value[1:-1]
        return t

    # Символ перевода строки для отслеживания номера строки в исходном файле
    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count('\n')

    # Если слово совпадает с зарезервированным (без учёта регистра),
    # оно получает тип соответствующего ключевого слова, иначе — ID
    def t_ID(self, t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        t.type = self.reversed_map.get(t.value.lower(), 'ID')
        return t

    # Фунцкия обработки ошибок
    def t_error(self, t):
        print(f"Illegal character {t.value[0]!r} at line {t.lexer.lineno}")
        t.lexer.skip(1)

    # Инициализация лексера
    def __init__(self):
        self.reversed_map = {r.lower(): r for r in self.reserved}
        self.lexer = lex.lex(object=self, reflags=int(__import__('re').VERBOSE))

    # Передать лексеру исходный текст.
    def input(self, data):
        self.lexer.input(data)

    # Вернуть следующий токен или None в конце ввода.
    def token(self):
        return self.lexer.token()

    # Получить итератор по токенам
    def __iter__(self):
        return iter(self.lexer)


if __name__ == '__main__':
    lx = Lexer()
    src = open('example.f').read()

    lx.input(src)
    for tok in lx:
        print(tok)