"""
Fase 2 — As Máquinas Mecânicas (1800-1840)

A cena é a oficina de Babbage. O jogador anda com WASD/setas ou clique do
mouse e precisa achar os 4 pontos de coleta escondidos pela sala (baú, pote
e caixote, que abrem ao clicar, mais uma engrenagem escondida num dos
desenhos já ilustrados no papel/planta da parede) para juntar uma
engrenagem de cada um. Depois de coletar as 4, a planta libera o puzzle
"ligar a máquina" (babbage_lovelace.py) — resolvê-lo conclui a fase.

`run()` reutiliza a mesma janela/clock do jogo principal. Devolve `True` se
o jogador concluiu o puzzle, ou `False` se saiu antes apertando ESC.
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

# Colisão da cena: faixa de chão andável (o resto é parede/janela, onde o
# personagem não deve conseguir pisar) e a bancada central, bloqueada por
# inteiro (tampo + pernas) como um único retângulo.
FLOOR_RECT = pygame.Rect(20, 400, 960, 230)
TABLE_RECT = pygame.Rect(160, 355, 380, 175)

# As imagens só podem passar por .convert()/.convert_alpha() depois que a
# janela existir (pygame.display.set_mode()). Como menu/jogo.py importa este
# módulo antes de criar a janela, o carregamento é adiado para _load_assets(),
# chamado no início de run() — mesmo padrão de common.init_fonts().
BACKGROUND = None
GEAR_SMALL = None
GEAR_SMALL_HOVER = None
GEAR_LARGE = None  # reservada para uso futuro — ainda não é desenhada na cena.
CLOSED_SPRITES = {}
OPEN_SPRITES = {}


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


def _load_assets():
    global BACKGROUND, GEAR_SMALL, GEAR_SMALL_HOVER, GEAR_LARGE
    if BACKGROUND is not None:
        return

    bg_raw = pygame.image.load(os.path.join(ASSETS_DIR, "background_oficina.png")).convert()
    BACKGROUND = pygame.transform.smoothscale(bg_raw, (1000, 650))

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


def _position_allowed(pos):
    """True se o personagem pode ficar nessa posição: dentro do chão
    andável e fora da área bloqueada da bancada."""
    x, y = pos.x, pos.y
    if not (FLOOR_RECT.left + PLAYER_RADIUS <= x <= FLOOR_RECT.right - PLAYER_RADIUS):
        return False
    if not (FLOOR_RECT.top + PLAYER_RADIUS <= y <= FLOOR_RECT.bottom - PLAYER_RADIUS):
        return False
    blocked = TABLE_RECT.inflate(PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
    if blocked.collidepoint(x, y):
        return False
    return True


def _try_move(pos, delta):
    """Aplica um deslocamento, deslizando ao longo de paredes/obstáculos em
    vez de travar (tenta o movimento completo, depois só X, depois só Y)."""
    full = pygame.Vector2(pos.x + delta.x, pos.y + delta.y)
    if _position_allowed(full):
        return full, True
    only_x = pygame.Vector2(pos.x + delta.x, pos.y)
    if _position_allowed(only_x):
        return only_x, True
    only_y = pygame.Vector2(pos.x, pos.y + delta.y)
    if _position_allowed(only_y):
        return only_y, True
    return pos, False


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

    container_open = {c["key"]: False for c in CONTAINERS}
    collected = {c["key"]: False for c in CONTAINERS}
    collected[PAPER_GEAR_KEY] = False
    total_gears = len(CONTAINERS) + 1

    player_pos = pygame.Vector2(750, 500)  # chão aberto à direita da bancada
    click_target = None

    hint_msg = ""
    hint_timer = 0.0
    paper_gear_flash_timer = 0.0
    completed = False

    running = True
    while running:
        dt = clock.tick(60) / 1000
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_something = False

                for c in CONTAINERS:
                    key = c["key"]
                    is_open = container_open[key]
                    sprite = OPEN_SPRITES[key] if is_open else CLOSED_SPRITES[key]
                    rect = sprite.get_rect(center=c["pos"])

                    if not is_open:
                        if rect.collidepoint(event.pos):
                            container_open[key] = True
                            clicked_something = True
                            break
                    elif not collected[key]:
                        gx, gy = c["pos"]
                        if math.hypot(event.pos[0] - gx, event.pos[1] - gy) <= GEAR_HOVER_RADIUS:
                            collected[key] = True
                            clicked_something = True
                            break

                if (
                    not clicked_something
                    and not collected[PAPER_GEAR_KEY]
                    and PAPER_GEAR_RECT.collidepoint(event.pos)
                ):
                    collected[PAPER_GEAR_KEY] = True
                    paper_gear_flash_timer = PAPER_GEAR_FLASH_SECONDS
                    clicked_something = True

                if not clicked_something and PAPER_RECT.collidepoint(event.pos):
                    clicked_something = True
                    if all(collected.values()):
                        if babbage_lovelace.run(screen, clock):
                            completed = True
                            running = False
                    else:
                        hint_msg = "Ainda faltam engrenagens para juntar."
                        hint_timer = 2.0

                if not clicked_something:
                    click_target = pygame.Vector2(event.pos)

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
            player_pos, _ = _try_move(player_pos, move.normalize() * PLAYER_SPEED * dt)
        elif click_target is not None:
            direction = click_target - player_pos
            dist = direction.length()
            if dist <= CLICK_ARRIVE_DIST:
                click_target = None
            else:
                step = min(PLAYER_SPEED * dt, dist)
                player_pos, moved = _try_move(player_pos, direction.normalize() * step)
                if not moved:
                    click_target = None  # caminho bloqueado (ex.: outro lado da bancada)

        # --- desenho ---
        screen.blit(BACKGROUND, (0, 0))

        title_surf = title_font.render(TITLE, True, GOLD)
        screen.blit(title_surf, title_surf.get_rect(midtop=(width // 2, margin + 8)))
        subtitle_surf = subtitle_font.render(SUBTITLE, True, CREAM)
        screen.blit(subtitle_surf, subtitle_surf.get_rect(midtop=(width // 2, margin + 46)))

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
        # desenho em si nunca muda, só o brilho dourado (hover, e um flash
        # rápido no momento da coleta).
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

        # papel / planta na parede — PAPER_RECT só existe para detecção de
        # clique (collidepoint); nada é desenhado sobre a arte de fundo.
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

        hint_surf2 = hint_font.render(HINT, True, CREAM)
        screen.blit(hint_surf2, hint_surf2.get_rect(midbottom=(width // 2, height - margin - 6)))

        pygame.display.flip()

    return completed
