from pprint import pprint
import ply.yacc as yacc

from lexer import Lexer


# Класс - синтаксический анализатор. Строит абстрактное синтаксическое дерево.
class Parser:

    # Ссылка на Lexer.tokens гарантирует, что лексер и парсер работают с одним и тем же списком
    tokens = Lexer.tokens

    # Инициализация парсера с передачей лексера
    def __init__(self, lexer):
        self.lexer = lexer
        self.parser = yacc.yacc(
            module=self,
            debug=False,
            write_tables=False,
            errorlog=yacc.NullLogger(),   # не печатать warning'и о конфликтах
        )
        self.errors = []

    # Разобрает исходный текст и возвращает AST.
    def parse(self, src):
        self.errors = []
        return self.parser.parse(src, lexer=self.lexer.lexer)

    # Правило, которое порождает программы на фортране
    def p_program(self, p):
        '''program : PROGRAM ID statements ENDPROGRAM'''
        p[0] = ('program', p[2], p[3])

    # Порождает тело блока выражений, может быть пустым
    def p_statements(self, p):
        '''statements : statements statement
                      | empty'''
        if len(p) == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = []

    # Выражения для обявления переменных с присваением значения или без него
    def p_statement_declaration(self, p):
        '''statement : INTEGER ID SEMICOLON
                     | REAL    ID SEMICOLON
                     | STRING  ID SEMICOLON
                     | INTEGER ID ASSIGN expr SEMICOLON
                     | REAL    ID ASSIGN expr SEMICOLON
                     | STRING  ID ASSIGN expr SEMICOLON'''
        if len(p) == 4:
            p[0] = ('decl', p[1].lower(), p[2], None)
        else:
            p[0] = ('decl', p[1].lower(), p[2], p[4])

    # Выражение присваения значения переменной
    def p_statement_assign(self, p):
        '''statement : ID ASSIGN expr SEMICOLON'''
        p[0] = ('assign', p[1], p[3])

    # Условный оператор. Полная и краткая версия
    def p_statement_if(self, p):
        '''statement : IF LEFT_BR expr RIGHT_BR statements ENDIF
                     | IF LEFT_BR expr RIGHT_BR statements ELSE statements ENDIF'''
        if len(p) == 7:
            p[0] = ('if', p[3], p[5], [])
        else:
            p[0] = ('if', p[3], p[5], p[7])

    # Вызовы функции
    def p_statement_expr(self, p):
        '''statement : expr SEMICOLON'''
        p[0] = ('fun', p[1])

    # Цикл while
    def p_statement_while(self, p):
        '''statement : WHILE LEFT_BR expr RIGHT_BR statements ENDWHILE'''
        p[0] = ('while', p[3], p[5])

    # Логическое ИЛИ между двумя выражениями
    def p_expr_or(self, p):
        '''expr : expr OR and_expr'''
        p[0] = ('or', p[1], p[3])

    # Это правило нужно для разделения приоритетов И и ИЛИ
    def p_expr_and(self, p):
        '''expr : and_expr'''
        p[0] = p[1]

    # Логическое И между двумя выражениями
    def p_and_expr(self, p):
        '''and_expr : and_expr AND cmp_expr
                    | cmp_expr'''
        if len(p) == 4:
            p[0] = ('and', p[1], p[3])
        else:
            p[0] = p[1]

    # Операции сравнения
    def p_cmp_expr(self, p):
        '''cmp_expr : cmp_expr EQ     add_expr
                    | cmp_expr NOT_EQ add_expr
                    | cmp_expr GT     add_expr
                    | cmp_expr LT     add_expr
                    | cmp_expr GE     add_expr
                    | cmp_expr LE     add_expr
                    | add_expr'''
        if len(p) == 4:
            p[0] = ('binop', p[2], p[1], p[3])
        else:
            p[0] = p[1]

    # Операция сложения и вычитания
    def p_add_expr(self, p):
        '''add_expr : add_expr PLUS  mul_expr
                    | add_expr MINUS mul_expr
                    | mul_expr'''
        if len(p) == 4:
            p[0] = ('binop', p[2], p[1], p[3])
        else:
            p[0] = p[1]

    # Операция умножения и деления
    def p_mul_expr(self, p):
        '''mul_expr : mul_expr MULT unary
                    | mul_expr DIV  unary
                    | unary'''
        if len(p) == 4:
            p[0] = ('binop', p[2], p[1], p[3])
        else:
            p[0] = p[1]

    # Унарный минус
    def p_unary(self, p):
        '''unary : MINUS unary
                 | atom'''
        if len(p) == 3:
            p[0] = ('neg', p[2])
        else:
            p[0] = p[1]

    # Порождает атомарное выражения.
    def p_atom(self, p):
        '''atom : ID
                | ID LEFT_BR RIGHT_BR
                | ID LEFT_BR arg_list RIGHT_BR
                | INT_CONST
                | REAL_CONST
                | STRING_CONST
                | TRUE
                | FALSE
                | LEFT_BR expr RIGHT_BR'''
        t = p.slice[1].type
        if t == 'ID' and len(p) == 2:
            p[0] = ('id', p[1])
        elif t == 'ID' and len(p) == 4:
            p[0] = ('call', p[1], [])
        elif t == 'ID' and len(p) == 5:
            p[0] = ('call', p[1], p[3])
        elif t in ('INT_CONST', 'REAL_CONST'):
            p[0] = ('num', p[1])
        elif t == 'STRING_CONST':
            p[0] = ('str', p[1])
        elif t in ('TRUE', 'FALSE'):
            p[0] = ('bool', p[1].lower() == 'true')
        else:
            p[0] = p[2]

    # Список аргументов через запятую
    def p_arg_list(self, p):
        '''arg_list : arg_list COMMA expr
                    | expr'''
        if len(p) == 4:
            p[0] = p[1] + [p[3]]
        else:
            p[0] = [p[1]]

    # Пустое правило
    def p_empty(self, p):
        'empty :'
        p[0] = None

    # Обработчик ошибок
    def p_error(self, p):
        if p:
            msg = f"Syntax error at line {p.lineno}: unexpected token {p.type} ({p.value!r})"
        else:
            msg = "Syntax error at EOF"
        print(msg)
        self.errors.append(msg)


if __name__ == '__main__':
    src = open('example.f').read()

    lx = Lexer()
    ast = Parser(lx).parse(src)
    pprint(ast)