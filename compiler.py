from lexer import Lexer
from parser import Parser
from semantic_anylizer import SemanticAnalyzer
from tac_generator import TACGenerator, print_tac


class Compiler:
    def __init__(self):
        self.lexer = Lexer()
        self.parser = Parser(self.lexer)
        self.semantic_analyzer = SemanticAnalyzer()
        self.tac_generator = TACGenerator()

    def generate_code(self, code):
        ast = self.parser.parse(code)
        table = self.semantic_analyzer.analyze(ast)
        return self.tac_generator.generate(ast, table)

if __name__ == '__main__':
    compiler = Compiler()
    try:
        src = open('example.f').read()
        tac_code = compiler.generate_code(src)
        print_tac(tac_code)
    except Exception as e:
        print(e)