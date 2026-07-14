"""
=====================================================================
config_fase9.py -- botão de engrenagem (canto superior direito) +
painel de configurações, COMPARTILHADO entre fase9.py (cena do quarto
e sala final) e puzzle_terminal.py (o puzzle roda seu PRÓPRIO loop,
separado do loop principal -- ver puzzle_terminal.run() -- por isso o
botão/painel precisam ser desenhados e tratados dos dois lados, não só
um; mesmo motivo pelo qual audio_fase9.py e estilo_crt.py também são
compartilhados entre os dois arquivos).

Como cada lado chama abrir_painel_config():
    if engrenagem_rect(largura).collidepoint(evento.pos):
        resultado = config_fase9.abrir_painel_config(tela, relogio, largura, altura)
        if resultado == "sair":
            ...encerra a fase inteira (ver fase9.Jogo.executar() e o
            tratamento de "sair" em puzzle_terminal.run())...

O painel É um mini-loop bloqueante (mesmo padrão de fase9._run_intro()
e puzzle_terminal.run()): enquanto ele está rodando, nada do jogo por
trás é atualizado nem redesenhado (fica congelado, com um véu escuro
por cima) -- é assim que o jogo "pausa" (inclusive o cronômetro do
puzzle, que só decrementa dentro do loop de puzzle_terminal.run(), que
fica parado enquanto este painel roda).
=====================================================================
"""

import math

import pygame

from estilo_crt import (
    COR_FUNDO_CRT,
    COR_AMBAR,
    COR_AMBAR_DIM,
    COR_AMBAR_BRILHO,
    COR_FUNDO_BOTAO,
    COR_FUNDO_BOTAO_HOVER,
    render_texto_glow,
    desenhar_scanlines,
)
import audio_fase9

FPS = 60

# ---------------------------------------------------------------------------
# ÍCONE DE ENGRENAGEM -- canto superior direito, longe do botão FECHAR/
# cronômetro do puzzle (que ficam em largura-165..largura-40, ver
# puzzle_terminal.run()) e do contador "Dicas restantes" (canto
# superior ESQUERDO, ver npc_chatbot.desenhar_contador_dicas).
# ---------------------------------------------------------------------------
GEAR_RAIO = 12
GEAR_MARGEM_DIREITA = 22
GEAR_MARGEM_TOPO = 26
GEAR_RAIO_CLIQUE = GEAR_RAIO + 6  # área clicável um pouco maior que o desenho, mais fácil de acertar


def _centro_engrenagem(largura):
    return (largura - GEAR_MARGEM_DIREITA, GEAR_MARGEM_TOPO)


def engrenagem_rect(largura):
    """Retângulo clicável do ícone -- comparar com evento.pos via
    collidepoint(), mesmo padrão dos outros botões desta fase."""
    cx, cy = _centro_engrenagem(largura)
    return pygame.Rect(cx - GEAR_RAIO_CLIQUE, cy - GEAR_RAIO_CLIQUE,
                        GEAR_RAIO_CLIQUE * 2, GEAR_RAIO_CLIQUE * 2)


def _pontos_engrenagem(centro, raio, raio_dente, n_dentes=8):
    cx, cy = centro
    pontos = []
    for i in range(n_dentes * 2):
        angulo = (i / (n_dentes * 2)) * 2 * math.pi
        r = raio_dente if i % 2 == 0 else raio
        pontos.append((cx + r * math.cos(angulo), cy + r * math.sin(angulo)))
    return pontos


def _construir_engrenagem_com_glow(raio, cor):
    """Monta a engrenagem (dentes + furo) numa superfície própria, com um
    leve halo de brilho ao redor -- mesma técnica de
    estilo_crt.render_texto_glow (a mesma silhueta desenhada várias vezes
    levemente deslocada, numa cor mais fraca e translúcida, por baixo da
    silhueta nítida), só aplicada numa forma desenhada em vez de texto,
    pra combinar com o resto da estética CRT âmbar da fase."""
    raio_dente = raio * 1.45
    margem = 8
    tam = int(raio_dente * 2 + margem * 2)
    centro_local = (tam // 2, tam // 2)

    superficie = pygame.Surface((tam, tam), pygame.SRCALPHA)

    # halo (glow): a silhueta em COR_AMBAR_DIM, translúcida, repetida em
    # várias direções ao redor do centro -- mesmo espírito do glow de
    # render_texto_glow.
    glow_surf = pygame.Surface((tam, tam), pygame.SRCALPHA)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        pontos_glow = _pontos_engrenagem((centro_local[0] + dx, centro_local[1] + dy), raio, raio_dente)
        pygame.draw.polygon(glow_surf, (*COR_AMBAR_DIM, 110), pontos_glow)
    superficie.blit(glow_surf, (0, 0))

    # silhueta nítida por cima do halo
    pygame.draw.polygon(superficie, cor, _pontos_engrenagem(centro_local, raio, raio_dente))
    pygame.draw.circle(superficie, COR_FUNDO_CRT, centro_local, max(1, int(raio * 0.55)))

    return superficie


def desenhar_engrenagem(tela, largura, mouse_pos):
    """Desenha o ícone (com glow âmbar) no canto superior direito, mais
    claro (COR_AMBAR_BRILHO) quando o mouse está em cima -- chamada TODO
    FRAME, em toda tela jogável da fase (quarto, puzzle, sala final),
    pra ficar sempre acessível."""
    centro = _centro_engrenagem(largura)
    hover = engrenagem_rect(largura).collidepoint(mouse_pos)
    cor = COR_AMBAR_BRILHO if hover else COR_AMBAR
    engrenagem_surf = _construir_engrenagem_com_glow(GEAR_RAIO, cor)
    tela.blit(engrenagem_surf, engrenagem_surf.get_rect(center=centro))


# ---------------------------------------------------------------------------
# PAINEL DE CONFIGURAÇÕES -- mini-loop modal (mesmo padrão de
# fase9._run_intro/puzzle_terminal.run(): tem seu próprio laço de
# eventos/desenho e só devolve o controle pra quem chamou quando o
# jogador fecha ele).
# ---------------------------------------------------------------------------
PAINEL_LARGURA = 420
PAINEL_ALTURA = 300


def abrir_painel_config(tela, relogio, largura, altura):
    """Roda o painel de config até o jogador clicar VOLTAR/SAIR ou
    apertar ESC (mesmo efeito de VOLTAR). O jogo por trás fica
    CONGELADO (só um retrato do último quadro, com um véu escuro por
    cima) -- nenhum evento do jogo em si é processado enquanto este
    loop está rodando, então tudo pausa de verdade (inclusive o
    cronômetro do puzzle, que só conta dentro do loop de
    puzzle_terminal.run(), parado enquanto este roda).

    Devolve:
      "voltar" -- fecha o painel, quem chamou continua o jogo de onde
                  parou (nenhuma mudança de estado necessária).
      "sair"   -- o jogador escolheu sair da fase inteira. Já para toda
                  a música/efeitos aqui dentro (audio_fase9.parar_tudo())
                  antes de devolver -- quem chamou só precisa encerrar o
                  próprio loop (ver fase9.Jogo.executar() e o
                  tratamento do retorno "sair" em puzzle_terminal.run()).
    """
    fundo_congelado = tela.copy()

    fonte_titulo = pygame.font.SysFont("consolas", 26, bold=True)
    fonte_volume = pygame.font.SysFont("consolas", 19, bold=True)
    fonte_pm = pygame.font.SysFont("consolas", 22, bold=True)
    fonte_opcao = pygame.font.SysFont("consolas", 19, bold=True)

    painel_rect = pygame.Rect(0, 0, PAINEL_LARGURA, PAINEL_ALTURA)
    painel_rect.center = (largura // 2, altura // 2)

    menos_rect = pygame.Rect(0, 0, 42, 42)
    menos_rect.center = (painel_rect.centerx - 90, painel_rect.top + 118)
    mais_rect = pygame.Rect(0, 0, 42, 42)
    mais_rect.center = (painel_rect.centerx + 90, painel_rect.top + 118)

    voltar_rect = pygame.Rect(0, 0, 280, 46)
    voltar_rect.center = (painel_rect.centerx, painel_rect.top + 196)
    sair_rect = pygame.Rect(0, 0, 280, 46)
    sair_rect.center = (painel_rect.centerx, painel_rect.top + 254)

    resultado = "voltar"
    rodando = True
    while rodando:
        relogio.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                rodando = False
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if menos_rect.collidepoint(evento.pos):
                    audio_fase9.definir_volume_geral(audio_fase9.fator_volume_geral - 0.1)
                elif mais_rect.collidepoint(evento.pos):
                    audio_fase9.definir_volume_geral(audio_fase9.fator_volume_geral + 0.1)
                elif voltar_rect.collidepoint(evento.pos):
                    rodando = False
                elif sair_rect.collidepoint(evento.pos):
                    resultado = "sair"
                    rodando = False

        # --- fundo: quadro congelado do jogo + véu escuro semi-transparente ---
        tela.blit(fundo_congelado, (0, 0))
        veu = pygame.Surface((largura, altura), pygame.SRCALPHA)
        veu.fill((0, 0, 0, 190))
        tela.blit(veu, (0, 0))

        # --- painel ---
        pygame.draw.rect(tela, COR_FUNDO_CRT, painel_rect)
        pygame.draw.rect(tela, COR_AMBAR, painel_rect, width=3)

        titulo_surf = render_texto_glow(fonte_titulo, "CONFIGURAÇÕES", COR_AMBAR)
        tela.blit(titulo_surf, titulo_surf.get_rect(midtop=(painel_rect.centerx, painel_rect.top + 22)))

        volume_pct = int(round(audio_fase9.fator_volume_geral * 100))
        volume_surf = fonte_volume.render(f"Volume: {volume_pct}%", True, COR_AMBAR)
        tela.blit(volume_surf, volume_surf.get_rect(midtop=(painel_rect.centerx, painel_rect.top + 78)))

        # Mesmo padrão de cores de puzzle_terminal._Botao.desenhar (sem
        # "selecionado", que não se aplica aqui): borda/texto em
        # COR_AMBAR_DIM parado, COR_AMBAR no hover -- só o fundo já
        # dava essa pista antes, agora a borda/texto também "acendem"
        # junto no hover, igual aos botões do puzzle.
        for rect, texto in ((menos_rect, "-"), (mais_rect, "+")):
            hover = rect.collidepoint(mouse_pos)
            cor_fundo = COR_FUNDO_BOTAO_HOVER if hover else COR_FUNDO_BOTAO
            cor_borda = COR_AMBAR if hover else COR_AMBAR_DIM
            cor_texto = COR_AMBAR if hover else COR_AMBAR_DIM
            pygame.draw.rect(tela, cor_fundo, rect)
            pygame.draw.rect(tela, cor_borda, rect, width=2)
            texto_surf = fonte_pm.render(texto, True, cor_texto)
            tela.blit(texto_surf, texto_surf.get_rect(center=rect.center))

        for rect, texto in ((voltar_rect, "VOLTAR"), (sair_rect, "SAIR PARA O MENU")):
            hover = rect.collidepoint(mouse_pos)
            cor_fundo = COR_FUNDO_BOTAO_HOVER if hover else COR_FUNDO_BOTAO
            cor_borda = COR_AMBAR if hover else COR_AMBAR_DIM
            cor_texto = COR_AMBAR if hover else COR_AMBAR_DIM
            pygame.draw.rect(tela, cor_fundo, rect)
            pygame.draw.rect(tela, cor_borda, rect, width=2)
            texto_surf = fonte_opcao.render(texto, True, cor_texto)
            tela.blit(texto_surf, texto_surf.get_rect(center=rect.center))

        desenhar_scanlines(tela, rect=painel_rect)
        pygame.display.flip()

    if resultado == "sair":
        audio_fase9.parar_tudo()

    return resultado
