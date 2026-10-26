from dataclasses import dataclass


# Класс - таблица символов
class SymbolTable:

    # Строка в таблице - храним только переменные(название и тип)
    @dataclass
    class Item:
        name: str
        type: str

    # Инифицализируем таблицу пустым словарем
    def __init__(self):
        self.symbols: dict[str, SymbolTable.Item] = {}

    # Добавление в таблицу информации о переменной
    def add(self, name: str, typ: str):
        if name in self.symbols:
            raise ValueError(f"Повторное объявление переменной с именем {name}")
        self.symbols[name] = SymbolTable.Item(name, typ)

    # Найти переменную
    def lookup(self, name:str):
        return self.symbols.get(name, None)

    # Показать таблицу
    def show(self):
        for _, sym in self.symbols.items():
            print(f"  {sym}")