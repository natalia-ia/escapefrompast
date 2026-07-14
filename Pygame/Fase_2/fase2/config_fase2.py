"""
=====================================================================
config_fase2.py -- botão de engrenagem (canto superior direito) +
painel de configurações, no mesmo espírito de config_fase9.py
(Pygame/Fase_9/config_fase9.py), só adaptado ao estilo visual
vitoriano/steampunk (dourado sobre marrom) e à arquitetura de tela
VIRTUAL vs janela REAL que a Fase 2 já usa em todo o resto do código.

COMPARTILHADO entre fase2.py (oficina + sala da máquina do tempo) e
puzzles/babbage_lovelace.py (o puzzle roda seu PRÓPRIO loop, separado
do loop principal -- por isso o botão/painel precisam ser desenhados e
tratados dos dois lados, não só um; mesmo motivo pelo qual
audio_fase2.py também é compartilhado entre os dois arquivos).

Como cada lado chama abrir_painel_config():
    if config_fase2.engrenagem_rect(width).collidepoint(click_pos):
        resultado = config_fase2.abrir_painel_config(screen, clock, width, height)
        if resultado == "sair":
            ...encerra a fase inteira (ver fase2.run() e o tratamento
            de "sair" em puzzles/babbage_lovelace.run())...

O painel É um mini-loop bloqueante (mesmo padrão de
babbage_lovelace.run()): enquanto ele está rodando, nada do jogo por
trás é atualizado nem redesenhado (fica congelado, com um véu escuro
por cima) -- é assim que o jogo "pausa" (inclusive o cronômetro do
puzzle, que só decrementa dentro do loop de babbage_lovelace.run(),
que fica parado enquanto este painel roda).

IMPORTANTE -- tela virtual vs janela real: assim como o resto da Fase
2, todo o desenho aqui acontece na tela VIRTUAL (`tela`, do tamanho
`largura`x`altura` combinado no resto do código), não direto na janela
real (que pode ter outro tamanho) -- por isso este módulo também faz, a
cada frame do seu próprio loop, a mesma conversão de mouse e o mesmo
redimensionamento final que fase2.run()/babbage_lovelace.run() já
fazem (ver o bloco real_screen/scale_x/scaled em ambos).
=====================================================================
"""

import os

import pygame

from . import audio_fase2
from .puzzles import common

FPS = 60

# ---------------------------------------------------------------------------
# PALETA -- mesmas cores já usadas no resto da Fase 2 (fase2.GOLD/CREAM,
# puzzles/common.PANEL_COLOR/HOVER_BG etc.), copiadas aqui em vez de
# importadas (mesmo espírito autocontido de audio_fase2.py: este módulo
# não cria uma dependência nova entre fase2.py e puzzles/common.py) --
# tons quentes: dourado, creme, marrom escuro, remetendo à era das
# máquinas a vapor/Revolução Industrial, igual ao resto da Fase 2.
# ---------------------------------------------------------------------------
GOLD = (212, 168, 67)
GOLD_DIM = (140, 112, 55)
CREAM = (232, 212, 176)
WHITE = (225, 230, 235)
PANEL_COLOR = (43, 30, 20)
HOVER_BG = (66, 48, 30)

# Fonte serifada (remete a livros/placas da época vitoriana) só pro texto
# deste painel -- o resto da Fase 2 usa "consolas" (monoespaçada) em
# todo o resto da UI, mas o pedido aqui foi especificamente uma fonte
# "que remeta à época vitoriana (serifada se possível)" pro painel de
# config. "georgia" é uma serifada clássica quase sempre disponível no
# Windows; pygame.font.SysFont cai automaticamente numa fonte padrão do
# sistema se ela não existir, então nunca quebra.
FONTE_VITORIANA = "georgia"

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# ---------------------------------------------------------------------------
# ÍCONE DE ENGRENAGEM -- reaproveita o MESMO asset (gear_small.png) já
# usado pelas engrenagens colecionáveis da oficina (ver fase2.GEAR_SMALL),
# em vez de desenhar uma forma genérica -- assim o ícone de config é
# literalmente a mesma peça de bronze/cobre que já faz parte do mundo
# visual da fase (Babbage, Ada, engrenagens), não só uma cor parecida.
# Posição: canto superior direito, ACIMA do contador "Engrenagens: N/4"
# (que fica em y=margin+14=34, ver fase2.run()), pra nunca sobrepor a
# área clicável dele.
# ---------------------------------------------------------------------------
GEAR_TAMANHO = 26
GEAR_TAMANHO_HOVER = 30  # um pouco maior no hover -- mesmo efeito (GEAR_HOVER_SCALE) das engrenagens colecionáveis da oficina
GEAR_MARGEM_DIREITA = 26
GEAR_MARGEM_TOPO = 20
GEAR_RAIO_CLIQUE = GEAR_TAMANHO_HOVER // 2 + 4  # área clicável um pouco maior que o desenho, mais fácil de acertar

_gear_icon_normal = None
_gear_icon_hover = None


def _carregar_icone_engrenagem():
    """Carrega e escala gear_small.png (mesmo arquivo das engrenagens
    colecionáveis) uma única vez, em dois tamanhos (normal/hover) --
    mesmo padrão de fase2._load_assets() escalando GEAR_SMALL/
    GEAR_SMALL_HOVER, só que carregado sob demanda aqui (este módulo não
    tem uma função de "carregar tudo no início" própria)."""
    global _gear_icon_normal, _gear_icon_hover
    if _gear_icon_normal is not None:
        return
    raw = pygame.image.load(os.path.join(ASSETS_DIR, "gear_small.png")).convert_alpha()
    _gear_icon_normal = pygame.transform.smoothscale(raw, (GEAR_TAMANHO, GEAR_TAMANHO))
    _gear_icon_hover = pygame.transform.smoothscale(raw, (GEAR_TAMANHO_HOVER, GEAR_TAMANHO_HOVER))


def _centro_engrenagem(largura):
    return (largura - GEAR_MARGEM_DIREITA, GEAR_MARGEM_TOPO)


def engrenagem_rect(largura):
    """Retângulo clicável do ícone -- comparar com a posição do clique
    (já convertida pra coordenada VIRTUAL) via collidepoint()."""
    cx, cy = _centro_engrenagem(largura)
    return pygame.Rect(cx - GEAR_RAIO_CLIQUE, cy - GEAR_RAIO_CLIQUE,
                        GEAR_RAIO_CLIQUE * 2, GEAR_RAIO_CLIQUE * 2)


def desenhar_engrenagem(tela, largura, mouse_pos):
    """Desenha o ícone (a mesma engrenagem de bronze/cobre da oficina) no
    canto superior direito, um pouco maior quando o mouse está em cima
    -- chamada TODO FRAME, em toda tela jogável da fase (oficina,
    puzzle, sala da máquina do tempo), pra ficar sempre acessível.
    `mouse_pos` já deve estar em coordenada VIRTUAL (mesma conversão que
    o resto do código já faz)."""
    _carregar_icone_engrenagem()
    centro = _centro_engrenagem(largura)
    hover = engrenagem_rect(largura).collidepoint(mouse_pos)
    icone = _gear_icon_hover if hover else _gear_icon_normal
    tela.blit(icone, icone.get_rect(center=centro))


# ---------------------------------------------------------------------------
# PAINEL DE CONFIGURAÇÕES -- mini-loop modal (mesmo padrão de
# babbage_lovelace.run(): tem seu próprio laço de eventos/desenho e só
# devolve o controle pra quem chamou quando o jogador fecha ele).
#
# O fundo/moldura do painel reaproveita o MESMO recorte de molduras.png
# usado pelos painéis de cartão do puzzle (common.SMALL_PANEL: cantos
# ornamentados com parafusos/rebites, centro com textura de madeira
# escura) -- carregado aqui, à parte, em vez de depender de
# common.SMALL_PANEL já estar carregado (o painel de config pode abrir
# antes de qualquer tela do puzzle ter rodado uma vez, ex: clicando na
# engrenagem direto na oficina) -- mesmo espírito autocontido do resto
# deste módulo. common.nine_slice() (função pública, sem underscore) é
# reaproveitada de verdade, só a SURFACE de origem é uma cópia local.
# ---------------------------------------------------------------------------
PAINEL_LARGURA = 440
# Mais alto que uma caixa "lisa" precisaria -- a moldura ornamentada
# consome 45px de cada lado (topo/rodapé) só com decoração, então o
# painel precisa de espaço de sobra pra nenhum texto/botão cair em cima
# dela (ver as posições de menos_rect/mais_rect/voltar_rect/sair_rect
# mais abaixo, todas calculadas com essa margem em mente).
PAINEL_ALTURA = 420
_MOLDURA_RECORTE = pygame.Rect(100, 56, 233, 230)  # mesmas coordenadas de common.SMALL_PANEL
MOLDURA_BORDA = 45  # mesmo valor de common.SMALL_PANEL_BORDER (é o mesmo recorte)

_moldura_painel = None


def _carregar_moldura_painel():
    global _moldura_painel
    if _moldura_painel is not None:
        return
    raw = pygame.image.load(os.path.join(ASSETS_DIR, "molduras.png")).convert_alpha()
    _moldura_painel = raw.subsurface(_MOLDURA_RECORTE).copy()


def abrir_painel_config(tela, relogio, largura, altura):
    """Roda o painel de config até o jogador clicar VOLTAR/SAIR ou
    apertar ESC (mesmo efeito de VOLTAR). O jogo por trás fica
    CONGELADO (só um retrato do último quadro, com um véu escuro por
    cima) -- nenhum evento do jogo em si é processado enquanto este
    loop está rodando, então tudo pausa de verdade (inclusive o
    cronômetro do puzzle, que só conta dentro do loop de
    babbage_lovelace.run(), parado enquanto este roda).

    Devolve:
      "voltar" -- fecha o painel, quem chamou continua o jogo de onde
                  parou (nenhuma mudança de estado necessária).
      "sair"   -- o jogador escolheu sair da fase inteira. Já para toda
                  a música/efeitos aqui dentro (audio_fase2.parar_tudo(),
                  que já chama tanto pygame.mixer.music.stop() quanto
                  pygame.mixer.stop()) antes de devolver -- quem chamou
                  só precisa encerrar o próprio loop (ver fase2.run() e
                  o tratamento do retorno "sair" em
                  puzzles/babbage_lovelace.run()).
    """
    _carregar_moldura_painel()
    fundo_congelado = tela.copy()

    # Fonte serifada (vitoriana) só neste painel -- ver o comentário de
    # FONTE_VITORIANA lá em cima.
    fonte_titulo = pygame.font.SysFont(FONTE_VITORIANA, 30, bold=True)
    fonte_volume = pygame.font.SysFont(FONTE_VITORIANA, 21, bold=True)
    fonte_pm = pygame.font.SysFont(FONTE_VITORIANA, 22, bold=True)
    fonte_opcao = pygame.font.SysFont(FONTE_VITORIANA, 20, bold=True)

    painel_rect = pygame.Rect(0, 0, PAINEL_LARGURA, PAINEL_ALTURA)
    painel_rect.center = (largura // 2, altura // 2)

    # Posições verticais afastadas o suficiente do topo/rodapé pra nunca
    # cair em cima da moldura ornamentada (MOLDURA_BORDA=45px de cada
    # lado) -- ver o ajuste de PAINEL_ALTURA logo acima.
    menos_rect = pygame.Rect(0, 0, 44, 44)
    menos_rect.center = (painel_rect.centerx - 95, painel_rect.top + 172)
    mais_rect = pygame.Rect(0, 0, 44, 44)
    mais_rect.center = (painel_rect.centerx + 95, painel_rect.top + 172)

    voltar_rect = pygame.Rect(0, 0, 290, 48)
    voltar_rect.center = (painel_rect.centerx, painel_rect.top + 256)
    sair_rect = pygame.Rect(0, 0, 290, 48)
    sair_rect.center = (painel_rect.centerx, painel_rect.top + 318)

    resultado = "voltar"
    rodando = True
    while rodando:
        relogio.tick(FPS)

        # Mesma conversão real->virtual usada no resto da Fase 2 (ver
        # fase2.run()/babbage_lovelace.run()): a janela real pode ter um
        # tamanho diferente da tela virtual (largura x altura).
        real_screen = pygame.display.get_surface()
        real_w, real_h = real_screen.get_size()
        scale_x, scale_y = largura / real_w, altura / real_h
        raw_mouse = pygame.mouse.get_pos()
        mouse_pos = (raw_mouse[0] * scale_x, raw_mouse[1] * scale_y)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                rodando = False
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                click_pos = (evento.pos[0] * scale_x, evento.pos[1] * scale_y)
                if menos_rect.collidepoint(click_pos):
                    audio_fase2.definir_volume_geral(audio_fase2.fator_volume_geral - 0.1)
                elif mais_rect.collidepoint(click_pos):
                    audio_fase2.definir_volume_geral(audio_fase2.fator_volume_geral + 0.1)
                elif voltar_rect.collidepoint(click_pos):
                    rodando = False
                elif sair_rect.collidepoint(click_pos):
                    resultado = "sair"
                    rodando = False

        # --- fundo: quadro congelado do jogo + véu escuro semi-transparente ---
        tela.blit(fundo_congelado, (0, 0))
        veu = pygame.Surface((largura, altura), pygame.SRCALPHA)
        veu.fill((0, 0, 0, 190))
        tela.blit(veu, (0, 0))

        # --- painel: moldura ornamentada (madeira escura + cantos de
        # metal dourado com rebites), mesma peça usada nos painéis de
        # cartão do puzzle -- em vez de um retângulo liso.
        common.nine_slice(tela, _moldura_painel, painel_rect, MOLDURA_BORDA)

        titulo_surf = fonte_titulo.render("CONFIGURAÇÕES", True, GOLD)
        tela.blit(titulo_surf, titulo_surf.get_rect(midtop=(painel_rect.centerx, painel_rect.top + 70)))

        volume_pct = int(round(audio_fase2.fator_volume_geral * 100))
        volume_surf = fonte_volume.render(f"Volume: {volume_pct}%", True, CREAM)
        tela.blit(volume_surf, volume_surf.get_rect(midtop=(painel_rect.centerx, painel_rect.top + 112)))

        # Mesmo esquema de cores de puzzles/common.Button.draw (o botão
        # FECHAR/TENTAR NOVAMENTE do puzzle): borda GOLD_DIM parada,
        # GOLD no hover; fundo PANEL_COLOR parado, HOVER_BG no hover;
        # texto WHITE parado, GOLD no hover -- pros botões deste painel
        # ficarem visualmente idênticos aos botões que já existem no
        # resto da Fase 2, com bordas douradas estilo moldura vitoriana.
        for rect, texto in ((menos_rect, "-"), (mais_rect, "+")):
            hover = rect.collidepoint(mouse_pos)
            cor_borda = GOLD if hover else GOLD_DIM
            cor_fundo = HOVER_BG if hover else PANEL_COLOR
            cor_texto = GOLD if hover else WHITE
            pygame.draw.rect(tela, cor_fundo, rect, border_radius=6)
            pygame.draw.rect(tela, cor_borda, rect, width=2, border_radius=6)
            texto_surf = fonte_pm.render(texto, True, cor_texto)
            tela.blit(texto_surf, texto_surf.get_rect(center=rect.center))

        for rect, texto in ((voltar_rect, "VOLTAR"), (sair_rect, "SAIR PARA O MENU")):
            hover = rect.collidepoint(mouse_pos)
            cor_borda = GOLD if hover else GOLD_DIM
            cor_fundo = HOVER_BG if hover else PANEL_COLOR
            cor_texto = GOLD if hover else WHITE
            pygame.draw.rect(tela, cor_fundo, rect, border_radius=8)
            pygame.draw.rect(tela, cor_borda, rect, width=2, border_radius=8)
            texto_surf = fonte_opcao.render(texto, True, cor_texto)
            tela.blit(texto_surf, texto_surf.get_rect(center=rect.center))

        # Redimensiona a tela virtual pro tamanho real da janela só na
        # hora de mostrar -- mesmo passo final de fase2.run()/
        # babbage_lovelace.run().
        scaled = pygame.transform.smoothscale(tela, (real_w, real_h))
        real_screen.blit(scaled, (0, 0))
        pygame.display.flip()

    if resultado == "sair":
        audio_fase2.parar_tudo()

    return resultado
