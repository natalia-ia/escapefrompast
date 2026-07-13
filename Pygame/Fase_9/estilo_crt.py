"""
=====================================================================
estilo_crt.py -- paleta e efeitos visuais COMPARTILHADOS entre
puzzle_terminal.py e npc_chatbot.py, pra unificar a estética dos dois
num visual de monitor CRT âmbar monocromático (anos 70/80): mesma cor,
mesma fonte monoespaçada (já era "consolas" nos dois arquivos, não
precisou mudar), bordas retas/quadradas e um efeito sutil de scanlines
por cima da tela.

Pra trocar a cor de tudo de uma vez (ex: pra um verde-fósforo em vez
de âmbar), troque só as constantes COR_* aqui embaixo -- o resto do
código de puzzle_terminal.py e npc_chatbot.py só usa os NOMES, nunca
valores de cor soltos.
=====================================================================
"""

import pygame

# ---------------------------------------------------------------------------
# PALETA -- monitor CRT âmbar
# ---------------------------------------------------------------------------
COR_FUNDO_CRT = (8, 6, 4)            # preto quase puro (leve tom quente) -- fundo da tela/caixas
COR_AMBAR = (255, 176, 0)            # âmbar principal -- texto/bordas normais
COR_AMBAR_DIM = (120, 82, 10)        # âmbar apagado -- bordas/textos secundários (estado inativo)
COR_AMBAR_BRILHO = (255, 224, 140)   # âmbar quase branco -- destaque (selecionado, texto importante, glow)
# Avisos críticos (cronômetro acabando, erro de conexão): mais alaranjado/
# intenso que o âmbar comum, pra continuar "lendo" como alerta sem virar um
# vermelho puro que destoaria da paleta monocromática.
COR_AMBAR_ALERTA = (255, 90, 0)

# Fundos de botão/campo (bem escuros, com leve tinta âmbar) -- o brilho de
# verdade fica por conta da borda/texto, não do fundo.
COR_FUNDO_BOTAO = (18, 14, 8)
COR_FUNDO_BOTAO_HOVER = (38, 28, 10)
COR_FUNDO_SELECIONADO = (55, 40, 10)


def render_texto_glow(fonte, texto, cor=COR_AMBAR, cor_glow=COR_AMBAR_DIM, glow=True):
    """Renderiza `texto` com um leve halo ao redor (glow), imitando o
    brilho de fósforo de um monitor CRT antigo: desenha a mesma palavra
    levemente deslocada em volta (numa cor mais fraca e translúcida)
    antes do texto nítido por cima -- tudo numa única superfície, pra
    quem chama só precisar dar um `blit` só. `glow=False` devolve o
    render normal (sem halo), pra textos pequenos onde o halo atrapalha
    mais do que ajuda (ex: rótulos de botão)."""
    base = fonte.render(texto, True, cor)
    if not glow:
        return base

    largura, altura = base.get_size()
    superficie = pygame.Surface((largura + 4, altura + 4), pygame.SRCALPHA)
    glow_surf = fonte.render(texto, True, cor_glow)
    glow_surf.set_alpha(120)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        superficie.blit(glow_surf, (2 + dx, 2 + dy))
    superficie.blit(base, (2, 2))
    return superficie


# Cache das superfícies de scanline por (tamanho, espaçamento, alpha) --
# são só linhas retas, não mudam frame a frame, então monta uma vez por
# combinação e reaproveita (redesenhar linha por linha todo frame seria
# desperdício).
_cache_scanlines = {}


def desenhar_scanlines(tela, rect=None, espacamento=3, alpha=40):
    """Desenha por cima de `tela` (ou só de `rect`, se informado) um
    padrão sutil de linhas horizontais semitransparentes, imitando as
    scanlines de um monitor CRT. `alpha` baixo de propósito -- é pra dar
    a textura, não atrapalhar a leitura do texto por baixo."""
    if rect is None:
        tamanho = tela.get_size()
        posicao = (0, 0)
    else:
        tamanho = (rect.width, rect.height)
        posicao = rect.topleft

    chave = (tamanho, espacamento, alpha)
    if chave not in _cache_scanlines:
        largura, altura = tamanho
        superficie = pygame.Surface(tamanho, pygame.SRCALPHA)
        for y in range(0, altura, espacamento):
            pygame.draw.line(superficie, (0, 0, 0, alpha), (0, y), (largura, y))
        _cache_scanlines[chave] = superficie

    tela.blit(_cache_scanlines[chave], posicao)
