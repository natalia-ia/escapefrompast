"""
=====================================================================
Fase_9: A REVOLUÇÃO DOS COMPUTADORES PESSOAIS (1975-1990)
=====================================================================

CONTEXTO DA FASE
-----------------
Estamos entre 1975 e 1990 -- a virada da linha de comando (terminais
de texto, tela preta com prompt) para a interface gráfica (o primeiro
desktop, com janelas, ícones e mouse). O jogador começa numa tela de
terminal preta (estilo microcomputador dos anos 70) e precisa
reconstruir o primeiro desktop gráfico; quando acerta, a tela "acende"
numa área de trabalho colorida e a fase termina.

ESTRUTURA DO JOGO (máquina de estados) -- SÓ O ESQUELETO POR ENQUANTO
----------------------------------------------------------------------
QUARTO    -> cena principal: o quarto retrô (assets/imagens/cenario_
             fase_9.png) onde o jogador anda com WASD/setas e pode
             clicar no computador em cima da escrivaninha para
             começar o puzzle. O jogador começa aqui.
TERMINAL  -> tela de terminal preto, com um cursor piscando
             (placeholder). Disparada (por enquanto só um print,
             # TODO) ao clicar no computador, dentro de QUARTO.
             # TODO: aqui entra o puzzle de "montar" o desktop --
             a mecânica em si (arrastar ícones? digitar comandos?
             organizar janelas?) ainda não foi definida.
DESKTOP   -> tela "acesa", área de trabalho colorida -- fim da fase.
             # TODO: transição visual entre TERMINAL e DESKTOP (um
             fade, por exemplo, parecido com fase2._fade_transition
             em Pygame/Fase_2/fase2/fase2.py) entra aqui, disparada no
             momento em que o puzzle for resolvido.

Este arquivo é só o ESQUELETO: abre a janela na mesma resolução das
outras fases, mostra a tela de terminal com o cursor piscando, e
marca com "# TODO" onde a lógica do puzzle e a transição pro desktop
vão entrar. SEM INVENTÁRIO -- esta fase não tem coleta de objetos no
cenário (diferente da Fase_4, que tem).

Requisitos: pip install pygame
Execução:   python fase9.py
=====================================================================
"""

import os
import sys

import pygame

from npc_chatbot import NPCChatbot

# No Windows, se o processo não avisar que é "DPI aware", o próprio
# Windows escala a janela sozinho (em telas com escala >100%, o padrão da
# maioria dos notebooks/monitores) -- o jogo continua desenhando em
# 960x600, mas os cliques do mouse chegam com coordenadas na escala
# "virtual" do Windows, que não bate mais 1-pra-1 com os retângulos
# calculados aqui (ex: COMPUTADOR_RECT), gerando cliques que "erram" um
# alvo que visualmente parece certo. Isso é o suspeito nº1 do bug "clicar
# no computador não faz nada" -- as outras fases não sofrem disso porque
# redesenham tudo numa tela virtual e recalculam a escala do mouse a cada
# frame (ver fase2._run_intro); esta fase ainda desenha direto na janela
# real, então a correção mais simples é pedir ao Windows pra não escalar
# a janela.
#
# Tenta a API mais nova/precisa primeiro (Per-Monitor V2 -- lida direito
# com múltiplos monitores com escalas diferentes, comum no Windows 11) e
# só cai pra APIs mais antigas se a atual não existir nessa versão do
# Windows. Se o processo já foi marcado DPI aware antes (ex: manifesto
# embutido no próprio python.exe), as chamadas seguintes simplesmente
# falham/no-op -- daí o try/except em cada uma, sem interromper o jogo.
if sys.platform == "win32":
    import ctypes

    _DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(
            _DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        )
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except (AttributeError, OSError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass

# =====================================================================
# 1. CONFIGURAÇÕES GERAIS DA JANELA E DO JOGO
# =====================================================================
LARGURA, ALTURA = 960, 600  # mesma resolução da janela usada nas outras fases
FPS = 60

PRETO = (15, 15, 15)
VERDE_TERMINAL = (60, 220, 100)  # texto/cursor estilo monitor de fósforo verde
BRANCO = (245, 245, 240)
AZUL_DESKTOP = (0, 90, 160)  # placeholder da área de trabalho "acesa"
GOLD = (212, 168, 67)   # títulos -- mesma cor da Fase 2 (fase2.GOLD)
CREAM = (232, 212, 176)  # instruções -- mesma cor da Fase 2 (fase2.CREAM)

# ---------------------------------------------------------------------------
# Tela inicial (intro) -- mesmo estilo/estrutura da Fase 2 (ver
# fase2._run_intro em Pygame/Fase_2/fase2/fase2.py): título/subtítulo no
# topo, personagem grande à esquerda, balão de fala à direita e um botão
# "Iniciar". Só muda o texto (texto provisório -- o combinado ajusta
# depois) e o fundo (aqui, o próprio cenário da fase, desfocado).
# ---------------------------------------------------------------------------
TITLE = "FASE 9"
SUBTITLE = "A REVOLUÇÃO DOS COMPUTADORES PESSOAIS  —  1975-1990"
INTRO_TEXT = (
    "A Cápsula do Tempo me trouxe para um quarto em algum ponto entre "
    "1975 e 1990 -- a era dos primeiros computadores pessoais. As telas "
    "pretas de comando estão dando lugar a algo novo: janelas, ícones, "
    "um mouse. Preciso entender essa passagem para religar a máquina e, "
    "quem sabe, voltar para casa."
)
INTRO_START_HINT = "Clique em Iniciar ou pressione ENTER"
INTRO_PORTRAIT_HEIGHT = 480  # bem maior que o sprite usado durante o jogo
INTRO_BUBBLE_BG = (232, 220, 196)  # bege claro, mesmo tom de fase2.INTRO_BUBBLE_BG
INTRO_BUBBLE_BORDER = (60, 45, 30)  # contorno escuro estilo quadrinho

# Intensidade do blur aplicado só no cenário de fundo da intro (o
# personagem, desenhado por cima depois, fica nítido) -- ver _aplicar_blur
# mais abaixo. INTRO_BLUR_PASSOS repete o processo pra deixar mais forte.
INTRO_BLUR_INTENSIDADE = 10
INTRO_BLUR_PASSOS = 2

# ---------------------------------------------------------------------------
# Cena do quarto (QUARTO) -- chão andável e área clicável do computador
# ---------------------------------------------------------------------------
# Medidos direto em cima de assets/imagens/cenario_fase_9.png (1536x1024,
# depois escalado pra LARGURA x ALTURA): FLOOR_RECT é a faixa de chão de
# madeira livre no meio do quarto (já exclui o baú no canto esquerdo e a
# cômoda no canto direito, que ficam por cima do chão); a escrivaninha, as
# estantes e o resto dos móveis da parede de fundo já ficam acima do topo
# desse retângulo, então não precisam de um bloqueio à parte (mesmo
# espírito do FLOOR_RECT/TABLE_RECT de fase2.py, só que aqui um retângulo
# já basta).
FLOOR_RECT = pygame.Rect(138, 328, 663, 264)

# Área invisível sobre o monitor + teclado da escrivaninha (mesa de madeira
# à esquerda da cena) -- NÃO é a TV/monitor da estante à direita. Clicar
# aqui dispara o início do puzzle (placeholder por enquanto).
COMPUTADOR_RECT = pygame.Rect(295, 120, 155, 95)

PLAYER_RADIUS = 22  # mesma margem de colisão usada em fase2.py


# =====================================================================
# 2. CAMINHOS DOS ASSETS -> PREENCHA AQUI COM SUAS IMAGENS
# =====================================================================
# Assets ficam em assets/imagens/ (artes) e assets/sons/ (efeitos sonoros
# e música), ao lado deste arquivo. Enquanto um arquivo não existir, as
# funções carregar_imagem/carregar_fonte abaixo devolvem None e quem
# desenha usa um placeholder (cor sólida), então dá pra testar a fase
# antes de ter os assets finais prontos -- mesmo espírito da Fase_4.
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))


def caminho_asset(nome_relativo):
    """Monta o caminho absoluto de um asset a partir da pasta deste
    arquivo .py (funciona não importa de onde o script é executado)."""
    return os.path.join(PASTA_DO_SCRIPT, nome_relativo)


ASSETS = {
    # TODO: preencher conforme os assets forem criados. Nenhum é
    # obrigatório ainda -- a tela de terminal é desenhada só com
    # texto (ver Jogo._desenhar_terminal mais abaixo).
    "fundo_desktop": caminho_asset("assets/imagens/fundo_desktop.png"),
    "sprite_npc": caminho_asset("assets/imagens/system_ai.png"),
    "fonte_terminal": caminho_asset("assets/imagens/fonte_terminal.ttf"),
    # TODO: som de "bipe" do terminal / efeito de "ligar" o monitor ao
    # entrar no desktop, por exemplo:
    # "som_beep": caminho_asset("assets/sons/beep.wav"),
}

# Cenário do quarto (fundo da cena QUARTO).
CENARIO_QUARTO_PATH = caminho_asset("assets/imagens/cenario_fase_9.png")

# Avatar do jogador -- mesmos 6 frames (3 por gênero) e mesma escala usados
# em Pygame/Fase_2/fase2/fase2.py (arquivos copiados de lá pra
# assets/imagens/ desta fase, já que é o mesmo personagem escolhido no
# jogo). "_m" = masculino, "_f" = feminino.
AVATAR_ASSETS = {
    "parado_m": caminho_asset("assets/imagens/personagem_parado.png"),
    "andando1_m": caminho_asset("assets/imagens/personagem_andando1.png"),
    "andando2_m": caminho_asset("assets/imagens/personagem_andando2.png"),
    "parado_f": caminho_asset("assets/imagens/personagem_parada.png"),
    "andando1_f": caminho_asset("assets/imagens/personagem_mulher_andando1.png"),
    "andando2_f": caminho_asset("assets/imagens/personagem_mulher_andando2.png"),
}
AVATAR_ALTURA = 220  # mesma escala (altura em pixels) usada em fase2.py


# =====================================================================
# 3. FUNÇÕES AUXILIARES DE CARREGAMENTO (mesmo padrão da Fase_4)
# =====================================================================
def carregar_imagem(caminho, tamanho):
    """Tenta carregar uma imagem do disco e redimensioná-la para
    `tamanho` (tupla largura, altura). Devolve None se o arquivo ainda
    não existir -- quem desenha decide o placeholder nesse caso."""
    if caminho and os.path.isfile(caminho):
        imagem = pygame.image.load(caminho).convert_alpha()
        return pygame.transform.smoothscale(imagem, tamanho)
    return None


def carregar_fonte(caminho, tamanho):
    """Carrega uma fonte customizada (.ttf) se disponível, ou usa uma
    fonte monoespaçada do sistema (combina com a estética de terminal)
    como alternativa."""
    if caminho and os.path.isfile(caminho):
        return pygame.font.Font(caminho, tamanho)
    return pygame.font.SysFont("consolas", tamanho)


def carregar_avatar_altura(caminho, altura):
    """Carrega um sprite do avatar e o redimensiona pela ALTURA, mantendo
    a proporção original -- mesma lógica de fase2._scale_fit, só que
    fixada no eixo da altura (é só isso que esta fase precisa)."""
    imagem = pygame.image.load(caminho).convert_alpha()
    escala = altura / imagem.get_height()
    largura = max(1, int(imagem.get_width() * escala))
    return pygame.transform.smoothscale(imagem, (largura, altura))


def _wrap_text(texto, fonte, largura_maxima):
    """Quebra `texto` em linhas que cabem em `largura_maxima` pixels na
    fonte dada -- mesma lógica de fase2._wrap_text (o pygame não quebra
    linha sozinho ao renderizar uma string longa)."""
    palavras = texto.split(" ")
    linhas = []
    atual = ""
    for palavra in palavras:
        candidata = f"{atual} {palavra}".strip()
        if fonte.size(candidata)[0] <= largura_maxima:
            atual = candidata
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def _aplicar_blur(superficie, intensidade=INTRO_BLUR_INTENSIDADE, passos=INTRO_BLUR_PASSOS):
    """Aproxima um efeito de blur/desfoque reduzindo a imagem bem pequena
    e ampliando de volta -- o próprio suavizador do smoothscale espalha os
    pixels nesse processo, dando um efeito parecido com um blur de
    verdade, sem precisar de nenhuma biblioteca externa de imagem (só
    pygame). `passos` repete o processo pra deixar o desfoque mais forte."""
    largura, altura = superficie.get_size()
    resultado = superficie
    for _ in range(passos):
        pequena = pygame.transform.smoothscale(
            resultado,
            (max(1, largura // intensidade), max(1, altura // intensidade)),
        )
        resultado = pygame.transform.smoothscale(pequena, (largura, altura))
    return resultado


# =====================================================================
# 3B. MOVIMENTO DO JOGADOR (mesma lógica/teclas de Pygame/Fase_2/fase2/fase2.py)
# =====================================================================
def _posicao_permitida(pos, floor_rect):
    """True se `pos` (pygame.Vector2) está dentro do chão andável, com uma
    margem de PLAYER_RADIUS pra dentro em cada lado -- mesma conta de
    fase2._position_allowed(), simplificada (o quarto não tem um obstáculo
    solto no meio, como a bancada da oficina)."""
    x, y = pos.x, pos.y
    if not (floor_rect.left + PLAYER_RADIUS <= x <= floor_rect.right - PLAYER_RADIUS):
        return False
    if not (floor_rect.top + PLAYER_RADIUS <= y <= floor_rect.bottom - PLAYER_RADIUS):
        return False
    return True


def _tentar_mover(pos, delta, floor_rect):
    """Aplica o deslocamento `delta`, deslizando ao longo das bordas do
    chão em vez de travar (tenta o movimento completo, depois só X, depois
    só Y) -- mesma lógica de fase2._try_move()."""
    completo = pygame.Vector2(pos.x + delta.x, pos.y + delta.y)
    if _posicao_permitida(completo, floor_rect):
        return completo

    so_x = pygame.Vector2(pos.x + delta.x, pos.y)
    if _posicao_permitida(so_x, floor_rect):
        return so_x

    so_y = pygame.Vector2(pos.x, pos.y + delta.y)
    if _posicao_permitida(so_y, floor_rect):
        return so_y

    return pos


class Jogador:
    """Avatar do jogador com animação de 3 frames (1 parado + 2 de
    caminhada) -- mesma classe/lógica de fase2.Jogador, duplicada aqui (e
    não importada) seguindo o mesmo padrão já usado entre as fases neste
    repositório (cada arquivo de fase fica autocontido).

    self.pos (Vector2) é onde os PÉS do personagem tocam o chão -- mesma
    referência usada pra desenhar (midbottom) e pra colisão.
    """

    VELOCIDADE = 4  # pixels por frame a 60fps, igual à Fase 2
    INTERVALO_ANIMACAO_MS = 150

    def __init__(self, frame_parado, frames_andando, posicao_inicial):
        self.frame_parado = frame_parado
        self.frames_andando = frames_andando  # [andando1, andando2]
        self.indice_animacao = 0
        self.tempo_ultimo_frame = pygame.time.get_ticks()
        self.imagem = self.frame_parado
        self.pos = pygame.Vector2(posicao_inicial)

    def mover(self, teclas, floor_rect):
        """Lê WASD/setas (pygame.key.get_pressed()) e anda na direção
        correspondente -- mesmas teclas da Fase 2."""
        dx = dy = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx -= 1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx += 1
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy -= 1
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy += 1

        esta_andando = (dx != 0 or dy != 0)
        if esta_andando:
            delta = pygame.Vector2(dx, dy).normalize() * self.VELOCIDADE
            self.pos = _tentar_mover(self.pos, delta, floor_rect)

        self._atualizar_sprite(esta_andando)

        if dx < 0:
            self.imagem = pygame.transform.flip(self.imagem, True, False)

    def _atualizar_sprite(self, esta_andando):
        if not esta_andando:
            self.imagem = self.frame_parado
            self.indice_animacao = 0
            return

        agora = pygame.time.get_ticks()
        if agora - self.tempo_ultimo_frame >= self.INTERVALO_ANIMACAO_MS:
            self.indice_animacao = (self.indice_animacao + 1) % len(self.frames_andando)
            self.tempo_ultimo_frame = agora
        self.imagem = self.frames_andando[self.indice_animacao]

    def desenhar(self, tela):
        """Desenha o avatar com os PÉS (midbottom) em self.pos."""
        rect = self.imagem.get_rect(midbottom=(int(self.pos.x), int(self.pos.y)))
        tela.blit(self.imagem, rect)


# =====================================================================
# 4. NPC ASSISTENTE (SYSTEM_AI)
# =====================================================================
# Contexto/system prompt do chatbot desta fase -- mesmo padrão do
# PROMPT_SISTEMA_ADA da Fase 2 (Pygame/Fase_2/fase2/puzzles/ada_chatbot.py):
# um texto que restringe a IA ao tema da fase.
# TODO: reforçar com regras explícitas de escopo/tamanho e exemplos
# few-shot quando o puzzle estiver definido de verdade (foi o que
# resolveu a Ada divagar demais na Fase 2 -- ver ada_chatbot.py).
CONTEXTO_SYSTEM_AI = (
    "Você é SYSTEM_AI, o assistente de um computador entre 1975 e 1990, "
    "ajudando o jogador a entender a passagem da linha de comando pra "
    "interface gráfica (o primeiro desktop). Responda sempre em "
    "português, de forma breve e didática. "
    # TODO: adicionar aqui as regras de escopo ("responda somente sobre "
    # X, Y, Z") e os exemplos few-shot assim que o puzzle for definido.
)


# =====================================================================
# 5. CLASSE PRINCIPAL DO JOGO
# =====================================================================
class Jogo:
    """Controla o laço principal (game loop) e a máquina de estados da
    fase. Estados: QUARTO (cena principal, jogador anda e clica no
    computador), TERMINAL e DESKTOP -- o suficiente pra rodar o esqueleto
    e testar a janela abrindo."""

    QUARTO = "quarto"
    TERMINAL = "terminal"
    DESKTOP = "desktop"
    # TODO: estados extras conforme o puzzle for definido (ex: um
    # estado "MONTANDO_DESKTOP" enquanto o jogador resolve, ou um MENU
    # inicial como a Fase 4 tem).

    def __init__(self, character_image=None, character_name="Jogador", genero="m"):
        # character_image/character_name/genero seguem o mesmo formato que
        # fase2.run() recebe do menu (ver Pygame/menu/jogo.py) -- ainda não
        # há integração desta fase com o menu, então por enquanto
        # `character_image` só é guardado (não usado pra desenhar; quem
        # decide o sprite do avatar é `genero`, igual à Fase 2).
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Fase 9 - A Revolução dos Computadores Pessoais")
        self.relogio = pygame.time.Clock()

        # --- Fontes ---
        self.fonte_terminal = carregar_fonte(ASSETS["fonte_terminal"], 24)
        self.fonte_texto = carregar_fonte(None, 22)
        self.fonte_pequena = carregar_fonte(None, 18)

        # --- Imagens (com placeholder automático se ainda não existirem) ---
        self.img_fundo_desktop = carregar_imagem(ASSETS["fundo_desktop"], (LARGURA, ALTURA))
        self.img_fundo_quarto = carregar_imagem(CENARIO_QUARTO_PATH, (LARGURA, ALTURA))

        # --- Avatar do jogador (mesmos frames/escala da Fase 2) ---
        self.character_name = character_name
        sufixo = "_m" if genero == "m" else "_f"
        self.jogador = Jogador(
            frame_parado=carregar_avatar_altura(AVATAR_ASSETS[f"parado{sufixo}"], AVATAR_ALTURA),
            frames_andando=[
                carregar_avatar_altura(AVATAR_ASSETS[f"andando1{sufixo}"], AVATAR_ALTURA),
                carregar_avatar_altura(AVATAR_ASSETS[f"andando2{sufixo}"], AVATAR_ALTURA),
            ],
            # pés num trecho livre do chão, longe da escrivaninha (que fica
            # à esquerda do quarto, ver COMPUTADOR_RECT/FLOOR_RECT).
            posicao_inicial=(600, 560),
        )

        # --- Tela inicial (intro) ---
        # Retrato grande e NÍTIDO do personagem (mesmo frame parado, só
        # numa escala bem maior) -- desenhado por cima do fundo desfocado,
        # igual à Fase 2.
        self.portrait_intro = carregar_avatar_altura(AVATAR_ASSETS[f"parado{sufixo}"], INTRO_PORTRAIT_HEIGHT)
        # Fundo da intro = o próprio cenário do quarto, mas desfocado (só
        # a imagem -- o personagem nítido é desenhado por cima depois).
        # Calculado uma única vez aqui (não a cada frame): desfocar é bem
        # mais caro que só desenhar a imagem já pronta.
        self.img_intro_fundo = _aplicar_blur(self.img_fundo_quarto) if self.img_fundo_quarto else None

        # --- NPC assistente (SYSTEM_AI) ---
        # Posição fixa por enquanto (canto inferior direito) -- ainda
        # não há um personagem "andando" nesta fase.
        # TODO: ajustar a posição quando o cenário/puzzle da tela de
        # terminal for definido.
        self.rect_npc = pygame.Rect(0, 0, 64, 64)
        self.rect_npc.center = (LARGURA - 80, ALTURA - 80)
        self.npc_chat = NPCChatbot(self.rect_npc, "SYSTEM_AI", CONTEXTO_SYSTEM_AI)

        # --- Estado inicial: a fase sempre começa na cena do quarto ---
        self.estado = Jogo.QUARTO

        # DEBUG temporário (bug do clique no computador): momento (em
        # pygame.time.get_ticks(), ms) até quando mostrar o banner
        # "PUZZLE ABERTO" na tela, pra confirmar visualmente que o clique
        # foi detectado sem precisar olhar o console. Remover quando o
        # puzzle de verdade existir (ver TODO no clique, mais abaixo).
        self.puzzle_debug_ate_ms = 0

    # -----------------------------------------------------------------
    # TELA INICIAL (intro) -- mesma estrutura/estilo de fase2._run_intro
    # (Pygame/Fase_2/fase2/fase2.py): título/subtítulo no topo, o
    # personagem grande e nítido à esquerda, balão de fala com o texto
    # narrativo à direita, botão "Iniciar". ENTER ou clique no botão
    # avança pro jogo; ESC sai sem jogar (mesma tecla/comportamento).
    # -----------------------------------------------------------------
    def _run_intro(self):
        """Roda a tela de introdução (um mini-loop próprio, como o de
        fase2._run_intro). Devolve True pra seguir pro jogo, False se o
        jogador apertou ESC."""
        margem = 20
        title_font = pygame.font.SysFont("consolas", 34, bold=True)
        subtitle_font = pygame.font.SysFont("consolas", 16, bold=True)
        hint_font = pygame.font.SysFont("consolas", 15)
        body_font = pygame.font.SysFont("consolas", 18)
        button_font = pygame.font.SysFont("consolas", 22, bold=True)

        portrait_center = (int(LARGURA * 0.22), int(ALTURA * 0.55))
        bubble_rect = pygame.Rect(int(LARGURA * 0.42), int(ALTURA * 0.28), int(LARGURA * 0.46), int(ALTURA * 0.4))
        linhas = _wrap_text(INTRO_TEXT, body_font, bubble_rect.width - 60)

        button_rect = pygame.Rect(0, 0, 220, 56)
        button_rect.center = (LARGURA // 2, int(ALTURA * 0.87))

        rodando = True
        avancar = True
        while rodando:
            self.relogio.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_RETURN:
                        rodando = False
                    elif evento.key == pygame.K_ESCAPE:
                        rodando = False
                        avancar = False
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if button_rect.collidepoint(evento.pos):
                        rodando = False

            if self.img_intro_fundo:
                self.tela.blit(self.img_intro_fundo, (0, 0))
            else:
                self.tela.fill(PRETO)

            title_surf = title_font.render(TITLE, True, GOLD)
            self.tela.blit(title_surf, title_surf.get_rect(midtop=(LARGURA // 2, margem + 8)))
            subtitle_surf = subtitle_font.render(SUBTITLE, True, CREAM)
            self.tela.blit(subtitle_surf, subtitle_surf.get_rect(midtop=(LARGURA // 2, margem + 46)))

            # Personagem grande e NÍTIDO (sem blur -- só o fundo é
            # desfocado) por cima do cenário.
            if self.portrait_intro:
                self.tela.blit(self.portrait_intro, self.portrait_intro.get_rect(center=portrait_center))
            else:
                pygame.draw.circle(self.tela, GOLD, portrait_center, 90)

            pygame.draw.rect(self.tela, INTRO_BUBBLE_BG, bubble_rect, border_radius=24)
            pygame.draw.rect(self.tela, INTRO_BUBBLE_BORDER, bubble_rect, width=3, border_radius=24)

            line_h = body_font.get_height() + 6
            text_top = bubble_rect.centery - (len(linhas) * line_h) // 2
            for i, linha in enumerate(linhas):
                linha_surf = body_font.render(linha, True, INTRO_BUBBLE_BORDER)
                self.tela.blit(linha_surf, linha_surf.get_rect(midtop=(bubble_rect.centerx, text_top + i * line_h)))

            hovered = button_rect.collidepoint(mouse_pos)
            pygame.draw.rect(self.tela, (66, 48, 30) if hovered else (43, 30, 20), button_rect, border_radius=10)
            pygame.draw.rect(self.tela, GOLD, button_rect, width=2, border_radius=10)
            button_text = button_font.render("Iniciar", True, GOLD if hovered else CREAM)
            self.tela.blit(button_text, button_text.get_rect(center=button_rect.center))

            start_hint = hint_font.render(INTRO_START_HINT, True, CREAM)
            self.tela.blit(start_hint, start_hint.get_rect(midtop=(LARGURA // 2, button_rect.bottom + 12)))

            pygame.display.flip()

        return avancar

    # -----------------------------------------------------------------
    # LAÇO PRINCIPAL DO JOGO
    # -----------------------------------------------------------------
    def executar(self):
        # Tela de introdução --> só aparece aqui, na entrada da fase. Se o
        # jogador apertar ESC na intro, sai da fase sem nem começar a cena
        # jogável (mesma regra de fase2.run()).
        if not self._run_intro():
            return

        rodando = True
        while rodando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    rodando = False

                elif evento.type == pygame.KEYDOWN:
                    if self.npc_chat.dialogo_aberto:
                        # Com a conversa aberta, todo o teclado é dela
                        # (mesma regra usada pelos NPCs das outras fases).
                        self.npc_chat.tratar_evento(evento)
                    elif evento.key == pygame.K_ESCAPE:
                        rodando = False
                    elif evento.key == pygame.K_e:
                        # TODO: sem checar distância ainda (ver
                        # perto_do_jogador em npc_chatbot.py) -- por
                        # enquanto E sempre abre o SYSTEM_AI.
                        self.npc_chat.abrir_dialogo()

                    # TODO: eventos do puzzle da tela de terminal
                    # (digitar comandos, montar o desktop, etc.) entram
                    # aqui -- provavelmente um bloco dedicado tipo
                    # "elif self.estado == Jogo.TERMINAL: ..."

                elif (
                    evento.type == pygame.MOUSEBUTTONDOWN
                    and evento.button == 1
                    and self.estado == Jogo.QUARTO
                    and not self.npc_chat.dialogo_aberto
                ):
                    # DEBUG temporário -- imprime TODO clique (dentro ou
                    # fora do retângulo), pra comparar a coordenada real
                    # do clique com COMPUTADOR_RECT caso ele continue sem
                    # disparar. TODO: remover quando o puzzle de verdade
                    # existir e o clique já estiver confirmado funcionando.
                    dentro = COMPUTADOR_RECT.collidepoint(evento.pos)
                    print(f"[DEBUG] clique em {evento.pos} | janela real: "
                          f"{pygame.display.get_surface().get_size()} | "
                          f"COMPUTADOR_RECT: {tuple(COMPUTADOR_RECT)} | dentro? {dentro}")
                    if dentro:
                        # TODO: abrir o puzzle de verdade (linha de comando
                        # -> desktop) aqui. Por enquanto só um placeholder
                        # pra confirmar que a área clicável está certa.
                        print("Computador clicado -- TODO: abrir puzzle da Fase 9")
                        self.puzzle_debug_ate_ms = pygame.time.get_ticks() + 2000

            # Movimento do jogador só faz sentido na cena do quarto, e só
            # quando nenhuma caixa de diálogo está roubando o teclado
            # (mesma regra da Fase 2).
            if self.estado == Jogo.QUARTO and not self.npc_chat.dialogo_aberto:
                teclas = pygame.key.get_pressed()
                self.jogador.mover(teclas, FLOOR_RECT)

            # TODO: lógica de atualização do puzzle entra aqui --
            # checar se o jogador já "montou" o desktop corretamente e,
            # quando isso acontecer, disparar a transição (fade?) e só
            # depois trocar self.estado para Jogo.DESKTOP.

            if self.estado == Jogo.QUARTO:
                self._desenhar_quarto()
            elif self.estado == Jogo.TERMINAL:
                self._desenhar_terminal()
            elif self.estado == Jogo.DESKTOP:
                self._desenhar_desktop()

            self.npc_chat.desenhar(self.tela, self.fonte_texto, self.fonte_pequena, LARGURA, ALTURA)
            if not self.npc_chat.dialogo_aberto:
                self.npc_chat.desenhar_dica_interacao(self.tela, self.fonte_pequena)

            pygame.display.flip()
            self.relogio.tick(FPS)

    # -----------------------------------------------------------------
    # DESENHO: QUARTO (cena principal -- jogador anda e clica no computador)
    # -----------------------------------------------------------------
    def _desenhar_quarto(self):
        """Quarto retrô: fundo fixo (cenario_fase_9.png) + o jogador
        andando por cima. COMPUTADOR_RECT é só uma área invisível (não
        desenhada) sobre o computador que já faz parte do fundo."""
        if self.img_fundo_quarto:
            self.tela.blit(self.img_fundo_quarto, (0, 0))
        else:
            self.tela.fill(PRETO)

        self.jogador.desenhar(self.tela)

        nome_render = self.fonte_pequena.render(self.character_name, True, BRANCO)
        self.tela.blit(nome_render, nome_render.get_rect(
            midtop=(int(self.jogador.pos.x), int(self.jogador.pos.y) + 4)
        ))

        # DEBUG temporário -- contorno do retângulo clicável do computador,
        # pra confirmar visualmente que ele está em cima do monitor/teclado
        # da escrivaninha na imagem real (ver bug do clique não funcionar).
        # TODO: remover esta linha quando o puzzle de verdade existir.
        pygame.draw.rect(self.tela, (255, 40, 40), COMPUTADOR_RECT, width=2)

        # DEBUG temporário -- banner "PUZZLE ABERTO" por 2s após o clique
        # no computador, pra confirmar o clique sem precisar olhar o
        # console. TODO: substituir pela abertura de verdade do puzzle.
        if pygame.time.get_ticks() < self.puzzle_debug_ate_ms:
            banner_font = pygame.font.SysFont("consolas", 30, bold=True)
            banner = banner_font.render("PUZZLE ABERTO", True, (255, 230, 60))
            fundo_rect = banner.get_rect(center=(LARGURA // 2, 90)).inflate(30, 20)
            pygame.draw.rect(self.tela, (20, 20, 20), fundo_rect, border_radius=8)
            pygame.draw.rect(self.tela, (255, 230, 60), fundo_rect, width=2, border_radius=8)
            self.tela.blit(banner, banner.get_rect(center=fundo_rect.center))

    # -----------------------------------------------------------------
    # DESENHO: TERMINAL (placeholder do puzzle)
    # -----------------------------------------------------------------
    def _desenhar_terminal(self):
        """Tela de terminal preta com um cursor piscando -- placeholder
        até o puzzle de verdade (linha de comando -> desktop) ser
        implementado."""
        self.tela.fill(PRETO)

        # TODO: texto/prompt de verdade (e o puzzle em si) entram aqui.
        # Por enquanto só um prompt fixo com cursor piscando, pra
        # confirmar que a janela e o laço principal estão funcionando.
        prompt = "C:\\>"
        cursor_aceso = pygame.time.get_ticks() % 1000 < 500
        texto = prompt + ("_" if cursor_aceso else " ")
        render = self.fonte_terminal.render(texto, True, VERDE_TERMINAL)
        self.tela.blit(render, (40, ALTURA - 60))

        # TODO: desenhar aqui os elementos do puzzle (ícones espalhados,
        # janelas incompletas, comandos disponíveis, o que for definido)
        # conforme a mecânica for criada.

    # -----------------------------------------------------------------
    # DESENHO: DESKTOP (tela final, quando o puzzle for resolvido)
    # -----------------------------------------------------------------
    def _desenhar_desktop(self):
        """Área de trabalho colorida -- mostrada quando o puzzle for
        resolvido e a fase "acende". Por enquanto só um placeholder de
        cor sólida (ou a imagem de fundo, se já existir)."""
        if self.img_fundo_desktop:
            self.tela.blit(self.img_fundo_desktop, (0, 0))
        else:
            self.tela.fill(AZUL_DESKTOP)

        # TODO: elementos do desktop reconstruído (ícones, janelas,
        # barra de tarefas -- o que for decidido) entram aqui.
        # TODO: a transição de verdade entre TERMINAL e DESKTOP (fade
        # ou outro efeito) deve acontecer ANTES da fase chegar nesse
        # estado, não aqui dentro do desenho -- ver TODO em executar().


# =====================================================================
# 6. PONTO DE ENTRADA DO PROGRAMA
# =====================================================================
if __name__ == "__main__":
    jogo = Jogo()
    jogo.executar()
