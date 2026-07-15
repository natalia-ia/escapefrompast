# -*- coding: utf-8 -*-
class ItemColecionavel:
    def __init__(self, nome, descricao, imagem_caminho=None):
        self.nome = nome
        self.descricao = descricao
        self.imagem_caminho = imagem_caminho

    def __repr__(self):
        return f"ItemColecionavel({self.nome!r})"


class Inventario:
    def __init__(self):
        self.itens = []

    def adicionar(self, item):
        if self.possui(item.nome):
            return False
        self.itens.append(item)
        return True

    def possui(self, nome_item):
        return any(item.nome == nome_item for item in self.itens)

    def quantidade(self):
        return len(self.itens)
