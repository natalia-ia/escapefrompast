"""
Ponto de entrada único do jogo -- é este arquivo que você executa
(`python main.py`, de dentro de Pygame/) pra abrir o jogo inteiro:
menu principal, opções e o mapa de fases.

Antes deste arquivo existir, quem cumpria esse papel era
Fase_2/Fase_2.py (ele continua funcionando, por compatibilidade, mas
main.py passa a ser a forma oficial e recomendada de rodar o jogo,
já que fica na raiz de Pygame/ -- onde qualquer pessoa nova no
projeto esperaria encontrar o ponto de entrada).

Por que isso não é tão simples quanto parece
-----------------------------------------------
O menu (Pygame/menu/jogo.py) é compartilhado por todas as fases. Logo
no topo dele, tem uma linha:

    from fase2.fase2 import run as run_fase2

Isso só funciona se o pacote `fase2` (que mora dentro de
Pygame/Fase_2/fase2/, não direto em Pygame/) já estiver "visível" pro
Python nesse momento -- ou seja, Pygame/Fase_2/ precisa estar no
sys.path ANTES de importarmos menu.jogo. Por isso este arquivo faz as
duas inserções de path abaixo antes do `from menu.jogo import Game`.

(As demais fases -- Fase_3, Fase_4, Fase_5 etc. -- não têm esse
problema porque são importadas sob demanda, só na hora do clique, por
`_importar_ponto_de_entrada` dentro do próprio menu/jogo.py.)
"""

import os
import sys

_PYGAME_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PYGAME_ROOT not in sys.path:
    sys.path.insert(0, _PYGAME_ROOT)

# fase2/ (o pacote da Fase 2) mora dentro de Fase_2/, não direto em
# Pygame/ -- por isso essa pasta específica também precisa entrar no
# sys.path antes de importar menu.jogo (que já importa fase2.fase2 lá
# no topo do próprio arquivo dele).
_FASE2_DIR = os.path.join(_PYGAME_ROOT, "Fase_2")
if _FASE2_DIR not in sys.path:
    sys.path.insert(0, _FASE2_DIR)

from menu.jogo import Game


# Só roda o jogo se este arquivo for executado diretamente
# (`python main.py`), não quando for importado por outro arquivo --
# padrão usual do Python pra separar "código que só deve rodar quando
# este arquivo é o programa principal" de "código que pode ser
# reaproveitado" (ex: um teste automatizado que só quer importar Game
# sem abrir a janela).
if __name__ == "__main__":
    Game().run()
