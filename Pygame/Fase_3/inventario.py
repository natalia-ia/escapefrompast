

class ItemColecionavel:
    """Representa um único item que o jogador pode coletar (ex: um
    bilhete, uma chave, uma peça de engrenagem)."""

    def __init__(self, nome, descricao, imagem_caminho=None):
        self.nome = nome
        self.descricao = descricao
        self.imagem_caminho = imagem_caminho

    def __repr__(self):
        return f"ItemColecionavel({self.nome!r})"


class Inventario:
    """Guarda a lista de itens que o jogador já coletou."""

    def __init__(self):
        self.itens = []

    def adicionar(self, item):
        """Adiciona um item, evitando duplicatas (compara pelo nome).
        Retorna True se adicionou, False se já existia."""
        if self.possui(item.nome):
            return False
        self.itens.append(item)
        return True

    def possui(self, nome_item):
        """Verifica se um item com esse nome já está no inventário."""
        return any(item.nome == nome_item for item in self.itens)

    def quantidade(self):
        """Retorna quantos itens distintos já foram coletados."""
        return len(self.itens)