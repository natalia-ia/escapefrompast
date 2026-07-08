"""
Fase 2 — As Máquinas Mecânicas (1800-1840)

A cena é a oficina de Babbage. O jogador anda com WASD/setas ou clique do
mouse e precisa achar os 4 pontos de coleta escondidos pela sala (baú, pote
e caixote, que abrem ao clicar, mais uma engrenagem escondida num dos
desenhos já ilustrados no papel/planta da parede) para juntar uma
engrenagem de cada um. Depois de coletar as 4, a planta libera o puzzle
"ligar a máquina" (babbage_lovelace.py). Resolvê-lo não encerra a fase na
hora: uma transição (fade) leva o personagem para uma sala separada, só
com a máquina do tempo — ele entra pela lateral esquerda e anda sozinho
(sem controle do jogador) até perto dela; ao chegar, o jogador recupera o
controle e só precisa clicar nela para concluir a fase.

`run()` reutiliza a mesma janela/clock do jogo principal. Devolve `True` se
o jogador concluiu a fase (clicou na máquina do tempo), ou `False` se saiu
antes apertando ESC.
"""

import math
import os

import pygame

from .puzzles import babbage_lovelace

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Paleta de textos da UI (Fase 2) — dourado para títulos, bege para
# instruções, verde-oliva para status/sucesso.
GOLD = (212, 168, 67)
CREAM = (232, 212, 176)
OLIVE = (138, 155, 110)
RED = (255, 70, 70)
WHITE = (225, 230, 235)
GREEN = (0, 255, 140)  # usado só em marcadores/efeitos visuais, não em texto

PLAYER_SPEED = 240  # pixels por segundo
PLAYER_RADIUS = 22
CLICK_ARRIVE_DIST = 4

TITLE = "FASE 2"
SUBTITLE = "AS MÁQUINAS MECÂNICAS  —  1800-1840"
HINT = "WASD / SETAS andam, CLIQUE move ou interage, ESC volta ao mapa"
MACHINE_HINT = "Entre na máquina do tempo para ir para a próxima fase!"

# Tela de introdução — aparece uma única vez, antes da cena jogável.
INTRO_TEXT = (
    "A Cápsula do Tempo me trouxe a uma velha oficina em Londres. "
    "Encontrei anotações de Charles Babbage sobre uma 'Máquina Analítica', "
    "e cartões de instrução de Ada Lovelace. Preciso reunir as peças "
    "espalhadas e programar a máquina para avançar no tempo!"
)
INTRO_START_HINT = "Clique em Iniciar ou pressione ENTER"
INTRO_PORTRAIT_HEIGHT = 480  # bem maior que o sprite usado durante o jogo
INTRO_BUBBLE_BG = (232, 220, 196)  # bege claro, mesmo tom da família do CREAM
INTRO_BUBBLE_BORDER = (60, 45, 30)  # contorno escuro estilo quadrinho

GEAR_SPRITE_SIZE = 24
GEAR_HOVER_SCALE = 1.1
GEAR_HOVER_RADIUS = 20  # um pouco maior que o sprite: "perto ou sobre" já destaca
GEAR_IDLE_ALPHA = 165  # ~65% — some um pouco até o mouse chegar perto
SHADOW_ALPHA = 140  # opacidade da sombra elíptica sob os objetos soltos no chão

# Os 3 objetos com estado fechado/aberto que escondem uma engrenagem cada.
# "fit" diz como a imagem é escalada: ("h", altura) mantém a altura fixa
# (objetos "verticais"), ("w", largura) mantém a largura fixa.
# "shadow" (largura, altura) desenha uma sombra elíptica sob o objeto, para
# fixá-lo visualmente na superfície onde está — pote fica sobre o tampo da
# mesa (sombra pequena e sutil), bau e caixote ficam soltos no chão.
CONTAINERS = [
    {"key": "bau", "pos": (615, 466), "closed": "bau_fechado", "open": "bau_aberto", "fit": ("h", 55), "rot": 0, "shadow": (56, 16)},
    {"key": "pote", "pos": (350, 365), "closed": "pote_fechado", "open": "pote_aberto", "fit": ("h", 40), "rot": 0, "shadow": (24, 7)},
    {"key": "caixote", "pos": (780, 575), "closed": "caixote_fechado", "open": "caixote_aberto", "fit": ("h", 60), "rot": 0, "shadow": (60, 16)},
]

# Área do papel/planta na parede, estimada a partir da imagem de fundo.
PAPER_RECT = pygame.Rect(210, 130, 275, 190)

# 4ª engrenagem escondida: não é um sprite próprio, é uma área clicável sobre
# um dos desenhos de engrenagem que já existem ilustrados no papel de fundo
# (a maior, no canto superior direito do desenho). Área independente do
# PAPER_RECT — clicar aqui coleta a engrenagem; clicar no resto do papel
# abre o puzzle (só depois de todas as 4 coletadas).
PAPER_GEAR_KEY = "engrenagem_papel"
PAPER_GEAR_RECT = pygame.Rect(390, 140, 60, 60)
PAPER_GEAR_POS = PAPER_GEAR_RECT.center
PAPER_GEAR_FLASH_SECONDS = 0.6

# Colisão da oficina: faixa de chão andável (o resto é parede/janela, onde
# o personagem não deve conseguir pisar) e a bancada central, bloqueada por
# inteiro (tampo + pernas) como um único retângulo.
FLOOR_RECT = pygame.Rect(20, 400, 960, 230)
TABLE_RECT = pygame.Rect(160, 355, 380, 175)

# Sala da máquina do tempo — só existe depois que o puzzle de Babbage é
# resolvido: uma transição (fade) troca o fundo da oficina por
# sala_maquina_tempo.png e leva o personagem pra lá. Sem bancada nem outros
# obstáculos, só o chão andável.
MACHINE_ROOM_FLOOR_RECT = pygame.Rect(20, 480, 960, 150)
MACHINE_ROOM_ENTRY_POS = (60, 550)  # onde o personagem aparece, como se tivesse entrado por uma porta à esquerda
TIME_MACHINE_FIT = ("h", 410)
TIME_MACHINE_POS = (720, 295)  # espaço vazio de parede reservado na nova sala (canto central-direita)
TIME_MACHINE_ARRIVAL_POS = (720, 560)  # onde o personagem para, na caminhada automática
FADE_DURATION_SECONDS = 0.35

# As imagens só podem passar por .convert()/.convert_alpha() depois que a
# janela existir (pygame.display.set_mode()). Como menu/jogo.py importa este
# módulo antes de criar a janela, o carregamento é adiado para _load_assets(),
# chamado no início de run() — mesmo padrão de common.init_fonts().
BACKGROUND = None
INTRO_BACKGROUND = None
MACHINE_ROOM_BACKGROUND = None
GEAR_SMALL = None
GEAR_SMALL_HOVER = None
GEAR_LARGE = None  # reservada para uso futuro — ainda não é desenhada na cena.
CLOSED_SPRITES = {}
OPEN_SPRITES = {}
TIME_MACHINE_SPRITE = None
TIME_MACHINE_RECT = None


def _scale_fit(img, fit, rot=0):
    axis, size = fit
    if axis == "h":
        scale = size / img.get_height()
    else:
        scale = size / img.get_width()
    scaled = pygame.transform.smoothscale(img, (max(1, int(img.get_width() * scale)), max(1, int(img.get_height() * scale))))
    if rot:
        scaled = pygame.transform.rotate(scaled, rot)
    return scaled


def _wrap_text(text, font, max_width):
    """Quebra `text` em linhas que cabem em `max_width` pixels na `font`
    dada — pygame não faz isso sozinho, então cada palavra é testada antes
    de entrar na linha atual."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _load_assets():
    global BACKGROUND, INTRO_BACKGROUND, MACHINE_ROOM_BACKGROUND, GEAR_SMALL, GEAR_SMALL_HOVER, GEAR_LARGE, TIME_MACHINE_SPRITE, TIME_MACHINE_RECT
    if BACKGROUND is not None:
        return

    bg_raw = pygame.image.load(os.path.join(ASSETS_DIR, "background_oficina.png")).convert()
    BACKGROUND = pygame.transform.smoothscale(bg_raw, (1000, 650))

    intro_bg_raw = pygame.image.load(os.path.join(ASSETS_DIR, "cenario_intro_blur.png")).convert()
    INTRO_BACKGROUND = pygame.transform.smoothscale(intro_bg_raw, (1000, 650))

    machine_room_bg_raw = pygame.image.load(os.path.join(ASSETS_DIR, "sala_maquina_tempo.png")).convert()
    MACHINE_ROOM_BACKGROUND = pygame.transform.smoothscale(machine_room_bg_raw, (1000, 650))

    gear_small_raw = pygame.image.load(os.path.join(ASSETS_DIR, "gear_small.png")).convert_alpha()
    GEAR_SMALL = pygame.transform.scale(gear_small_raw, (GEAR_SPRITE_SIZE, GEAR_SPRITE_SIZE))
    GEAR_SMALL.set_alpha(GEAR_IDLE_ALPHA)  # ~65% parada; some no cenário até o mouse chegar perto
    hover_size = int(GEAR_SPRITE_SIZE * GEAR_HOVER_SCALE)
    GEAR_SMALL_HOVER = pygame.transform.scale(gear_small_raw, (hover_size, hover_size))
    # GEAR_SMALL_HOVER fica com alpha cheio (100%) — é o destaque de "encontrado".

    gear_large_raw = pygame.image.load(os.path.join(ASSETS_DIR, "gear_large.png")).convert_alpha()
    GEAR_LARGE = pygame.transform.scale(gear_large_raw, (96, 96))

    for c in CONTAINERS:
        closed_raw = pygame.image.load(os.path.join(ASSETS_DIR, f"{c['closed']}.png")).convert_alpha()
        open_raw = pygame.image.load(os.path.join(ASSETS_DIR, f"{c['open']}.png")).convert_alpha()
        CLOSED_SPRITES[c["key"]] = _scale_fit(closed_raw, c["fit"], c.get("rot", 0))
        OPEN_SPRITES[c["key"]] = _scale_fit(open_raw, c["fit"], c.get("rot", 0))

    machine_raw = pygame.image.load(os.path.join(ASSETS_DIR, "maquina_do_tempo_v4.png")).convert_alpha()
    TIME_MACHINE_SPRITE = _scale_fit(machine_raw, TIME_MACHINE_FIT)
    TIME_MACHINE_RECT = TIME_MACHINE_SPRITE.get_rect(center=TIME_MACHINE_POS)


def _draw_player(screen, pos, character_image, character_name, name_font):
    if character_image:
        rect = character_image.get_rect(center=(int(pos.x), int(pos.y)))
        screen.blit(character_image, rect)
        label_y = rect.bottom + 4
    else:
        pygame.draw.circle(screen, GREEN, (int(pos.x), int(pos.y)), PLAYER_RADIUS)
        pygame.draw.circle(screen, (10, 12, 24), (int(pos.x), int(pos.y)), PLAYER_RADIUS - 5)
        label_y = int(pos.y) + PLAYER_RADIUS + 4

    name_surf = name_font.render(character_name, True, WHITE)
    screen.blit(name_surf, name_surf.get_rect(midtop=(int(pos.x), label_y)))


def _position_allowed(pos, floor_rect, table_rect=None):
    """True se o personagem pode ficar nessa posição: dentro do chão
    andável da sala atual e fora da área bloqueada da bancada (quando a
    sala tem uma — a sala da máquina do tempo não tem)."""
    x, y = pos.x, pos.y
    if not (floor_rect.left + PLAYER_RADIUS <= x <= floor_rect.right - PLAYER_RADIUS):
        return False
    if not (floor_rect.top + PLAYER_RADIUS <= y <= floor_rect.bottom - PLAYER_RADIUS):
        return False
    if table_rect is not None:
        blocked = table_rect.inflate(PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
        if blocked.collidepoint(x, y):
            return False
    return True


def _try_move(pos, delta, floor_rect, table_rect=None):
    """Aplica um deslocamento, deslizando ao longo de paredes/obstáculos em
    vez de travar (tenta o movimento completo, depois só X, depois só Y)."""
    full = pygame.Vector2(pos.x + delta.x, pos.y + delta.y)
    if _position_allowed(full, floor_rect, table_rect):
        return full, True
    only_x = pygame.Vector2(pos.x + delta.x, pos.y)
    if _position_allowed(only_x, floor_rect, table_rect):
        return only_x, True
    only_y = pygame.Vector2(pos.x, pos.y + delta.y)
    if _position_allowed(only_y, floor_rect, table_rect):
        return only_y, True
    return pos, False


def _run_intro(screen, clock, character_image, width, height, title_font, subtitle_font, hint_font):
    """Tela de introdução (uma vez só, antes da cena jogável): personagem
    grande à esquerda, balão de fala à direita, título/subtítulo iguais aos
    do HUD principal e um botão "Iniciar". Devolve True para seguir pro
    jogo, False se o jogador saiu (ESC) — mesmo padrão de retorno de run()."""
    margin = 20
    body_font = pygame.font.SysFont("consolas", 18)
    button_font = pygame.font.SysFont("consolas", 22, bold=True)

    portrait = None
    if character_image:
        scale = INTRO_PORTRAIT_HEIGHT / character_image.get_height()
        portrait = pygame.transform.smoothscale(
            character_image,
            (max(1, int(character_image.get_width() * scale)), INTRO_PORTRAIT_HEIGHT),
        )
    portrait_center = (int(width * 0.22), int(height * 0.55))

    bubble_rect = pygame.Rect(int(width * 0.42), int(height * 0.28), int(width * 0.46), int(height * 0.4))
    lines = _wrap_text(INTRO_TEXT, body_font, bubble_rect.width - 60)

    button_rect = pygame.Rect(0, 0, 220, 56)
    button_rect.center = (width // 2, int(height * 0.87))

    running = True
    advance = True
    while running:
        clock.tick(60)

        real_screen = pygame.display.get_surface()
        real_w, real_h = real_screen.get_size()
        scale_x, scale_y = width / real_w, height / real_h
        raw_mouse = pygame.mouse.get_pos()
        mouse_pos = (raw_mouse[0] * scale_x, raw_mouse[1] * scale_y)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    running = False
                elif event.key == pygame.K_ESCAPE:
                    running = False
                    advance = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click_pos = (event.pos[0] * scale_x, event.pos[1] * scale_y)
                if button_rect.collidepoint(click_pos):
                    running = False

        screen.blit(INTRO_BACKGROUND, (0, 0))

        title_surf = title_font.render(TITLE, True, GOLD)
        screen.blit(title_surf, title_surf.get_rect(midtop=(width // 2, margin + 8)))
        subtitle_surf = subtitle_font.render(SUBTITLE, True, CREAM)
        screen.blit(subtitle_surf, subtitle_surf.get_rect(midtop=(width // 2, margin + 46)))

        if portrait:
            screen.blit(portrait, portrait.get_rect(center=portrait_center))
        else:
            pygame.draw.circle(screen, GREEN, portrait_center, 90)

        pygame.draw.rect(screen, INTRO_BUBBLE_BG, bubble_rect, border_radius=24)
        pygame.draw.rect(screen, INTRO_BUBBLE_BORDER, bubble_rect, width=3, border_radius=24)
        line_h = body_font.get_height() + 6
        text_top = bubble_rect.centery - (len(lines) * line_h) // 2
        for i, line in enumerate(lines):
            line_surf = body_font.render(line, True, INTRO_BUBBLE_BORDER)
            screen.blit(line_surf, line_surf.get_rect(midtop=(bubble_rect.centerx, text_top + i * line_h)))

        hovered = button_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (66, 48, 30) if hovered else (43, 30, 20), button_rect, border_radius=10)
        pygame.draw.rect(screen, GOLD, button_rect, width=2, border_radius=10)
        button_text = button_font.render("Iniciar", True, GOLD if hovered else CREAM)
        screen.blit(button_text, button_text.get_rect(center=button_rect.center))

        start_hint = hint_font.render(INTRO_START_HINT, True, CREAM)
        screen.blit(start_hint, start_hint.get_rect(midtop=(width // 2, button_rect.bottom + 12)))

        scaled = pygame.transform.smoothscale(screen, (real_w, real_h))
        real_screen.blit(scaled, (0, 0))
        pygame.display.flip()

    return advance


def _fade_transition(screen, clock, before_surface, after_surface, duration=FADE_DURATION_SECONDS):
    """Fade simples entre dois quadros já prontos: escurece `before_surface`
    até preto, depois clareia até `after_surface`. Usado só na troca
    oficina -> sala da máquina do tempo, então não processa cliques nem
    teclado — só QUIT, pra não travar a janela achando que o app travou."""
    steps = max(1, int(duration * 60))
    for source, fading_out in ((before_surface, True), (after_surface, False)):
        for i in range(steps):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            clock.tick(60)

            screen.blit(source, (0, 0))
            progress = (i + 1) / steps
            alpha = int(255 * progress) if fading_out else int(255 * (1 - progress))
            overlay = pygame.Surface(screen.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(alpha)
            screen.blit(overlay, (0, 0))

            real_screen = pygame.display.get_surface()
            scaled = pygame.transform.smoothscale(screen, real_screen.get_size())
            real_screen.blit(scaled, (0, 0))
            pygame.display.flip()


def run(screen, clock, character_image=None, character_name="Jogador"):
    """Roda o loop da Fase 2. Devolve True se concluída, False se saiu antes."""
    _load_assets()
    width, height = screen.get_size()
    margin = 20

    title_font = pygame.font.SysFont("consolas", 34, bold=True)
    subtitle_font = pygame.font.SysFont("consolas", 16, bold=True)
    hint_font = pygame.font.SysFont("consolas", 15)
    name_font = pygame.font.SysFont("consolas", 15, bold=True)
    counter_font = pygame.font.SysFont("consolas", 18, bold=True)

    # Tela de introdução -- só aparece aqui, uma vez, na entrada da fase;
    # reabrir o puzzle depois não passa mais por este ponto do código.
    if not _run_intro(screen, clock, character_image, width, height, title_font, subtitle_font, hint_font):
        return False

    container_open = {c["key"]: False for c in CONTAINERS}
    collected = {c["key"]: False for c in CONTAINERS}
    collected[PAPER_GEAR_KEY] = False
    total_gears = len(CONTAINERS) + 1

    player_pos = pygame.Vector2(340, 558)  # chão aberto em frente à bancada, entre baú e caixote
    click_target = None

    hint_msg = ""
    hint_timer = 0.0
    paper_gear_flash_timer = 0.0
    in_machine_room = False  # troca pra True só depois do puzzle resolvido (fade)
    walking_to_machine = False  # caminhada automática até a máquina, sem controle do jogador
    arrived_at_machine = False  # liberou o controle; só falta clicar na máquina
    completed = False

    running = True
    while running:
        dt = clock.tick(60) / 1000

        # a janela real pode ter um tamanho diferente da tela virtual
        # (width x height, o espaço em que todas as coordenadas da fase já
        # são calculadas) -- converte mouse/clique de volta pra cá antes de
        # checar qualquer colisão.
        real_screen = pygame.display.get_surface()
        real_w, real_h = real_screen.get_size()
        scale_x, scale_y = width / real_w, height / real_h
        raw_mouse = pygame.mouse.get_pos()
        mouse_pos = (raw_mouse[0] * scale_x, raw_mouse[1] * scale_y)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not walking_to_machine:
                click_pos = (event.pos[0] * scale_x, event.pos[1] * scale_y)
                clicked_something = False

                if in_machine_room:
                    if arrived_at_machine and TIME_MACHINE_RECT.collidepoint(click_pos):
                        completed = True
                        running = False
                        clicked_something = True
                else:
                    for c in CONTAINERS:
                        key = c["key"]
                        is_open = container_open[key]
                        sprite = OPEN_SPRITES[key] if is_open else CLOSED_SPRITES[key]
                        rect = sprite.get_rect(center=c["pos"])

                        if not is_open:
                            if rect.collidepoint(click_pos):
                                container_open[key] = True
                                clicked_something = True
                                break
                        elif not collected[key]:
                            gx, gy = c["pos"]
                            if math.hypot(click_pos[0] - gx, click_pos[1] - gy) <= GEAR_HOVER_RADIUS:
                                collected[key] = True
                                clicked_something = True
                                break

                    if (
                        not clicked_something
                        and not collected[PAPER_GEAR_KEY]
                        and PAPER_GEAR_RECT.collidepoint(click_pos)
                    ):
                        collected[PAPER_GEAR_KEY] = True
                        paper_gear_flash_timer = PAPER_GEAR_FLASH_SECONDS
                        clicked_something = True

                    if not clicked_something and PAPER_RECT.collidepoint(click_pos):
                        clicked_something = True
                        if all(collected.values()):
                            if babbage_lovelace.run(screen, clock):
                                # transição pra sala separada da máquina do tempo --
                                # fade a partir do último quadro da oficina (ainda
                                # em `screen`) até um quadro novo já com o fundo da
                                # sala, a máquina e o personagem na entrada (lateral
                                # esquerda, como se tivesse atravessado uma porta).
                                before_surface = screen.copy()
                                after_surface = pygame.Surface((width, height))
                                after_surface.blit(MACHINE_ROOM_BACKGROUND, (0, 0))
                                after_surface.blit(TIME_MACHINE_SPRITE, TIME_MACHINE_RECT)
                                _draw_player(after_surface, pygame.Vector2(MACHINE_ROOM_ENTRY_POS), character_image, character_name, name_font)
                                _fade_transition(screen, clock, before_surface, after_surface)

                                in_machine_room = True
                                player_pos = pygame.Vector2(MACHINE_ROOM_ENTRY_POS)
                                walking_to_machine = True
                                click_target = None
                        else:
                            hint_msg = "Ainda faltam engrenagens para juntar."
                            hint_timer = 2.0

                if not clicked_something:
                    click_target = pygame.Vector2(click_pos)

        floor_rect = MACHINE_ROOM_FLOOR_RECT if in_machine_room else FLOOR_RECT
        table_rect = None if in_machine_room else TABLE_RECT

        if walking_to_machine:
            # caminhada automática até a máquina do tempo -- ignora
            # teclado/clique do jogador; usa a mesma _try_move (com
            # deslize em obstáculos) e velocidade do movimento normal.
            direction = pygame.Vector2(TIME_MACHINE_ARRIVAL_POS) - player_pos
            dist = direction.length()
            if dist <= CLICK_ARRIVE_DIST:
                player_pos = pygame.Vector2(TIME_MACHINE_ARRIVAL_POS)
                walking_to_machine = False
                arrived_at_machine = True
            else:
                step = min(PLAYER_SPEED * dt, dist)
                player_pos, _ = _try_move(player_pos, direction.normalize() * step, floor_rect, table_rect)
        else:
            keys = pygame.key.get_pressed()
            move = pygame.Vector2(0, 0)
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                move.y -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                move.y += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                move.x -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                move.x += 1

            if move.length_squared() > 0:
                click_target = None  # teclado cancela o alvo do clique
                player_pos, _ = _try_move(player_pos, move.normalize() * PLAYER_SPEED * dt, floor_rect, table_rect)
            elif click_target is not None:
                direction = click_target - player_pos
                dist = direction.length()
                if dist <= CLICK_ARRIVE_DIST:
                    click_target = None
                else:
                    step = min(PLAYER_SPEED * dt, dist)
                    player_pos, moved = _try_move(player_pos, direction.normalize() * step, floor_rect, table_rect)
                    if not moved:
                        click_target = None  # caminho bloqueado (ex.: outro lado da bancada)

        # --- desenho ---
        screen.blit(MACHINE_ROOM_BACKGROUND if in_machine_room else BACKGROUND, (0, 0))

        title_surf = title_font.render(TITLE, True, GOLD)
        screen.blit(title_surf, title_surf.get_rect(midtop=(width // 2, margin + 8)))
        subtitle_surf = subtitle_font.render(SUBTITLE, True, CREAM)
        screen.blit(subtitle_surf, subtitle_surf.get_rect(midtop=(width // 2, margin + 46)))

        if in_machine_room:
            # sala separada: só a máquina do tempo -- os objetos da oficina
            # (baú/pote/caixote/papel) já cumpriram seu papel e não existem
            # mais aqui.
            screen.blit(TIME_MACHINE_SPRITE, TIME_MACHINE_RECT)
        else:
            # --- objetos com engrenagem escondida ---
            for c in CONTAINERS:
                key = c["key"]
                is_open = container_open[key]
                sprite = OPEN_SPRITES[key] if is_open else CLOSED_SPRITES[key]
                rect = sprite.get_rect(center=c["pos"])

                shadow = c.get("shadow")
                if shadow:
                    sw, sh = shadow
                    shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
                    pygame.draw.ellipse(shadow_surf, (0, 0, 0, SHADOW_ALPHA), shadow_surf.get_rect())
                    screen.blit(shadow_surf, shadow_surf.get_rect(center=(c["pos"][0], rect.bottom - 4)))

                screen.blit(sprite, rect)

                if is_open and not collected[key]:
                    gx, gy = c["pos"]
                    hovered = math.hypot(mouse_pos[0] - gx, mouse_pos[1] - gy) <= GEAR_HOVER_RADIUS
                    if hovered:
                        glow_radius = int(GEAR_SPRITE_SIZE * GEAR_HOVER_SCALE) // 2 + 8
                        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (*GOLD, 90), (glow_radius, glow_radius), glow_radius)
                        screen.blit(glow_surf, glow_surf.get_rect(center=(gx, gy)))
                    gear_sprite = GEAR_SMALL_HOVER if hovered else GEAR_SMALL
                    screen.blit(gear_sprite, gear_sprite.get_rect(center=(gx, gy)))

            # --- engrenagem escondida no desenho do papel (canto superior
            # direito) --- é só uma área clicável sobre a arte de fundo; o
            # desenho em si nunca muda, só o brilho dourado (hover, e um
            # flash rápido no momento da coleta).
            glow_radius = max(PAPER_GEAR_RECT.width, PAPER_GEAR_RECT.height) // 2 + 6
            if not collected[PAPER_GEAR_KEY]:
                if PAPER_GEAR_RECT.collidepoint(mouse_pos):
                    glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*GOLD, 90), (glow_radius, glow_radius), glow_radius)
                    screen.blit(glow_surf, glow_surf.get_rect(center=PAPER_GEAR_POS))
            elif paper_gear_flash_timer > 0:
                alpha = int(220 * (paper_gear_flash_timer / PAPER_GEAR_FLASH_SECONDS))
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*GOLD, alpha), (glow_radius, glow_radius), glow_radius)
                screen.blit(glow_surf, glow_surf.get_rect(center=PAPER_GEAR_POS))

            # papel / planta na parede — PAPER_RECT só existe para detecção
            # de clique (collidepoint); nada é desenhado sobre a arte de
            # fundo.
            paper_ready = all(collected.values())
            if paper_ready:
                paper_hint = counter_font.render("Clique para consultar a planta", True, OLIVE)
                screen.blit(paper_hint, paper_hint.get_rect(midtop=(PAPER_RECT.centerx, PAPER_RECT.bottom + 8)))

            # contador de progresso
            counter_text = f"Engrenagens: {sum(collected.values())}/{total_gears}"
            counter_surf = counter_font.render(counter_text, True, OLIVE if paper_ready else CREAM)
            screen.blit(counter_surf, (width - counter_surf.get_width() - 30, margin + 14))

        _draw_player(screen, player_pos, character_image, character_name, name_font)

        if paper_gear_flash_timer > 0:
            paper_gear_flash_timer -= dt

        if hint_timer > 0:
            hint_timer -= dt
            hint_surf = counter_font.render(hint_msg, True, RED)
            screen.blit(hint_surf, hint_surf.get_rect(midtop=(width // 2, height - 100)))

        if in_machine_room:
            bottom_hint = MACHINE_HINT if arrived_at_machine else ""
        else:
            bottom_hint = HINT
        if bottom_hint:
            hint_surf2 = hint_font.render(bottom_hint, True, CREAM)
            screen.blit(hint_surf2, hint_surf2.get_rect(midbottom=(width // 2, height - margin - 6)))

        # redimensiona a tela virtual (width x height) pro tamanho real da
        # janela só na hora de mostrar -- nenhuma coordenada de desenho
        # precisa mudar.
        scaled = pygame.transform.smoothscale(screen, (real_w, real_h))
        real_screen.blit(scaled, (0, 0))
        pygame.display.flip()

    return completed
