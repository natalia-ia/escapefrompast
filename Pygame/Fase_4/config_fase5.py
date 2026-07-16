"""
=====================================================================
config_fase5.py -- botão de configurações (canto superior direito) +
painel de configurações, no mesmo espírito de config_fase2.py
(Pygame/Fase_2/fase2/config_fase2.py).

Duas diferenças de arquitetura em relação à Fase 2, por isso este
módulo não é uma cópia 1:1:
  1. fase_5.py usa uma janela FIXA (LARGURA x ALTURA, sem a conversão
     de tela virtual/real que a Fase 2 usa) -- então aqui não há
     scale_x/scale_y nem redimensionamento no fim do loop do painel.
  2. O ícone é um ASSET QUADRADO próprio da Fase 5 (não o gear.png
     redondo da Fase 2), carregado por fase_5.py com o mesmo
     `carregar_imagem()` (com placeholder automático) que o resto dos
     assets desta fase já usa -- por isso este módulo NÃO carrega
     nenhuma imagem sozinho: ele recebe as superfícies já prontas
     (ícone parado/hover) por parâmetro. Isso evita duplicar a lógica
     de placeholder aqui e evita um import circular com fase_5.py.

Como fase_5.py chama (dentro de executar(), no tratamento de clique):
    if config_fase5.icone_rect(LARGURA).collidepoint(evento.pos):
        resultado = config_fase5.abrir_painel_config(
            self.tela, self.relogio, self.img_config, self.img_config_hover,
        )
        if resultado == "sair":
            rodando = False

E a cada frame, em toda cena jogável (mesmo padrão de
desenhar_botao_inventario()):
    config_fase5.desenhar_icone(self.tela, self.img_config, self.img_config_hover)

O painel É um mini-loop bloqueante (mesmo padrão de
config_fase2.abrir_painel_config()): enquanto ele está rodando, nada do
jogo por trás é atualizado nem redesenhado (fica congelado, com um véu
escuro por cima) -- inclusive o cronômetro da fase, que só é
decrementado dentro do laço de executar(), parado enquanto este painel
roda.
=====================================================================
"""

import pygame

import audio_fase5

FPS = 60

# ---------------------------------------------------------------------------
# PALETA -- mesmas cores já usadas em fase_5.py, copiadas aqui (não
# importadas) pelo mesmo motivo de audio_fase2.py/config_fase2.py: este
# módulo não cria uma dependência nova com fase_5.py.
# ---------------------------------------------------------------------------
BRANCO      = (245, 245, 240)
PRETO       = (15, 15, 15)
CINZA_CLARO = (180, 180, 180)
VERDE       = (60, 170, 90)
VERMELHO    = (190, 60, 60)
AMARELO_SEPIA = (196, 164, 96)
AZUL_ACO    = (80, 120, 150)
PAINEL_COR  = (30, 35, 45)   # fundo do painel: azul-acinzentado escuro, combina com AZUL_ACO
HOVER_BG    = (48, 56, 70)

# ---------------------------------------------------------------------------
# ÍCONE DE CONFIGURAÇÃO -- canto superior direito, com a mesma margem
# usada pelo botão de inventário no canto oposto (ver fase_5.py,
# botao_inventario.bottomright = (LARGURA-20, ALTURA-20)).
# ---------------------------------------------------------------------------
ICONE_TAMANHO = 56
ICONE_MARGEM = 15


def icone_rect(largura):
    """Retângulo clicável do ícone -- comparar com evento.pos direto
    (não precisa converter escala: a janela da Fase 5 é fixa)."""
    rect = pygame.Rect(0, 0, ICONE_TAMANHO, ICONE_TAMANHO)
    rect.topright = (largura - ICONE_MARGEM, ICONE_MARGEM)
    return rect


def desenhar_icone(tela, icone_normal, icone_hover):
    """Desenha o ícone de configuração no canto superior direito --
    chamada TODO FRAME, em toda tela jogável da fase (mesmo padrão de
    fase_5.desenhar_botao_inventario()). `icone_normal`/`icone_hover`
    já vêm carregados e escalados por fase_5.py (via carregar_imagem)."""
    largura = tela.get_width()
    rect = icone_rect(largura)
    mouse_pos = pygame.mouse.get_pos()
    hover = rect.collidepoint(mouse_pos)

    if hover:
        pygame.draw.rect(tela, VERDE, rect, width=3, border_radius=10)
    else:
        pygame.draw.rect(tela, AMARELO_SEPIA, rect, width=2, border_radius=10)

    icone = icone_hover if hover else icone_normal
    tela.blit(icone, icone.get_rect(center=rect.center))


# ---------------------------------------------------------------------------
# PAINEL DE CONFIGURAÇÕES -- mini-loop modal (mesmo padrão de
# config_fase2.abrir_painel_config()): tem seu próprio laço de
# eventos/desenho e só devolve o controle pra quem chamou quando o
# jogador fecha o painel (ESC/VOLTAR) ou escolhe sair da fase.
# ---------------------------------------------------------------------------
PAINEL_LARGURA = 420
PAINEL_ALTURA = 320


def abrir_painel_config(tela, relogio, icone_normal, icone_hover):
    """Roda o painel de configurações até o jogador clicar VOLTAR/SAIR
    ou apertar ESC (mesmo efeito de VOLTAR). O jogo por trás fica
    CONGELADO (só um retrato do último quadro, com um véu escuro por
    cima) -- nenhum evento do jogo em si é processado enquanto este
    loop está rodando, então o cronômetro da fase também pausa de
    verdade (ele só é decrementado dentro do laço de executar()).

    Devolve:
      "voltar" -- fecha o painel, fase_5.py continua o jogo de onde
                  parou (nenhuma mudança de estado necessária).
      "sair"   -- o jogador escolheu sair da fase inteira. Já para a
                  música aqui dentro (audio_fase5.parar_tudo()) antes
                  de devolver -- quem chamou só precisa encerrar o
                  próprio loop (ver fase_5.executar()).
    """
    largura, altura = tela.get_size()
    fundo_congelado = tela.copy()

    fonte_titulo = pygame.font.SysFont("arial", 28, bold=True)
    fonte_volume = pygame.font.SysFont("arial", 22, bold=True)
    fonte_pm = pygame.font.SysFont("arial", 24, bold=True)
    fonte_opcao = pygame.font.SysFont("arial", 20, bold=True)

    painel_rect = pygame.Rect(0, 0, PAINEL_LARGURA, PAINEL_ALTURA)
    painel_rect.center = (largura // 2, altura // 2)

    menos_rect = pygame.Rect(0, 0, 44, 44)
    menos_rect.center = (painel_rect.centerx - 95, painel_rect.top + 130)
    mais_rect = pygame.Rect(0, 0, 44, 44)
    mais_rect.center = (painel_rect.centerx + 95, painel_rect.top + 130)

    voltar_rect = pygame.Rect(0, 0, 260, 48)
    voltar_rect.center = (painel_rect.centerx, painel_rect.top + 210)
    sair_rect = pygame.Rect(0, 0, 260, 48)
    sair_rect.center = (painel_rect.centerx, painel_rect.top + 270)

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
                    audio_fase5.definir_volume_geral(audio_fase5.fator_volume_geral - 0.1)
                elif mais_rect.collidepoint(evento.pos):
                    audio_fase5.definir_volume_geral(audio_fase5.fator_volume_geral + 0.1)
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
        pygame.draw.rect(tela, PAINEL_COR, painel_rect, border_radius=14)
        pygame.draw.rect(tela, AMARELO_SEPIA, painel_rect, width=3, border_radius=14)

        titulo_surf = fonte_titulo.render("CONFIGURAÇÕES", True, AMARELO_SEPIA)
        tela.blit(titulo_surf, titulo_surf.get_rect(midtop=(painel_rect.centerx, painel_rect.top + 30)))

        volume_pct = int(round(audio_fase5.fator_volume_geral * 100))
        volume_surf = fonte_volume.render(f"Volume da música: {volume_pct}%", True, BRANCO)
        tela.blit(volume_surf, volume_surf.get_rect(midtop=(painel_rect.centerx, painel_rect.top + 80)))

        for rect, texto in ((menos_rect, "-"), (mais_rect, "+")):
            hover = rect.collidepoint(mouse_pos)
            cor_borda = VERDE if hover else AMARELO_SEPIA
            cor_fundo = HOVER_BG if hover else AZUL_ACO
            pygame.draw.rect(tela, cor_fundo, rect, border_radius=6)
            pygame.draw.rect(tela, cor_borda, rect, width=2, border_radius=6)
            texto_surf = fonte_pm.render(texto, True, BRANCO)
            tela.blit(texto_surf, texto_surf.get_rect(center=rect.center))

        for rect, texto in ((voltar_rect, "VOLTAR"), (sair_rect, "SAIR PARA O MENU")):
            hover = rect.collidepoint(mouse_pos)
            cor_borda = VERDE if hover else AMARELO_SEPIA
            cor_fundo = HOVER_BG if hover else AZUL_ACO
            cor_texto = VERDE if hover else BRANCO
            pygame.draw.rect(tela, cor_fundo, rect, border_radius=8)
            pygame.draw.rect(tela, cor_borda, rect, width=2, border_radius=8)
            texto_surf = fonte_opcao.render(texto, True, cor_texto)
            tela.blit(texto_surf, texto_surf.get_rect(center=rect.center))

        pygame.display.flip()

    if resultado == "sair":
        audio_fase5.parar_tudo()

    return resultado
