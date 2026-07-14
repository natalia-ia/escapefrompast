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
numa área de trabalho colorida, uma sequência de vitória leva o
personagem pra uma sala separada com a máquina do tempo (mesmo
espírito da Fase 2) e a fase termina ao clicar nela.

ESTRUTURA DO JOGO (máquina de estados)
----------------------------------------------------------------------
QUARTO      -> cena principal: o quarto retrô (assets/imagens/cenario_
               fase_9.png) onde o jogador anda com WASD/setas e pode
               clicar no computador em cima da escrivaninha para
               começar o puzzle. O jogador começa aqui.
TERMINAL    -> o puzzle de verdade (3 etapas encadeadas: ação + alvo,
               uma etapa alimenta a pista da próxima) -- implementado
               em puzzle_terminal.py, chamado direto no clique do
               computador (mesmo padrão de fase2.py chamando
               babbage_lovelace.run()). Ao concluir, a própria função
               já faz a tela "acender" (efeito simples de transição)
               e devolve True -- ver Jogo._iniciar_sequencia_de_vitoria.
SALA_FINAL  -> sala separada (assets/imagens/cena_final.png), só com a
               máquina do tempo (assets/imagens/maquina_do_tempo_v4.png,
               mesmo asset da Fase 2): o personagem entra pela esquerda,
               anda sozinho até perto da máquina (mesma lógica de
               fase2.Jogador.mover_para) e, ao chegar, o jogador
               recupera o controle e só precisa clicar nela pra
               terminar a fase.
               # TODO: quando a Fase 10 existir (a combinar com o
               grupo), conectar a saída da máquina do tempo a ela pelo
               menu -- por enquanto só encerra a fase (ver
               Jogo.executar()).

Este arquivo monta a cena/estados da fase; a lógica do puzzle em si
mora em puzzle_terminal.py (dados do puzzle separados da lógica, ver
ETAPAS lá). SEM INVENTÁRIO -- esta fase não tem coleta de objetos no
cenário (diferente da Fase_4, que tem).

Requisitos: pip install pygame
Execução:   python fase9.py
=====================================================================
"""

import math
import os

import pygame

from npc_chatbot import NPCChatbot
import puzzle_terminal
from estilo_crt import COR_FUNDO_CRT, COR_AMBAR, COR_AMBAR_DIM, COR_AMBAR_BRILHO, render_texto_glow, desenhar_scanlines
import audio_fase9
import config_fase9

# PROPOSITALMENTE sem nenhuma chamada de "DPI awareness" aqui: testado ao
# vivo (clique físico simulado via API do Windows) e confirmado que, sem
# ela, o Windows já converte a posição do mouse pra a mesma escala
# "virtual" 960x600 que o resto do código usa -- é assim que TODAS as
# outras fases (Fase_2, Fase_4, menu) já funcionam, nenhuma delas marca
# o processo como DPI aware. Uma versão anterior desta fase chamava
# SetProcessDpiAwarenessContext aqui, achando que isso evitava um bug de
# clique -- na prática, o efeito real foi só deixar a janela desta fase
# com um tamanho FÍSICO diferente das outras (crua/sem escala do Windows,
# enquanto as demais são escaladas), quebrando o padrão "mesma resolução
# visual em todas as fases" combinado com o grupo.
# =====================================================================
# 1. CONFIGURAÇÕES GERAIS DA JANELA E DO JOGO
# =====================================================================
LARGURA, ALTURA = 960, 600  # mesma resolução da janela usada nas outras fases
FPS = 60

PRETO = (15, 15, 15)
VERDE_TERMINAL = (60, 220, 100)  # texto/cursor estilo monitor de fósforo verde
BRANCO = (245, 245, 240)
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

PLAYER_RADIUS = 27  # crescido junto com AVATAR_ALTURA (mesma proporção), pra manter a mesma folga relativa entre o sprite maior e as paredes -- mesma margem de colisão usada em fase2.py

# Distância (em pixels) que já conta como "chegou" no alvo de uma
# caminhada automática -- mesmo valor/papel de fase2.CLICK_ARRIVE_DIST,
# usado só por Jogador.mover_para() (caminhada sozinha até a máquina do
# tempo, na sala final).
CLICK_ARRIVE_DIST = 4

# ---------------------------------------------------------------------------
# Sala final (SALA_FINAL) -- só existe depois que o puzzle é resolvido: uma
# sala separada, com a máquina do tempo, no mesmo espírito da sala da
# máquina do tempo de Pygame/Fase_2/fase2/fase2.py (MACHINE_ROOM_*/
# TIME_MACHINE_*): o personagem entra pela lateral esquerda do chão livre e
# anda sozinho até perto da máquina; o jogador só recupera o controle
# depois que ele chegar lá (ver Jogo._iniciar_sequencia_de_vitoria/
# Jogo.executar()).
# ---------------------------------------------------------------------------
# Medidos direto em cima de assets/imagens/cena_final.png (1586x992, depois
# escalado pra LARGURA x ALTURA): a faixa central da sala tem chão de
# madeira livre; as bancadas com computadores retrô ficam nas duas
# laterais, fora deste retângulo (por isso o personagem "entra" já dentro
# da faixa livre, não na borda esquerda da tela).
SALA_FINAL_FLOOR_RECT = pygame.Rect(230, 350, 560, 245)
SALA_FINAL_ENTRY_POS = (262, 560)  # pés na borda esquerda do chão livre, como se tivesse acabado de entrar -- ajustado (255->262) junto com o aumento de PLAYER_RADIUS, pra continuar dentro da margem permitida por _posicao_permitida (senão o personagem nasceria fora do chão andável e ficaria preso sem conseguir andar de lado)

# Máquina do tempo ENCOSTADA na parede do fundo (não solta no meio do
# chão): MAQUINA_TEMPO_POS é a BASE dela (não o centro -- ver
# get_rect(midbottom=...) mais abaixo), fixada bem em cima da linha onde
# a textura de chão de madeira (com as tábuas visíveis) realmente começa
# nesta imagem (~y=335 -- medido direto em cima de cena_final.png já
# escalada pra 960x600; a faixa acima disso, até uns y=300, ainda é
# parede/rodapé, não chão). Ancorar pela BASE (em vez do centro) garante
# que aumentar MAQUINA_TEMPO_ALTURA só faz ela crescer PRA CIMA, sem
# nunca voltar a flutuar.
#
# A altura (280) é um pouco MAIOR que o personagem (AVATAR_ALTURA=270)
# -- imponente, já que é uma máquina em que a pessoa entra dentro -- mas
# sem passar do cano/tubulação que corre horizontalmente perto do teto
# desta sala (~y=65 em cima da mesma imagem escalada): 280 foi o maior
# valor testado que ainda deixa uma folga visível abaixo do cano (300+
# já esbarra nele) -- ver o comentário de MAQUINA_TEMPO_CHEGADA_POS.
MAQUINA_TEMPO_ALTURA = 280
MAQUINA_TEMPO_POS = (480, 335)  # base (não centro) do trecho vazio da parede
# Onde os pés do personagem param na caminhada automática: em frente à
# máquina. Não dá pra ficar 100% sem sobrepor (a máquina agora ocupa boa
# parte da faixa de chão vertical disponível) sem esbarrar na dica
# MACHINE_HINT colada no rodapé -- por isso um pequeno overlap entre o
# topo da cabeça do personagem e a base da máquina é aceitável aqui
# (mesmo efeito de estar bem em pé na frente/embaixo dela).
MAQUINA_TEMPO_CHEGADA_POS = (480, 540)

MENSAGEM_VITORIA = "Você concluiu, parabéns!"
MENSAGEM_VITORIA_SEGUNDOS = 2.0  # mesmo valor de fase2.MENSAGEM_VITORIA_SEGUNDOS
MACHINE_HINT = "Entre na máquina do tempo para ir para a próxima fase!"
FADE_DURATION_SECONDS = 0.35  # mesmo valor de fase2.FADE_DURATION_SECONDS

# Segunda verificação do código de ativação, agora na sala da máquina --
# o mesmo código do desktop_final (XK47), só que INVERTIDO, pra exigir
# que o jogador perceba a inversão em vez de só copiar o que já achou.
CODIGO_MAQUINA_CORRETO = "74KX"
INSTRUCAO_CODIGO_MAQUINA = "Digite o código de ativação da máquina (dica: inverta a sequência):"
MSG_CODIGO_MAQUINA_ERRO = "Código inválido."
MSG_CODIGO_MAQUINA_OK = "Código aceito! A máquina está pronta -- clique nela para entrar."


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
    # obrigatório ainda -- a tela de terminal é desenhada só com texto,
    # e o desktop reconstruído (mostrado ao resolver o puzzle) usa o
    # desenho estilizado de puzzle_terminal.desenhar_desktop_retro (sem
    # imagem própria).
    "sprite_npc": caminho_asset("assets/imagens/system_ai.png"),
    "fonte_terminal": caminho_asset("assets/imagens/fonte_terminal.ttf"),
    # TODO: som de "bipe" do terminal / efeito de "ligar" o monitor ao
    # entrar no desktop, por exemplo:
    # "som_beep": caminho_asset("assets/sons/beep.wav"),
}

# Cenário do quarto (fundo da cena QUARTO).
CENARIO_QUARTO_PATH = caminho_asset("assets/imagens/cenario_fase_9.png")

# Cenário e máquina do tempo da sala final (fundo da cena SALA_FINAL) --
# maquina_do_tempo_v4.png é o MESMO asset usado em
# Pygame/Fase_2/fase2/assets/maquina_do_tempo_v4.png (copiado pra esta
# pasta, já que cada fase deste repositório mantém seus próprios assets).
CENA_FINAL_PATH = caminho_asset("assets/imagens/cena_final.png")
MAQUINA_TEMPO_PATH = caminho_asset("assets/imagens/maquina_do_tempo_v4.png")

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
AVATAR_ALTURA = 270  # mesma escala (altura em pixels) usada em fase2.py


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

    def mover_para(self, alvo, floor_rect):
        """Anda sozinho em direção a um ponto fixo (`alvo`), ignorando o
        teclado -- mesma lógica/animação de fase2.Jogador.mover_para(),
        usada só na caminhada automática até a máquina do tempo, na sala
        final (ver Jogo.executar()). Devolve True quando chega perto o
        bastante do alvo (ou desiste, se bater num obstáculo e não
        conseguir se mexer mais)."""
        direcao = pygame.Vector2(alvo) - self.pos
        dist = direcao.length()
        chegou = dist <= CLICK_ARRIVE_DIST

        if not chegou:
            passo = min(self.VELOCIDADE, dist)
            nova_pos = _tentar_mover(self.pos, direcao.normalize() * passo, floor_rect)
            if nova_pos == self.pos:
                # Bateu num obstáculo e não conseguiu se mexer nem um
                # pouco -- desiste de perseguir esse alvo em vez de
                # tentar pra sempre no mesmo lugar (mesma regra da Fase 2).
                chegou = True
            else:
                self.pos = nova_pos

        self._atualizar_sprite(not chegou)
        if not chegou and direcao.x < 0:
            self.imagem = pygame.transform.flip(self.imagem, True, False)

        return chegou

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
# um texto que restringe a IA ao tema da fase. NUNCA entrega a resposta
# do puzzle (ação/alvo certos ou a ordem WIMP) -- só aponta a direção,
# pra não estragar a dedução que puzzle_terminal.py foi desenhado pra
# exigir (ver ETAPAS_COMANDO/WIMP_ELEMENTOS lá).
CONTEXTO_SYSTEM_AI = (
    "Você é o SYSTEM_AI, um assistente de sistema operacional de um "
    "computador pessoal dos anos 1980. Seu tom é seco, direto e "
    "técnico, como um terminal antigo -- nada de saudações longas, "
    "emojis ou enrolação. Respostas curtas (no máximo 3 frases).\n\n"
    "CONTEXTO DA CENA: o usuário está reconstruindo a passagem da linha "
    "de comando para a interface gráfica. Ele precisa completar 3 "
    "etapas: (1) e (2) são comandos de terminal, (3) é ativar os "
    "elementos da interface gráfica (janela, ícone, menu, ponteiro).\n\n"
    "REGRAS DE AJUDA (MUITO IMPORTANTE):\n"
    "- Você NUNCA dá a resposta exata. Nunca diga o comando certo, o "
    "alvo certo, nem a ordem exata dos elementos. Você apenas APONTA A "
    "DIREÇÃO e faz o usuário raciocinar.\n"
    "- Se perguntarem direto a resposta, recuse e devolva uma dica que "
    "force o raciocínio.\n"
    "- Ex. de dica válida: \"Pense no que precisa existir ANTES. Não há "
    "menu flutuando sem algo que o contenha.\" (aponta, não entrega)\n"
    "- Prefira dicas conceituais e históricas a instruções diretas.\n\n"
    "FATOS HISTÓRICOS (você SÓ pode afirmar estes; se não souber, diga "
    "que não tem o dado -- NUNCA invente datas ou nomes):\n"
    "- A interface gráfica (janelas, ícones, menus, mouse) foi "
    "inventada no Xerox PARC nos anos 1970 (computadores Xerox Alto e "
    "depois Xerox Star).\n"
    "- A Xerox criou a tecnologia, mas não a transformou em sucesso "
    "comercial.\n"
    "- A Apple popularizou a interface gráfica com o Macintosh, "
    "lançado em 1984.\n"
    "- A Microsoft lançou o Windows em 1985.\n"
    "- Antes disso, os computadores eram usados por linha de comando "
    "(texto digitado).\n\n"
    "PROIBIÇÕES:\n"
    "- NÃO invente fatos, datas, nomes de produtos ou versões. Se não "
    "estiver na lista acima, você não afirma.\n"
    "- NÃO fale de assuntos fora deste contexto (computação pessoal "
    "dos anos 1975-1990 e o puzzle). Se perguntarem outra coisa, diga "
    "que está fora do seu escopo.\n"
    "- Responda SEMPRE em português do Brasil.\n\n"
    # Exemplos few-shot -- testado ao vivo com qwen2.5:0.5b e confirmado
    # que as regras acima SOZINHAS (só em prosa) não bastam: o modelo
    # entregava a resposta do puzzle e respondia perguntas fora de
    # escopo mesmo com a proibição escrita. Os exemplos concretos abaixo
    # (mesmo padrão que resolveu isso na Ada, na Fase 2 -- ver
    # PROMPT_SISTEMA_ADA em Pygame/Fase_2/fase2/puzzles/ada_chatbot.py)
    # são o que faz a recusa/redirecionamento acontecer de verdade.
    "EXEMPLOS:\n\n"
    "Pergunta: Qual é o comando certo da primeira etapa? Me diz a resposta exata.\n"
    "Resposta: Não entrego respostas prontas. Pense: qual pasta guardaria "
    "algo do SISTEMA, e qual ação te deixa VER o que tem dentro dela?\n\n"
    "Pergunta: Qual a ordem certa de ativar janela, ícone, menu e ponteiro?\n"
    "Resposta: Não vou te dar a ordem. Pense no que precisa existir ANTES: "
    "não há ícone nem menu sem algo que os contenha, e não há ponteiro "
    "sem nada pra apontar.\n\n"
    "Pergunta: Qual seu time de futebol favorito?\n"
    "Resposta: Isso está fora do meu escopo. Só falo sobre computadores "
    "pessoais (1975-1990) e o que você precisa resolver aqui.\n\n"
    "Pergunta: Quem inventou a interface gráfica e quando?\n"
    "Resposta: Foi o Xerox PARC, nos anos 1970, com os computadores Alto "
    "e depois Star -- a Xerox criou a tecnologia mas não a tornou um "
    "sucesso comercial."
)

# Quantas perguntas o jogador pode fazer ao SYSTEM_AI durante A FASE
# INTEIRA (não só dentro do puzzle -- o limite é do NPCChatbot, o mesmo
# objeto usado no quarto e no puzzle). Só conta pergunta ENVIADA (ver
# NPCChatbot._enviar_pergunta), não só abrir a caixa de diálogo.
LIMITE_DICAS_SYSTEM_AI = 3


# =====================================================================
# 4B. SEQUÊNCIA DE VITÓRIA (fade + balão de parabéns) -- mesma lógica de
#     Pygame/Fase_2/fase2/fase2.py (_fade_transition/
#     _mostrar_mensagem_vitoria), adaptada: esta fase desenha direto na
#     janela real (sem o passo extra de escalar uma tela virtual pra
#     janela, que a Fase 2 tem porque ela roda numa resolução virtual
#     diferente da janela) e o balão usa a paleta CRT âmbar desta fase
#     (estilo_crt.py) em vez do dourado/creme da Fase 2.
# =====================================================================
def _transicao_fade(tela, relogio, antes, depois, duracao=FADE_DURATION_SECONDS):
    """Fade simples entre dois quadros já prontos: escurece `antes` até
    a cor de fundo CRT, depois clareia até `depois` -- mesma lógica de
    fase2._fade_transition. `antes`/`depois` já vêm PRONTOS (desenhados
    inteiros) de quem chamou; esta função só faz a transição visual
    entre os dois. Só processa QUIT, pra não travar a janela achando
    que o jogo travou."""
    passos = max(1, int(duracao * FPS))
    for origem, escurecendo in ((antes, True), (depois, False)):
        for i in range(passos):
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            relogio.tick(FPS)

            tela.blit(origem, (0, 0))
            progresso = (i + 1) / passos
            alpha = int(255 * progresso) if escurecendo else int(255 * (1 - progresso))
            veu = pygame.Surface(tela.get_size())
            veu.fill(COR_FUNDO_CRT)
            veu.set_alpha(alpha)
            tela.blit(veu, (0, 0))

            pygame.display.flip()


def _pontos_estrela(centro, raio_externo, raio_interno):
    """Devolve os 10 vértices (alternando raio externo/interno, a cada
    36°) de uma estrela de 5 pontas centrada em `centro`, com uma ponta
    voltada pra cima -- usado por _desenhar_estrela. Mesma fórmula de
    fase2._pontos_estrela, copiada aqui (não importada) pra este módulo
    não depender de fase2.py -- mesmo espírito autocontido do resto do
    repositório (audio_fase9.py/audio_fase2.py, etc)."""
    pontos = []
    angulo_inicial = -math.pi / 2  # começa apontando pra cima
    for i in range(10):
        angulo = angulo_inicial + i * math.pi / 5
        raio = raio_externo if i % 2 == 0 else raio_interno
        pontos.append((centro[0] + raio * math.cos(angulo), centro[1] + raio * math.sin(angulo)))
    return pontos


def _desenhar_estrela(surface, centro, raio, conquistada):
    """Desenha uma estrela de 5 pontas em `centro`: preenchida em âmbar
    brilhante se `conquistada`, ou só o contorno (vazia) em âmbar bem
    apagado (COR_AMBAR_DIM) se não -- mesma paleta CRT do resto da fase."""
    pontos = _pontos_estrela(centro, raio, raio * 0.42)
    if conquistada:
        pygame.draw.polygon(surface, COR_AMBAR_BRILHO, pontos)
        pygame.draw.polygon(surface, COR_AMBAR, pontos, width=2)
    else:
        pygame.draw.polygon(surface, COR_AMBAR_DIM, pontos, width=2)


def _mostrar_mensagem_vitoria(tela, relogio, cena_base, mensagem, duracao, estrelas=None, tempo_formatado=None):
    """Mostra `mensagem` num balão estilo CRT âmbar (mesma paleta do
    puzzle/SYSTEM_AI -- ver estilo_crt.py), sobreposto a `cena_base` (uma
    Surface já pronta, redesenhada em todo frame por baixo do balão) por
    `duracao` segundos -- mesmo espírito de
    fase2._mostrar_mensagem_vitoria, só com a estética desta fase em vez
    do dourado/creme da Fase 2.

    `estrelas` (1-3) e `tempo_formatado` ("MM:SS") são opcionais -- quando
    informados (ver a chamada em _iniciar_sequencia_de_vitoria, com o
    resultado de puzzle_terminal.EstadoPuzzleTerminal), o balão cresce
    pra caber a fileira de 3 estrelas e o tempo levado, embaixo da
    mensagem."""
    fonte_balao = pygame.font.SysFont("consolas", 26, bold=True)
    fonte_tempo = pygame.font.SysFont("consolas", 18, bold=True)
    balao_altura = 100 if estrelas is None else 190
    balao_rect = pygame.Rect(0, 0, 560, balao_altura)
    balao_rect.center = (tela.get_width() // 2, tela.get_height() // 2)

    passos = max(1, int(duracao * FPS))
    for _ in range(passos):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
        relogio.tick(FPS)

        tela.blit(cena_base, (0, 0))
        pygame.draw.rect(tela, COR_FUNDO_CRT, balao_rect)
        pygame.draw.rect(tela, COR_AMBAR, balao_rect, width=3)

        texto_y = balao_rect.top + 30 if estrelas is not None else balao_rect.centery
        texto_surf = render_texto_glow(fonte_balao, mensagem, COR_AMBAR_BRILHO)
        tela.blit(texto_surf, texto_surf.get_rect(center=(balao_rect.centerx, texto_y)))

        if estrelas is not None:
            raio_estrela = 20
            espaco_estrela = 56
            estrelas_y = balao_rect.top + 100
            for i in range(3):
                centro_x = balao_rect.centerx + (i - 1) * espaco_estrela
                _desenhar_estrela(tela, (centro_x, estrelas_y), raio_estrela, conquistada=(i < estrelas))
            if tempo_formatado is not None:
                tempo_surf = render_texto_glow(fonte_tempo, f"Tempo: {tempo_formatado}", COR_AMBAR)
                tela.blit(tempo_surf, tempo_surf.get_rect(center=(balao_rect.centerx, balao_rect.bottom - 26)))

        desenhar_scanlines(tela, rect=balao_rect)

        pygame.display.flip()


# =====================================================================
# 5. CLASSE PRINCIPAL DO JOGO
# =====================================================================
class Jogo:
    """Controla o laço principal (game loop) e a máquina de estados da
    fase. Estados: QUARTO (cena principal, jogador anda e clica no
    computador), TERMINAL (o puzzle toma a tela) e SALA_FINAL (depois de
    resolvido: sala separada com a máquina do tempo, mesmo espírito da
    sala da máquina do tempo da Fase 2)."""

    QUARTO = "quarto"
    TERMINAL = "terminal"
    SALA_FINAL = "sala_final"

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

        # --- Música de fundo (em loop) -- toca durante a fase inteira;
        # não faz nada se o arquivo não existir ou não houver placa de
        # som (ver audio_fase9.iniciar_musica_fundo).
        audio_fase9.iniciar_musica_fundo()

        # --- Fontes ---
        self.fonte_terminal = carregar_fonte(ASSETS["fonte_terminal"], 24)
        self.fonte_texto = carregar_fonte(None, 22)
        self.fonte_pequena = carregar_fonte(None, 18)

        # --- Imagens (com placeholder automático se ainda não existirem) ---
        self.img_fundo_quarto = carregar_imagem(CENARIO_QUARTO_PATH, (LARGURA, ALTURA))

        # --- Sala final (SALA_FINAL) -- fundo + máquina do tempo ---
        self.img_fundo_sala_final = carregar_imagem(CENA_FINAL_PATH, (LARGURA, ALTURA))
        self.maquina_tempo_sprite = carregar_avatar_altura(MAQUINA_TEMPO_PATH, MAQUINA_TEMPO_ALTURA)
        self.maquina_tempo_rect = self.maquina_tempo_sprite.get_rect(midbottom=MAQUINA_TEMPO_POS)

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
        # LARGURA - 200 (em vez de LARGURA - 80): a dica "Pressione E
        # para falar com SYSTEM_AI" tem ~360px de largura na fonte
        # consolas e é centralizada em cima do NPC -- perto demais da
        # borda direita, ela ultrapassava os 960px da janela e o nome
        # ficava cortado (o clamp_ip em npc_chatbot.desenhar_dica_interacao
        # é a defesa extra, mas a margem certa aqui evita precisar dele
        # na prática).
        self.rect_npc = pygame.Rect(0, 0, 64, 64)
        self.rect_npc.center = (LARGURA - 200, ALTURA - 80)
        self.npc_chat = NPCChatbot(
            self.rect_npc, "SYSTEM_AI", CONTEXTO_SYSTEM_AI,
            limite_perguntas=LIMITE_DICAS_SYSTEM_AI,
        )

        # --- Estado inicial: a fase sempre começa na cena do quarto ---
        self.estado = Jogo.QUARTO

        # --- Sequência de vitória (sala final) -- só mudam de valor
        # dentro de _iniciar_sequencia_de_vitoria()/executar(), ver lá.
        self.andando_ate_maquina = False  # caminhada automática até a máquina, sem controle do jogador
        self.chegou_na_maquina = False    # libera o controle e o painel do código da máquina

        # Segunda verificação do código (74KX, o código do desktop
        # invertido) -- só depois de codigo_maquina_liberado=True o
        # clique na máquina passa a encerrar a fase (ver o tratamento de
        # MOUSEBUTTONDOWN em executar() e _desenhar_painel_codigo_maquina).
        self.codigo_maquina_liberado = False
        self.codigo_maquina_digitado = ""
        self.codigo_maquina_feedback = ""
        self.codigo_maquina_feedback_ok = None

        # --- Estado do puzzle do terminal (persiste entre aberturas) ---
        # Criado uma única vez aqui, mesmo padrão do ada_chat/estado_puzzle
        # na Fase 2: fechar o puzzle (ESC) sem terminar e clicar no
        # computador de novo continua exatamente na mesma etapa.
        self.estado_puzzle_terminal = puzzle_terminal.EstadoPuzzleTerminal()

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
                    elif (
                        evento.key == pygame.K_e
                        and self.estado != Jogo.SALA_FINAL
                        and not self.npc_chat.limite_atingido()
                    ):
                        # TODO: sem checar distância ainda (ver
                        # perto_do_jogador em npc_chatbot.py) -- por
                        # enquanto E sempre abre o SYSTEM_AI. self.estado
                        # != SALA_FINAL: o SYSTEM_AI é do computador do
                        # quarto, não faz sentido ele "seguir" o jogador
                        # até a sala da máquina do tempo (mesma regra da
                        # Ada não aparecer na sala da máquina, na Fase 2).
                        self.npc_chat.abrir_dialogo()
                    elif (
                        self.estado == Jogo.SALA_FINAL
                        and self.chegou_na_maquina
                        and not self.codigo_maquina_liberado
                    ):
                        # Campo de texto do painel da máquina (ver
                        # _desenhar_painel_codigo_maquina) -- mesmo
                        # padrão de digitação de desktop_final._tentar_
                        # codigo (BACKSPACE apaga, ENTER confere,
                        # qualquer caractere imprimível é adicionado).
                        if evento.key == pygame.K_RETURN:
                            self._tentar_codigo_maquina()
                        elif evento.key == pygame.K_BACKSPACE:
                            self.codigo_maquina_digitado = self.codigo_maquina_digitado[:-1]
                        elif evento.unicode.isprintable() and len(self.codigo_maquina_digitado) < 8:
                            self.codigo_maquina_digitado += evento.unicode.upper()

                elif (
                    evento.type == pygame.MOUSEBUTTONDOWN
                    and evento.button == 1
                    and not self.npc_chat.dialogo_aberto
                    and config_fase9.engrenagem_rect(LARGURA).collidepoint(evento.pos)
                ):
                    # Botão de configurações: sempre acessível (quarto e
                    # sala final), menos com a conversa do SYSTEM_AI
                    # aberta (mesma regra do resto do teclado/mouse
                    # enquanto ela está roubando a atenção -- ver o
                    # KEYDOWN acima). O painel É o "jogo pausado": nada
                    # do resto do laço roda enquanto ele está aberto (ver
                    # config_fase9.abrir_painel_config()).
                    resultado_config = config_fase9.abrir_painel_config(self.tela, self.relogio, LARGURA, ALTURA)
                    if resultado_config == "sair":
                        rodando = False

                elif (
                    evento.type == pygame.MOUSEBUTTONDOWN
                    and evento.button == 1
                    and self.estado == Jogo.QUARTO
                    and not self.npc_chat.dialogo_aberto
                    and COMPUTADOR_RECT.collidepoint(evento.pos)
                ):
                    # Clicou no computador da escrivaninha: "empresta" a
                    # tela pro puzzle do terminal (mesmo padrão de
                    # fase2.py chamando babbage_lovelace.run() -- ver
                    # Pygame/Fase_2/fase2/fase2.py) até o jogador fechar
                    # (ESC, sem terminar) ou concluir as 3 etapas.
                    self.estado = Jogo.TERMINAL
                    resolveu = puzzle_terminal.run(
                        self.tela, self.relogio, self.npc_chat,
                        self.estado_puzzle_terminal, LARGURA, ALTURA,
                    )
                    if resolveu == "sair":
                        # Jogador escolheu SAIR no painel de config
                        # ABERTO DE DENTRO DO PUZZLE (ver o tratamento de
                        # "sair" no loop de puzzle_terminal.run()) --
                        # encerra a fase inteira, não só o puzzle.
                        rodando = False
                    elif resolveu:
                        self._iniciar_sequencia_de_vitoria()
                    else:
                        self.estado = Jogo.QUARTO

                elif (
                    evento.type == pygame.MOUSEBUTTONDOWN
                    and evento.button == 1
                    and self.estado == Jogo.SALA_FINAL
                    and self.chegou_na_maquina
                    and self.codigo_maquina_liberado
                    and self.maquina_tempo_rect.collidepoint(evento.pos)
                ):
                    # Clicou na máquina do tempo depois de já ter chegado
                    # perto dela andando sozinho E já ter digitado o
                    # código certo no painel (74KX -- ver
                    # codigo_maquina_liberado/_tentar_codigo_maquina):
                    # conclui a fase.
                    # TODO: quando a Fase 10 existir (a ser combinado com
                    # o grupo), conectar essa saída a ela pelo menu (ver
                    # Pygame/menu/jogo.py e como fase2.run() devolve
                    # True/False pro menu decidir o que vem a seguir) --
                    # por enquanto só encerra a fase, igual ao ESC.
                    rodando = False

            # Movimento do jogador: WASD/setas na cena do quarto, e
            # também na sala final DEPOIS que a caminhada automática até
            # a máquina termina (mesmos controles/regra da Fase 2) --
            # sempre que nenhuma caixa de diálogo está roubando o
            # teclado.
            if self.estado == Jogo.QUARTO and not self.npc_chat.dialogo_aberto:
                teclas = pygame.key.get_pressed()
                self.jogador.mover(teclas, FLOOR_RECT)
            elif self.estado == Jogo.SALA_FINAL:
                if self.andando_ate_maquina:
                    # Caminhada automática (ignora o teclado do jogador)
                    # até bem em frente à máquina do tempo -- mesma lógica
                    # de fase2.Jogador.mover_para(), usada na Fase 2 pra
                    # ir até a máquina do tempo dela.
                    if self.jogador.mover_para(MAQUINA_TEMPO_CHEGADA_POS, SALA_FINAL_FLOOR_RECT):
                        self.andando_ate_maquina = False
                        self.chegou_na_maquina = True
                elif not self.npc_chat.dialogo_aberto:
                    teclas = pygame.key.get_pressed()
                    self.jogador.mover(teclas, SALA_FINAL_FLOOR_RECT)

            # SYSTEM_AI precisa saber em qual etapa do puzzle o jogador
            # está agora mesmo perguntando daqui do quarto (antes de
            # abrir o computador) -- mesmo contexto dinâmico usado
            # dentro de puzzle_terminal.run().
            self.npc_chat.atualizar_contexto_dinamico(
                puzzle_terminal.contexto_dinamico_etapa(self.estado_puzzle_terminal)
            )

            if self.estado == Jogo.QUARTO:
                self._desenhar_quarto()
            elif self.estado == Jogo.TERMINAL:
                self._desenhar_terminal()
            elif self.estado == Jogo.SALA_FINAL:
                self._desenhar_sala_final()

            # SYSTEM_AI só existe no quarto/computador -- na sala final
            # (depois da vitória) ele não é desenhado nem interativo,
            # mesma regra do retrato da Ada não aparecer na sala da
            # máquina do tempo, na Fase 2.
            if self.estado != Jogo.SALA_FINAL:
                self.npc_chat.desenhar(self.tela, self.fonte_texto, self.fonte_pequena, LARGURA, ALTURA)
                if not self.npc_chat.dialogo_aberto:
                    self.npc_chat.desenhar_dica_interacao(self.tela, self.fonte_pequena)
                self.npc_chat.desenhar_contador_dicas(self.tela, self.fonte_pequena)

            # Botão de configurações -- sempre visível, em toda tela
            # jogável da fase (quarto e sala final; o puzzle desenha o
            # próprio dentro de puzzle_terminal.run(), que tem seu
            # próprio loop separado deste).
            config_fase9.desenhar_engrenagem(self.tela, LARGURA, pygame.mouse.get_pos())

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

    # -----------------------------------------------------------------
    # DESENHO: TERMINAL (só um placeholder de transição -- o puzzle de
    # verdade roda dentro de puzzle_terminal.run(), chamado direto no
    # clique do computador; este estado só é redesenhado, se algum dia
    # for, no frame logo antes/depois do puzzle "tomar" a tela)
    # -----------------------------------------------------------------
    def _desenhar_terminal(self):
        """Tela de terminal preta com um cursor piscando -- fallback
        visual simples (o puzzle de verdade é puzzle_terminal.run())."""
        self.tela.fill(PRETO)
        # Por enquanto só um prompt fixo com cursor piscando, pra
        # confirmar que a janela e o laço principal estão funcionando.
        prompt = "C:\\>"
        cursor_aceso = pygame.time.get_ticks() % 1000 < 500
        texto = prompt + ("_" if cursor_aceso else " ")
        render = self.fonte_terminal.render(texto, True, VERDE_TERMINAL)
        self.tela.blit(render, (40, ALTURA - 60))

    # -----------------------------------------------------------------
    # SEQUÊNCIA DE VITÓRIA: fade pro desktop reconstruído -> sala final
    # (mesma lógica de fase2.run(), no bloco logo após
    # babbage_lovelace.run() devolver True)
    # -----------------------------------------------------------------
    def _iniciar_sequencia_de_vitoria(self):
        """Chamada assim que puzzle_terminal.run() devolve True (puzzle
        resolvido): tira uma "foto" do último quadro que ele deixou em
        self.tela (o desktop gráfico já reconstruído, aceso pela própria
        animação de puzzle_terminal._animar_tela_acendendo) e faz a
        transição pra sala final, só com a máquina do tempo -- mesmo
        fluxo de fase2.run(): fade (_transicao_fade) + balão de parabéns
        (_mostrar_mensagem_vitoria) + início da caminhada automática até
        a máquina (o jogador só recupera o controle ao chegar perto
        dela, ver o bloco de movimento em executar())."""
        antes = self.tela.copy()

        # Personagem "entrando pela porta": mesmo frame parado (sem
        # animação de caminhada) usado por fase2._draw_player no quadro
        # "depois" da transição dela.
        self.jogador.pos = pygame.Vector2(SALA_FINAL_ENTRY_POS)
        self.jogador.imagem = self.jogador.frame_parado
        self.jogador.indice_animacao = 0

        depois = pygame.Surface((LARGURA, ALTURA))
        if self.img_fundo_sala_final:
            depois.blit(self.img_fundo_sala_final, (0, 0))
        else:
            depois.fill(PRETO)
        depois.blit(self.maquina_tempo_sprite, self.maquina_tempo_rect)
        self.jogador.desenhar(depois)
        nome_render = self.fonte_pequena.render(self.character_name, True, BRANCO)
        depois.blit(nome_render, nome_render.get_rect(
            midtop=(int(self.jogador.pos.x), int(self.jogador.pos.y) + 4)
        ))

        _transicao_fade(self.tela, self.relogio, antes, depois)
        _mostrar_mensagem_vitoria(
            self.tela, self.relogio, depois, MENSAGEM_VITORIA, MENSAGEM_VITORIA_SEGUNDOS,
            estrelas=self.estado_puzzle_terminal.estrelas_conquistadas,
            tempo_formatado=self.estado_puzzle_terminal.tempo_formatado,
        )

        self.estado = Jogo.SALA_FINAL
        self.andando_ate_maquina = True
        self.chegou_na_maquina = False
        self.codigo_maquina_liberado = False
        self.codigo_maquina_digitado = ""
        self.codigo_maquina_feedback = ""
        self.codigo_maquina_feedback_ok = None

    def _tentar_codigo_maquina(self):
        """Confere o texto digitado no painel da máquina contra
        CODIGO_MAQUINA_CORRETO (74KX) -- mesmo padrão de
        desktop_final._tentar_codigo. Só libera o clique na máquina
        (ver o MOUSEBUTTONDOWN em executar()) quando acerta."""
        tentativa = self.codigo_maquina_digitado.strip().upper()
        acertou = tentativa == CODIGO_MAQUINA_CORRETO
        self.codigo_maquina_feedback = MSG_CODIGO_MAQUINA_OK if acertou else MSG_CODIGO_MAQUINA_ERRO
        self.codigo_maquina_feedback_ok = acertou
        if acertou:
            self.codigo_maquina_liberado = True
        return acertou

    # -----------------------------------------------------------------
    # DESENHO: SALA_FINAL (sala separada com a máquina do tempo, depois
    # do puzzle resolvido -- mesmo espírito da sala da máquina do tempo
    # da Fase 2)
    # -----------------------------------------------------------------
    def _desenhar_sala_final(self):
        """Fundo da sala final + máquina do tempo + o personagem (que
        chegou pela esquerda e anda sozinho até perto dela, ver
        Jogo.executar()). Ao chegar, mostra embaixo a dica pra clicar na
        máquina (MACHINE_HINT), com o mesmo estilo âmbar/CRT do resto da
        fase."""
        if self.img_fundo_sala_final:
            self.tela.blit(self.img_fundo_sala_final, (0, 0))
        else:
            self.tela.fill(PRETO)

        self.tela.blit(self.maquina_tempo_sprite, self.maquina_tempo_rect)

        self.jogador.desenhar(self.tela)
        nome_render = self.fonte_pequena.render(self.character_name, True, BRANCO)
        self.tela.blit(nome_render, nome_render.get_rect(
            midtop=(int(self.jogador.pos.x), int(self.jogador.pos.y) + 4)
        ))

        if self.chegou_na_maquina and not self.codigo_maquina_liberado:
            self._desenhar_painel_codigo_maquina()
        elif self.chegou_na_maquina:
            dica_surf = render_texto_glow(self.fonte_pequena, MACHINE_HINT, COR_AMBAR)
            self.tela.blit(dica_surf, dica_surf.get_rect(midbottom=(LARGURA // 2, ALTURA - 8)))

    def _desenhar_painel_codigo_maquina(self):
        """Painel CRT âmbar (mesma paleta/estilo de _mostrar_mensagem_
        vitoria -- COR_FUNDO_CRT/COR_AMBAR, consistente com o resto da
        fase) pedindo o código de ativação (74KX) antes de liberar o
        clique na máquina. Substitui a MACHINE_HINT até o jogador
        acertar (ver _tentar_codigo_maquina)."""
        fonte_instr = pygame.font.SysFont("consolas", 15, bold=True)
        fonte_campo = pygame.font.SysFont("consolas", 22, bold=True)
        fonte_fb = pygame.font.SysFont("consolas", 14, bold=True)

        painel_rect = pygame.Rect(0, 0, 480, 130)
        painel_rect.midbottom = (LARGURA // 2, ALTURA - 8)

        pygame.draw.rect(self.tela, COR_FUNDO_CRT, painel_rect)
        pygame.draw.rect(self.tela, COR_AMBAR, painel_rect, width=3)

        instr_surf = render_texto_glow(fonte_instr, INSTRUCAO_CODIGO_MAQUINA, COR_AMBAR)
        self.tela.blit(instr_surf, instr_surf.get_rect(midtop=(painel_rect.centerx, painel_rect.top + 10)))

        campo_rect = pygame.Rect(0, 0, 200, 34)
        campo_rect.midtop = (painel_rect.centerx, painel_rect.top + 40)
        pygame.draw.rect(self.tela, PRETO, campo_rect)
        pygame.draw.rect(self.tela, COR_AMBAR, campo_rect, width=2)
        texto_surf = fonte_campo.render(self.codigo_maquina_digitado, True, COR_AMBAR_BRILHO)
        self.tela.blit(texto_surf, texto_surf.get_rect(midleft=(campo_rect.left + 8, campo_rect.centery)))
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = campo_rect.left + 8 + texto_surf.get_width() + 2
            pygame.draw.line(
                self.tela, COR_AMBAR_BRILHO,
                (cursor_x, campo_rect.top + 6), (cursor_x, campo_rect.bottom - 6), 2,
            )

        if self.codigo_maquina_feedback:
            cor_fb = COR_AMBAR_BRILHO if self.codigo_maquina_feedback_ok else (200, 60, 40)
            fb_surf = fonte_fb.render(self.codigo_maquina_feedback, True, cor_fb)
            self.tela.blit(fb_surf, fb_surf.get_rect(midtop=(painel_rect.centerx, campo_rect.bottom + 8)))
        else:
            dica_surf = fonte_fb.render("(pressione ENTER para confirmar)", True, (150, 110, 40))
            self.tela.blit(dica_surf, dica_surf.get_rect(midtop=(painel_rect.centerx, campo_rect.bottom + 8)))

        desenhar_scanlines(self.tela, rect=painel_rect)


# =====================================================================
# 6. PONTO DE ENTRADA DO PROGRAMA
# =====================================================================
if __name__ == "__main__":
    jogo = Jogo()
    jogo.executar()
