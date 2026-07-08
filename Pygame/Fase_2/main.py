"""
Ponto de entrada único do jogo.

Fluxo:
  1. Roda o menu (menu/jogo.py) — telas de menu, opções e o mapa de fases.
  2. O jogador clica em "JOGAR" e é levado ao mapa de fases; ao escolher a
     Fase 2 ali, o próprio menu já chama fases/fase2/fase2.py (run_fase2)
     para tocar a fase. Este arquivo não mexe em menu/jogo.py nem em
     fase2.py — só reúne os dois pontos de entrada num único lugar na raiz
     do projeto.

Fase 9 (ainda não criada):
  Quando fases/fase9/fase9.py existir, ela deve ser importada aqui do mesmo
  jeito que a Fase 2 (import fases.fase9.fase9.run as run_fase9) e conectada
  dentro de menu/jogo.py, em Game.do_action, no tratamento da ação
  "start_phase_8" — seguindo exatamente o mesmo padrão já usado para a
  Fase 2 (start_phase_1).
"""

from menu.jogo import Game

# Importado aqui explicitamente para deixar visível, neste ponto de entrada,
# a ligação entre o menu e a Fase 2 — o menu já usa essa mesma função
# internamente quando o jogador chega na Fase 2 pelo mapa.
from fases.fase2.fase2 import run as run_fase2  # noqa: F401


if __name__ == "__main__":
    Game().run()
