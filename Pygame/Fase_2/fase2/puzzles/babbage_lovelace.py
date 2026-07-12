"""
Este arquivo é o puzzle único da Fase 2 — Ligar a Máquina de Babbage com o
Programa de Ada.

Funde os dois puzzles antigos (engrenagens + cartões de Ada) numa mecânica
só: o jogador reordena os cartões de instrução de Ada Lovelace nos slots
numerados ao lado da Máquina Analítica de Babbage. Quando a ordem está
certa, a engrenagem da máquina liga e gira — representando o cálculo do
número de Bernoulli — e a fase se completa.

A máquina em si ainda é um placeholder (retângulo "MÁQUINA"), mas a
engrenagem já usa a arte real (gear_large.png), girada com
pygame.transform.rotate().

Este puzzle é chamado de dentro de fase2.py (função run() lá) quando o
jogador clica no papel/planta da parede depois de já ter juntado as 4
engrenagens escondidas pela oficina.

O retrato clicável da Ada Lovelace (ada_chatbot.AdaChat) também aparece
aqui, pra o jogador poder pedir dicas sem precisar fechar o puzzle -- é o
MESMO objeto AdaChat usado na oficina, só repassado como parâmetro (ver
`ada_chat` em run()), então a conversa continua a mesma se o jogador já
tinha perguntado algo antes de abrir o puzzle.

Cronômetro e estrelas: o puzzle tem um limite de 1 minuto (EstadoPuzzle,
logo abaixo) guardado num objeto criado uma única vez em fase2.py e
repassado por parâmetro pra run() -- mesmo padrão do `ada_chat`. Isso é o
que permite fechar a tela do puzzle (ESC/FECHAR) sem resolver e reabrir
depois retomando a MESMA tentativa (cartões já colocados e tempo restante
continuam de onde pararam, porque só decrementamos o tempo dentro do loop
de run(); tempo real passado com a tela fechada não conta). Se o tempo
zerar sem resolver, mostra uma tela de derrota com um botão "Tentar
novamente" que reembaralha os cartões, reseta o tempo e tira 1 estrela
(começando de 3, nunca fica negativa). Quando o jogador resolve com
sucesso, o número final de estrelas é salvo em Pygame/progresso.json (ver
`_salvar_progresso` mais abaixo) -- um arquivo compartilhado entre fases,
pra o mapa de fases do menu poder ler no futuro.
"""

import json
import os
import random

import pygame

from . import common

# Pasta assets/ da Fase 2 (mesma ideia do ASSETS_DIR em common.py).
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# ---------------------------------------------------------------------------
# Progresso compartilhado (Pygame/progresso.json)
# ---------------------------------------------------------------------------
# Fica na raiz de Pygame/ (quatro pastas acima deste arquivo: puzzles/ ->
# fase2/ -> Fase_2/ -> Pygame/), fora de qualquer fase específica, pra
# outras fases poderem ler (e escrever suas próprias chaves) no mesmo
# arquivo mais tarde -- por isso o formato é um dicionário por fase, em vez
# de um valor único.
_PYGAME_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROGRESSO_PATH = os.path.join(_PYGAME_DIR, "progresso.json")
PROGRESSO_CHAVE_FASE = "fase_2"


def _carregar_progresso():
    """Lê Pygame/progresso.json inteiro (de todas as fases). Devolve um
    dicionário vazio se o arquivo ainda não existir ou vier corrompido --
    assim a gente nunca trava tentando salvar só porque o arquivo está
    ausente ou malformado."""
    if not os.path.exists(PROGRESSO_PATH):
        return {}
    try:
        with open(PROGRESSO_PATH, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError):
        return {}


def _salvar_progresso(estrelas):
    """Grava `estrelas` (0 a 3) na chave PROGRESSO_CHAVE_FASE do
    progresso.json compartilhado, preservando as chaves de outras fases que
    já estiverem lá (lê tudo, atualiza só a nossa chave, escreve tudo de
    volta) -- assim colegas trabalhando em outras fases podem usar o mesmo
    arquivo sem um sobrescrever o progresso do outro."""
    progresso = _carregar_progresso()
    progresso[PROGRESSO_CHAVE_FASE] = {"estrelas": estrelas, "completo": True}
    with open(PROGRESSO_PATH, "w", encoding="utf-8") as arquivo:
        json.dump(progresso, arquivo, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Configurações do puzzle
# ---------------------------------------------------------------------------
# Cartões de instrução do "programa" de Ada — mesma lista/ordem correta que
# já existia em lovelace_cards.py. Lista simples, fácil de editar depois: a
# ORDEM em que aparecem aqui é a ordem "certa" que o jogador precisa montar.
CARDS = ["INICIAR", "SOMAR", "MULTIPLICAR", "REPETIR", "IMPRIMIR"]

# Tamanho de cada cartão (largura, altura) e o espaço entre eles, em pixels.
CARD_W, CARD_H = 150, 74
GAP = 16

MACHINE_GEAR_SIZE = 110
GEAR_SPIN_DEGREES_PER_FRAME = 2  # quantos graus a engrenagem gira a cada frame, depois de resolvido
SOLVE_HOLD_SECONDS = 2.0  # quanto tempo girando + "Máquina ligada!" antes de fechar e devolver completed=True
RESULT_NUMBER = "87"  # placeholder do número de Bernoulli "calculado"

# ---------------------------------------------------------------------------
# Configurações do cronômetro e da tela de derrota
# ---------------------------------------------------------------------------
TEMPO_LIMITE_SEGUNDOS = 60  # 1 minuto por tentativa
TEMPO_ALERTA_SEGUNDOS = 30  # últimos 30s: cronômetro fica vermelho
ESTRELAS_INICIAIS = 3

FALHA_TEXTO = (
    "Opa! O tempo acabou antes de você conseguir montar o programa de "
    "Ada Lovelace. Reorganize os cartões e tente novamente para ligar a "
    "Máquina Analítica!"
)
FALHA_RETRATO_DIAMETRO = 140
FALHA_LARGURA_BALAO = 480

# A engrenagem só é carregada de verdade dentro de _load_assets() (ver
# comentário parecido em fase2.py sobre por que isso não pode acontecer no
# import do módulo).
MACHINE_GEAR = None


def _load_assets():
    """Carrega a imagem da engrenagem grande, mas só na primeira vez que o
    puzzle rodar (se já carregou antes, `MACHINE_GEAR` deixa de ser None e a
    função não faz nada)."""
    global MACHINE_GEAR
    if MACHINE_GEAR is not None:
        return
    raw = pygame.image.load(os.path.join(ASSETS_DIR, "gear_large.png")).convert_alpha()
    MACHINE_GEAR = pygame.transform.scale(raw, (MACHINE_GEAR_SIZE, MACHINE_GEAR_SIZE))


def _shuffled_order():
    """Devolve uma lista com os índices de CARDS embaralhados (a ordem que o
    jogador vai VER os cartões disponíveis, não a ordem certa de resolver).

    Mesma lógica de lovelace_cards.py: sorteia com random.shuffle e repete o
    sorteio se, por azar, o resultado vier igual à ordem correta -- assim o
    puzzle nunca começa já resolvido sem querer.
    """
    order = list(range(len(CARDS)))
    while True:
        random.shuffle(order)
        if order != list(range(len(CARDS))):
            return order


def atualizar_engrenagem(angulo_atual):
    """Incrementa o ângulo de rotação da engrenagem (graus por frame).

    Recebe o ângulo atual (em graus) e devolve o próximo, sempre entre 0 e
    359 (o `% 360` "dá a volta" de novo pra 0 quando passa de 360, senão o
    ângulo cresceria pra sempre)."""
    return (angulo_atual + GEAR_SPIN_DEGREES_PER_FRAME) % 360


class EstadoPuzzle:
    """Guarda o progresso do puzzle entre reaberturas da tela (fechar sem
    resolver e reabrir continua a MESMA tentativa) e o número de estrelas
    da fase inteira.

    Criado uma única vez em fase2.py (mesmo padrão do `ada_chat`) e
    repassado por parâmetro pra run() -- assim, mesmo que o jogador feche o
    puzzle (ESC/FECHAR) e reabra depois clicando no papel de novo, os
    cartões já colocados e o tempo restante continuam de onde pararam, em
    vez de reembaralhar/reiniciar o cronômetro do zero.
    """

    def __init__(self):
        self.estrelas = ESTRELAS_INICIAIS
        self.reiniciar()

    def reiniciar(self):
        """Começa uma tentativa nova do zero: reembaralha os cartões e
        reseta o cronômetro pra TEMPO_LIMITE_SEGUNDOS. NÃO mexe em
        `self.estrelas` -- isso é só responsabilidade de `perder_estrela`,
        chamado quando o jogador clica "Tentar novamente" depois de uma
        derrota."""
        self.shuffled = _shuffled_order()
        self.placed = []
        self.tempo_restante = float(TEMPO_LIMITE_SEGUNDOS)

    def perder_estrela(self):
        """Tira 1 estrela (chamado a cada "Tentar novamente" depois de uma
        derrota) sem deixar o total ficar negativo."""
        self.estrelas = max(0, self.estrelas - 1)


def _quebrar_texto(texto, fonte, largura_maxima):
    """Quebra `texto` em linhas que cabem em `largura_maxima` pixels --
    mesma lógica usada em fase2._wrap_text e em ada_chatbot._quebrar_texto,
    copiada aqui (em vez de importada) pra este módulo não criar
    dependência de nenhum outro arquivo da Fase 2 além de `common`."""
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


def run(screen, clock, ada_chat, estado):
    """Roda o loop deste puzzle até o jogador fechar (ESC/botão FECHAR) ou
    resolver. Devolve True se resolveu (fase2.py usa isso pra saber se deve
    seguir com a transição pra sala da máquina do tempo), ou False se saiu
    sem resolver.

    `screen` e `clock` são os MESMOS objetos usados pelo loop principal da
    Fase 2 -- não criamos uma janela nova aqui, só "tomamos emprestado" a
    tela por um tempo e devolvemos o controle no final. `ada_chat` é o
    mesmo ada_chatbot.AdaChat já criado em fase2.py -- é só desenhado e
    tratado aqui também, pra o retrato da Ada continuar clicável durante
    o puzzle. `estado` é o EstadoPuzzle (também criado uma vez em
    fase2.py) que guarda os cartões já colocados, o tempo restante e as
    estrelas -- é o que permite fechar essa tela sem resolver e retomar a
    MESMA tentativa depois.
    """
    width, height = screen.get_size()
    common.init_fonts()
    _load_assets()

    # `estado.shuffled` é a ordem em que os cartões aparecem embaralhados
    # na "pool" (fileira de baixo); `estado.placed` guarda, na ordem em que
    # o jogador for clicando, quais cartões (pelo índice em CARDS) já foram
    # colocados nos slots de cima. O puzzle está resolvido quando
    # `estado.placed` ficar igual a [0, 1, 2, 3, 4] (a ordem original de
    # CARDS). Usamos `estado.X` direto (em vez de copiar pra uma variável
    # local) de propósito -- assim qualquer mudança aqui (placed.append,
    # estado.reiniciar()) já fica automaticamente refletida no objeto que
    # fase2.py continua segurando entre uma chamada de run() e outra.

    # --- geometria da máquina (placeholder) ---
    # Por enquanto a "máquina" é só um retângulo com a palavra MÁQUINA
    # escrita -- ainda não tem arte própria, só a engrenagem (gear_large.png)
    # que gira de verdade quando o puzzle é resolvido.
    machine_rect = pygame.Rect(width // 2 - 160, 110, 320, 150)
    gear_center = (machine_rect.centerx, machine_rect.top + 80)
    display_rect = pygame.Rect(machine_rect.centerx - 55, machine_rect.bottom + 12, 110, 34)

    # --- geometria dos cartões/slots ---
    # Calcula a largura total ocupada por todos os cartões enfileirados
    # (cada um com CARD_W de largura, mais o espaço GAP entre eles) pra
    # poder centralizar essa fileira inteira horizontalmente na tela.
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

    # --- geometria da tela de derrota (retrato + balão + botão) ---
    falha_retrato_center = (int(width * 0.24), int(height * 0.42))
    falha_balao_rect = pygame.Rect(int(width * 0.40), int(height * 0.22), FALHA_LARGURA_BALAO, int(height * 0.32))
    retry_btn = common.Button((width // 2 - 140, int(height * 0.62), 280, 50), "TENTAR NOVAMENTE (R)")

    gear_angle = 0.0
    solved = False  # true assim que os cartões estiverem na ordem certa
    solve_timer = 0.0  # conta quanto tempo já ficou "resolvido" (girando + "Máquina ligada!")
    completed = False  # valor final devolvido por essa função

    # Se o jogador já tinha perdido antes de fechar essa tela (tempo zerou
    # numa aberta anterior e ele saiu sem clicar "Tentar novamente"),
    # reabrir deve continuar mostrando a tela de derrota, não recomeçar a
    # contagem -- daí checar `estado.tempo_restante` logo de cara, e não só
    # inicializar `derrotado = False`.
    derrotado = estado.tempo_restante <= 0 and not solved

    running = True
    while running:
        # dt = tempo (em segundos) que passou desde o frame anterior --
        # usado pra contar o solve_timer/tempo_restante de forma
        # consistente, independente da velocidade real do computador (em
        # vez de simplesmente somar 1 a cada frame, o que ia depender do
        # FPS).
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
        retry_btn.update_hover(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            elif event.type == pygame.KEYDOWN:
                if ada_chat.aberta:
                    # Com a conversa aberta, todo o teclado (inclusive ESC)
                    # é dela -- ESC fecha só a caixinha, não o puzzle.
                    ada_chat.tratar_evento_teclado(event)
                elif derrotado and event.key == pygame.K_r:
                    # Atalho de teclado pro botão "Tentar novamente" --
                    # mesma ação de clicar nele (ver mais abaixo).
                    estado.perder_estrela()
                    estado.reiniciar()
                    derrotado = False
                elif event.key == pygame.K_ESCAPE and not solved:
                    # só deixa sair com ESC se AINDA não resolveu -- depois de
                    # resolvido, o puzzle fecha sozinho (ver o "if solved"
                    # logo abaixo), então não faz sentido também sair na mão.
                    running = False
            elif event.type == pygame.MOUSEWHEEL and ada_chat.aberta:
                # Rola o texto da resposta da Ada -- mesma lógica da cena
                # principal da oficina (fase2.py).
                ada_chat.tratar_evento_scroll(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and derrotado:
                # Na tela de derrota só o botão de reiniciar reage a
                # clique -- os cartões/slots nem são desenhados aqui, então
                # não faz sentido checar clique neles.
                if retry_btn.clicked(mouse_pos, event):
                    estado.perder_estrela()
                    estado.reiniciar()
                    derrotado = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not solved and not ada_chat.aberta:
                if ada_chat.tratar_clique_no_icone(mouse_pos):
                    continue

                if close_btn.clicked(mouse_pos, event):
                    running = False
                    continue

                # Primeiro tenta ver se o clique foi num cartão ainda
                # disponível na fileira de baixo (a "pool") -- se foi, esse
                # cartão vai pro próximo slot livre (o final da lista
                # `estado.placed`, já que cartões são sempre adicionados em
                # ordem).
                clicked_pool = False
                if len(estado.placed) < len(CARDS):
                    for i, card_i in enumerate(estado.shuffled):
                        if card_i in estado.placed:
                            continue
                        if pool_rects[i].collidepoint(mouse_pos):
                            estado.placed.append(card_i)
                            clicked_pool = True
                            break

                if not clicked_pool:
                    # Se não clicou em nenhum cartão da pool, tenta ver se
                    # clicou num slot JÁ preenchido -- nesse caso, remove
                    # aquele cartão de volta pra pool (sem penalidade, o
                    # jogador pode tentar de novo à vontade).
                    for slot_i, rect in enumerate(slot_rects):
                        if slot_i < len(estado.placed) and rect.collidepoint(mouse_pos):
                            estado.placed.pop(slot_i)
                            break

        # O puzzle está resolvido quando os cartões foram colocados
        # EXATAMENTE na ordem original de CARDS (0, 1, 2, 3, 4...) -- ou
        # seja, o jogador acertou a sequência certa do "programa" de Ada.
        if not solved and not derrotado and estado.placed == list(range(len(CARDS))):
            solved = True
            print("Puzzle resolvido: máquina de Babbage programada com sucesso!")

        # Cronômetro: só conta enquanto ainda está jogando (nem resolvido
        # nem já em tela de derrota) -- por isso decrementar tempo_restante
        # só acontece aqui dentro do loop, nunca entre uma chamada de run()
        # e outra. É exatamente isso que faz o cronômetro "pausar" quando o
        # jogador fecha a tela do puzzle sem resolver.
        if not solved and not derrotado:
            estado.tempo_restante = max(0.0, estado.tempo_restante - dt)
            if estado.tempo_restante <= 0:
                derrotado = True

        if solved:
            # Depois de resolvido, a engrenagem fica girando (só efeito
            # visual) por SOLVE_HOLD_SECONDS segundos com a mensagem
            # "Máquina ligada! Calculando...", antes de fechar e devolver
            # completed=True. A mensagem de vitória ("Você concluiu,
            # parabéns!") não aparece mais aqui -- fase2.py agora mostra
            # ela sobreposta à sala da máquina do tempo, logo no início da
            # transição pra lá.
            solve_timer += dt
            gear_angle = atualizar_engrenagem(gear_angle)
            if solve_timer >= SOLVE_HOLD_SECONDS:
                # Salva o resultado final (estrelas) só aqui, no momento
                # exato em que a fase é dada como concluída com sucesso.
                _salvar_progresso(estado.estrelas)
                completed = True
                running = False

        # --- a partir daqui é só desenho: fundo + máquina + cartões ---
        common.draw_frame(
            screen, width, height,
            "LIGUE A MÁQUINA DE BABBAGE",
            "Monte o programa de Ada Lovelace nos slots para ligar a máquina",
        )

        if derrotado:
            # --- tela de derrota: retrato da Ada + balão + botão ---
            tela_retrato = pygame.transform.smoothscale(ada_chat.retrato_grande, (FALHA_RETRATO_DIAMETRO, FALHA_RETRATO_DIAMETRO))
            screen.blit(tela_retrato, tela_retrato.get_rect(center=falha_retrato_center))

            common.nine_slice(screen, common.SMALL_PANEL, falha_balao_rect, common.SMALL_PANEL_BORDER)
            linhas = _quebrar_texto(FALHA_TEXTO, common.FONT_SMALL, falha_balao_rect.width - 60)
            linha_h = common.FONT_SMALL.get_height() + 6
            texto_top = falha_balao_rect.centery - (len(linhas) * linha_h) // 2
            for i, linha in enumerate(linhas):
                linha_surf = common.FONT_SMALL.render(linha, True, common.CREAM)
                screen.blit(linha_surf, linha_surf.get_rect(midtop=(falha_balao_rect.centerx, texto_top + i * linha_h)))

            retry_btn.draw(screen)
        else:
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
                if slot_i < len(estado.placed):
                    card_surf = common.FONT_MED.render(CARDS[estado.placed[slot_i]], True, common.CREAM)
                    screen.blit(card_surf, card_surf.get_rect(center=(rect.centerx, rect.centery + 12)))

            # --- cartões ainda não usados ---
            for i, card_i in enumerate(estado.shuffled):
                if card_i in estado.placed:
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

            # Retrato/chat da Ada -- desenhado por cima de tudo, igual na
            # oficina, pra o jogador poder pedir dica sem sair do puzzle.
            # Não aparece na tela de derrota (foco no retrato grande e no
            # botão de tentar de novo).
            ada_chat.desenhar(screen, mouse_pos)

        # --- cronômetro (canto superior direito) ---
        minutos = int(estado.tempo_restante) // 60
        segundos = int(estado.tempo_restante) % 60
        cor_tempo = common.RED if estado.tempo_restante <= TEMPO_ALERTA_SEGUNDOS else common.GOLD
        tempo_surf = common.FONT_MED.render(f"{minutos:02d}:{segundos:02d}", True, cor_tempo)
        screen.blit(tempo_surf, tempo_surf.get_rect(topright=(width - 50, 44)))

        # redimensiona a tela virtual pro tamanho real da janela só na hora
        # de mostrar -- nenhuma coordenada de desenho precisa mudar.
        scaled = pygame.transform.smoothscale(screen, (real_w, real_h))
        real_screen.blit(scaled, (0, 0))
        pygame.display.flip()

    # completed só vira True lá em cima, quando o cronômetro pós-solução
    # (solve_timer) termina -- se o jogador saiu antes com ESC/FECHAR,
    # continua False.
    return completed
