"""
Puzzle único da Fase 2 — Ligar a Máquina de Babbage com o Programa de Ada.

Funde os dois puzzles antigos (engrenagens + cartões de Ada) numa mecânica
só: o jogador reordena os cartões de instrução de Ada Lovelace nos slots
numerados ao lado da Máquina Analítica de Babbage. Quando a ordem está
certa, a engrenagem da máquina liga e gira — representando o cálculo do
número de Bernoulli — e a fase se completa.

A máquina em si ainda é um placeholder (retângulo "MÁQUINA"), mas a
engrenagem já usa a arte real (gear_large.png), girada com
pygame.transform.rotate().
"""

import os
import random

import pygame

from . import common

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# Cartões de instrução do "programa" de Ada — mesma lista/ordem correta que
# já existia em lovelace_cards.py. Lista simples, fácil de editar depois.
CARDS = ["INICIAR", "SOMAR", "MULTIPLICAR", "REPETIR", "IMPRIMIR"]

CARD_W, CARD_H = 150, 74
GAP = 16

MACHINE_GEAR_SIZE = 110
GEAR_SPIN_DEGREES_PER_FRAME = 2
SOLVE_HOLD_SECONDS = 2.0
RESULT_NUMBER = "87"  # placeholder do número de Bernoulli "calculado"

MACHINE_GEAR = None


def _load_assets():
    global MACHINE_GEAR
    if MACHINE_GEAR is not None:
        return
    raw = pygame.image.load(os.path.join(ASSETS_DIR, "gear_large.png")).convert_alpha()
    MACHINE_GEAR = pygame.transform.scale(raw, (MACHINE_GEAR_SIZE, MACHINE_GEAR_SIZE))


def _shuffled_order():
    # Mesma lógica de lovelace_cards.py: embaralha os índices dos cartões
    # garantindo que não comece já na ordem correta.
    order = list(range(len(CARDS)))
    while True:
        random.shuffle(order)
        if order != list(range(len(CARDS))):
            return order


def atualizar_engrenagem(angulo_atual):
    """Incrementa o ângulo de rotação da engrenagem (graus por frame)."""
    return (angulo_atual + GEAR_SPIN_DEGREES_PER_FRAME) % 360


def run(screen, clock):
    width, height = screen.get_size()
    common.init_fonts()
    _load_assets()

    shuffled = _shuffled_order()
    placed = []  # índices (em CARDS) já colocados nos slots, na ordem escolhida

    # --- geometria da máquina (placeholder) ---
    machine_rect = pygame.Rect(width // 2 - 160, 110, 320, 150)
    gear_center = (machine_rect.centerx, machine_rect.top + 80)
    display_rect = pygame.Rect(machine_rect.centerx - 55, machine_rect.bottom + 12, 110, 34)

    # --- geometria dos cartões/slots ---
    total_w = len(CARDS) * CARD_W + (len(CARDS) - 1) * GAP
    start_x = width // 2 - total_w // 2

    slot_rects = [
        pygame.Rect(start_x + i * (CARD_W + GAP), 320, CARD_W, CARD_H)
        for i in range(len(CARDS))
    ]
    pool_rects = [
        pygame.Rect(start_x + i * (CARD_W + GAP), 410, CARD_W, CARD_H)
        for i in range(len(CARDS))
    ]

    close_btn = common.Button((width // 2 - 95, 505, 190, 46), "FECHAR")

    gear_angle = 0.0
    solved = False
    solve_timer = 0.0
    completed = False

    running = True
    while running:
        dt = clock.tick(60) / 1000

        # a janela real pode ser menor que a tela virtual (width x height,
        # o espaço em que todas as coordenadas deste puzzle já são
        # calculadas) -- converte o mouse de volta pra cá antes de checar
        # qualquer colisão.
        real_screen = pygame.display.get_surface()
        real_w, real_h = real_screen.get_size()
        raw_mouse = pygame.mouse.get_pos()
        mouse_pos = (raw_mouse[0] * width / real_w, raw_mouse[1] * height / real_h)
        close_btn.update_hover(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not solved:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not solved:
                if close_btn.clicked(mouse_pos, event):
                    running = False
                    continue

                # clique num cartão ainda não colocado -> vai pro próximo slot livre
                clicked_pool = False
                if len(placed) < len(CARDS):
                    for i, card_i in enumerate(shuffled):
                        if card_i in placed:
                            continue
                        if pool_rects[i].collidepoint(mouse_pos):
                            placed.append(card_i)
                            clicked_pool = True
                            break

                if not clicked_pool:
                    # clique num slot já preenchido -> remove esse cartão (sem penalidade)
                    for slot_i, rect in enumerate(slot_rects):
                        if slot_i < len(placed) and rect.collidepoint(mouse_pos):
                            placed.pop(slot_i)
                            break

        if not solved and placed == list(range(len(CARDS))):
            solved = True
            print("Puzzle resolvido: máquina de Babbage programada com sucesso!")

        if solved:
            solve_timer += dt
            gear_angle = atualizar_engrenagem(gear_angle)
            if solve_timer >= SOLVE_HOLD_SECONDS:
                completed = True
                running = False

        common.draw_frame(
            screen, width, height,
            "LIGUE A MÁQUINA DE BABBAGE",
            "Monte o programa de Ada Lovelace nos slots para ligar a máquina",
        )

        # --- máquina (placeholder) ---
        pygame.draw.rect(screen, common.PANEL_COLOR, machine_rect, border_radius=10)
        pygame.draw.rect(
            screen, common.GOLD if solved else common.GOLD_DIM, machine_rect, width=2, border_radius=10
        )
        label_surf = common.FONT_MED.render("MÁQUINA", True, common.WHITE)
        screen.blit(label_surf, label_surf.get_rect(midtop=(machine_rect.centerx, machine_rect.top + 10)))

        rotated_gear = pygame.transform.rotate(MACHINE_GEAR, gear_angle)
        screen.blit(rotated_gear, rotated_gear.get_rect(center=gear_center))

        pygame.draw.rect(screen, common.PANEL_COLOR, display_rect, border_radius=6)
        pygame.draw.rect(
            screen, common.GOLD if solved else common.GOLD_DIM, display_rect, width=2, border_radius=6
        )
        display_text = RESULT_NUMBER if solved else "??"
        display_color = common.OLIVE if solved else common.CREAM
        display_surf = common.FONT_BIG.render(display_text, True, display_color)
        screen.blit(display_surf, display_surf.get_rect(center=display_rect.center))

        # --- slots numerados ---
        for slot_i, rect in enumerate(slot_rects):
            common.nine_slice(screen, common.SMALL_PANEL, rect, common.SMALL_PANEL_BORDER)
            num_surf = common.FONT_SMALL.render(f"slot {slot_i + 1}", True, common.CREAM)
            screen.blit(num_surf, num_surf.get_rect(midtop=(rect.centerx, rect.top + 6)))
            if slot_i < len(placed):
                card_surf = common.FONT_MED.render(CARDS[placed[slot_i]], True, common.CREAM)
                screen.blit(card_surf, card_surf.get_rect(center=(rect.centerx, rect.centery + 12)))

        # --- cartões ainda não usados ---
        for i, card_i in enumerate(shuffled):
            if card_i in placed:
                continue
            rect = pool_rects[i]
            common.nine_slice(screen, common.SMALL_PANEL, rect, common.SMALL_PANEL_BORDER)
            card_surf = common.FONT_MED.render(CARDS[card_i], True, common.WHITE)
            screen.blit(card_surf, card_surf.get_rect(center=rect.center))

        if solved:
            common.draw_feedback(screen, width, height, "Máquina ligada! Calculando...", True)
        else:
            hint = common.FONT_SMALL.render(common.ESC_HINT, True, common.CREAM)
            screen.blit(hint, (30, height - 40))
            close_btn.draw(screen)

        # redimensiona a tela virtual pro tamanho real da janela só na hora
        # de mostrar -- nenhuma coordenada de desenho precisa mudar.
        scaled = pygame.transform.smoothscale(screen, (real_w, real_h))
        real_screen.blit(scaled, (0, 0))
        pygame.display.flip()

    return completed
