"""
Este arquivo é o ponto de entrada único do jogo -- é ele que você executa
(python Fase_2.py) pra abrir o jogo inteiro a partir do menu.

Fluxo:
  1. Roda o menu (Pygame/menu/jogo.py) — telas de menu, opções e o mapa de
     fases. O menu é compartilhado por todas as fases (fica um nível acima,
     em Pygame/menu/), então este arquivo garante que Pygame/ esteja no
     sys.path antes de importá-lo.
  2. O jogador clica em "JOGAR" e é levado ao mapa de fases; ao escolher a
     Fase 2 ali, o próprio menu já chama fase2/fase2.py (run_fase2)
     para tocar a fase. Este arquivo não mexe em menu/jogo.py nem em
     fase2.py — só reúne os dois pontos de entrada num único lugar na raiz
     desta pasta.

Fase 9 (ainda não criada):
  Quando fase9/fase9.py existir, ela deve ser importada aqui do mesmo
  jeito que a Fase 2 (import fase9.fase9.run as run_fase9) e conectada
  dentro de menu/jogo.py, em Game.do_action, no tratamento da ação
  "start_phase_8" — seguindo exatamente o mesmo padrão já usado para a
  Fase 2 (start_phase_1).
"""

import os
import sys

# menu/ mora em Pygame/menu/ (compartilhado por todas as fases), um nível
# acima desta pasta (Pygame/Fase_2/). Garante que Pygame/ esteja no sys.path
# antes de importar menu.jogo, independente de onde este script for chamado.
_PYGAME_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PYGAME_ROOT not in sys.path:
    sys.path.insert(0, _PYGAME_ROOT)

from menu.jogo import Game

# Importado aqui explicitamente para deixar visível, neste ponto de entrada,
# a ligação entre o menu e a Fase 2 — o menu já usa essa mesma função
# internamente quando o jogador chega na Fase 2 pelo mapa.
from fase2.fase2 import run as run_fase2  # noqa: F401


# Só roda o jogo se este arquivo for executado diretamente (python
# Fase_2.py), não quando for importado por outro arquivo -- é o padrão
# usual do Python pra separar "código que só deve rodar quando este
# arquivo é o programa principal" de "código que pode ser reaproveitado".
if __name__ == "__main__":
    Game().run()
