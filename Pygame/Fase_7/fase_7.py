"""
=====================================================================
Fase_Valvulas: O MAINFRAME SUPERAQUECIDO (transição válvulas -> transistores)
=====================================================================

CONTEXTO DA FASE
-----------------
O computador do laboratório ainda usa válvulas (como o Colossus) e está
superaquecendo. O jogador (a) precisa entrar no mainframe e substituir
as 8 válvulas por transistores novos antes que o tempo acabe. Ao
concluir, um painel acende com um código que abre a porta e leva à
tela de vitória.

ESTRUTURA DO JOGO (máquina de estados)
---------------------------------------
MENU          -> tela preta de introdução com a frase de contexto e o
                 botão "Iniciar".
CENA1         -> sala com o personagem (avatar), o NPC (Tommy Flowers)
                 e o computador/mainframe fechado, ao lado. O jogador
                 anda até ele e clica para entrar.
CENA_DESAFIO  -> close-up do mainframe aberto: 8 válvulas brilhando +
                 caixa com 8 transistores ao lado. O jogador clica em
                 cada válvula para trocá-la por um transistor. Ao
                 trocar todas, aparece "Sistema modernizado." e um
                 painel com o código (ex: 1943) que, ao ser clicado,
                 abre a porta e leva à Vitória.
VITORIA       -> "Sistema modernizado, porta aberta!" + botão
                 "Continuar" que devolve o controle ao menu principal
                 do jogo (mesmo contrato usado pela Fase 4).
DERROTA       -> aparece se o tempo acabar antes de trocar todas as
                 válvulas.

COMO VOCÊ VAI PERSONALIZAR
---------------------------
1. Gere/baixe as imagens e salve-as numa pasta "assets/" ao lado deste
   arquivo (ou ajuste os caminhos no dicionário ASSETS).
2. Enquanto uma imagem não existir, o jogo desenha automaticamente um
   retângulo colorido com um texto no lugar dela (placeholder), então
   dá para testar a lógica da fase antes de ter todas as artes prontas.
3. Se essa fase tiver outro número no seu jogo (ex: Fase 6, Fase 7...),
   troque só PROGRESSO_CHAVE_FASE, o título da janela e o texto do
   título na tela de menu -- o resto do código não depende do número.

Requisitos: pip install pygame
Execução:   python fase_valvulas_final.py
=====================================================================
"""

import json
import os
import sys
import math
import pygame
from inventario import Inventario
from npc_chatbot import NPCChatbot
import audio_fase5
import config_fase5

# =====================================================================
# 1. CONFIGURAÇÕES GERAIS DA JANELA E DO JOGO
# =====================================================================
LARGURA, ALTURA = 960, 600
FPS = 60

# Tempo total da fase, em segundos (4 minutos -- desafio simples,
# então um tempo mais curto que o da Fase 4 já é justo)
TEMPO_LIMITE_SEGUNDOS = 4 * 60


# Cores utilitárias (RGB) usadas em textos e placeholders
BRANCO      = (245, 245, 240)
PRETO       = (10, 10, 12)
CINZA       = (90, 90, 90)
CINZA_CLARO = (180, 180, 180)
VERDE       = (60, 170, 90)
VERMELHO    = (190, 60, 60)
LARANJA_VALVULA = (214, 122, 46)   # brilho quente da válvula ligada
AZUL_TRANSISTOR = (80, 150, 190)   # tom "moderno" do transistor
BG_COLOR = (8, 10, 22)


# =====================================================================
# 2. CAMINHOS DOS ASSETS -> PREENCHA AQUI COM SUAS IMAGENS
# =====================================================================
# Dica: crie uma pasta "assets" ao lado deste arquivo .py e salve suas
# imagens lá dentro. Formatos aceitos: .png (recomendado, com
# transparência) ou .jpg.
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))


def caminho_asset(nome_relativo):
    """Monta o caminho absoluto de um asset a partir da pasta 'assets'
    ao lado deste arquivo .py."""
    return os.path.join(PASTA_DO_SCRIPT, nome_relativo)


# ---------------------------------------------------------------------------
# Progresso (estrelas + tempo) -- mesmo arquivo/formato compartilhado que as
# outras fases já usam: {"estrelas": 1-3, "completo": true, "tempo": "MM:SS"}
# ("tempo" é quanto o jogador LEVOU pra resolver, não quanto sobrou no
# timer). Fica na raiz de Pygame/, fora de qualquer fase específica.
#
# Conectada como Fase 7 no mapa (Pygame/menu/jogo.py) -- chave alinhada
# com o padrão "fase_N" usado por todas as outras fases já conectadas.
# ---------------------------------------------------------------------------
_PYGAME_DIR = os.path.dirname(PASTA_DO_SCRIPT)
PROGRESSO_PATH = os.path.join(_PYGAME_DIR, "progresso.json")
PROGRESSO_CHAVE_FASE = "fase_7"


def _carregar_progresso():
    """Lê Pygame/progresso.json inteiro (de todas as fases). Devolve um
    dicionário vazio se o arquivo ainda não existir ou vier corrompido."""
    if not os.path.exists(PROGRESSO_PATH):
        return {}
    try:
        with open(PROGRESSO_PATH, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError):
        return {}


def _salvar_progresso(estrelas, tempo_formatado):
    """Grava `estrelas` (1 a 3) e `tempo_formatado` ("MM:SS") na chave
    PROGRESSO_CHAVE_FASE do progresso.json compartilhado, preservando as
    chaves de outras fases. Nunca sobrescreve um resultado melhor já
    salvo (mesma regra usada na Fase 4)."""
    progresso = _carregar_progresso()
    anterior = progresso.get(PROGRESSO_CHAVE_FASE)
    if anterior is not None and anterior.get("estrelas", 0) >= estrelas:
        if anterior.get("tempo") is not None:
            return
        novo_registro = {**anterior, "estrelas": anterior.get("estrelas", estrelas), "completo": True, "tempo": tempo_formatado}
    else:
        novo_registro = {"estrelas": estrelas, "completo": True, "tempo": tempo_formatado}

    progresso[PROGRESSO_CHAVE_FASE] = novo_registro
    with open(PROGRESSO_PATH, "w", encoding="utf-8") as arquivo:
        json.dump(progresso, arquivo, indent=2, ensure_ascii=False)


# Limiares de estrelas -- baseados no tempo RESTANTE no timer no instante
# em que o jogador vence (mesmos limiares usados nas outras fases).
ESTRELAS_3_TEMPO_MIN = 25  # >= 25s sobrando -> 3 estrelas
ESTRELAS_2_TEMPO_MIN = 15  # 15 a 24s sobrando -> 2 estrelas
# < 15s sobrando -> 1 estrela


def _calcular_estrelas(tempo_restante):
    """Devolve 1, 2 ou 3 conforme `tempo_restante` (segundos ainda no
    timer quando o jogador venceu) contra os limiares acima."""
    if tempo_restante >= ESTRELAS_3_TEMPO_MIN:
        return 3
    if tempo_restante >= ESTRELAS_2_TEMPO_MIN:
        return 2
    return 1


def _formatar_tempo(segundos):
    """Formata `segundos` (int/float) como "MM:SS"."""
    total = max(0, int(segundos))
    return f"{total // 60:02d}:{total % 60:02d}"


ASSETS = {
    # Fundo da tela de MENU/INTRODUÇÃO inicial (tela preta com a frase
    # de contexto). Sugestão de tamanho: 960x600 px. Se preferir, deixe
    # o arquivo ausente -- o jogo já desenha um fundo preto liso.
    "fundo_intro": caminho_asset("assets/fundo_intro_valvulas.png"),

    # Avatar do jogador (spritesheet simples ou imagem única).
    # Sugestão de tamanho: 138x288 px, fundo transparente (PNG).
    "avatar_parado": caminho_asset("assets/personagem_parado.png"),
    "avatar_andando1": caminho_asset("assets/personagem_andando1.png"),
    "avatar_andando2": caminho_asset("assets/personagem_andando2.png"),

    # Segundo personagem selecionável no menu geral (mesmo padrão de
    # 3 imagens: parado + 2 de caminhada).
    "avatar2_parado": caminho_asset("assets/personagem2_parado.png"),
    "avatar2_andando1": caminho_asset("assets/personagem2_andando1.png"),
    "avatar2_andando2": caminho_asset("assets/personagem2_andando2.png"),

    # Sprite do NPC (Tommy Flowers, o engenheiro que projetou o
    # Colossus). Fundo transparente (PNG). Mesmo tamanho do avatar.
    "npc": caminho_asset("assets/tommy_flowers.png"),

    # Fundo da CENA 1: sala do laboratório com o mainframe fechado
    # (ainda não é o close-up do desafio). Sugestão: 960x600 px.
    "fundo_cena1": caminho_asset("assets/sala_mainframe.png"),

    # Sprite do computador/mainframe FECHADO, clicável na Cena 1.
    "computador": caminho_asset("assets/mainframe_fechado.png"),

    # Fundo da CENA_DESAFIO: o mainframe aberto, mostrando os 8
    # encaixes de válvula. Sugestão: 960x600 px.
    "fundo_desafio": caminho_asset("assets/mainframe_aberto.png"),

    # Sprite de UMA válvula acesa (será desenhada 8 vezes, uma por
    # encaixe). Fundo transparente (PNG). Sugestão: 70x100 px.
    "valvula": caminho_asset("assets/valvula.png"),

    # Sprite de UM transistor (substitui a válvula após o clique).
    # Mesmo tamanho da válvula, fundo transparente (PNG).
    "transistor": caminho_asset("assets/transistor.png"),

    # Caixa com os transistores novos, desenhada ao lado do mainframe
    # (elemento decorativo). Sugestão: 200x260 px.
    "caixa_transistores": caminho_asset("assets/caixa_transistores.png"),

    # Painel que acende com o código, uma vez modernizado o sistema.
    # Sugestão: 260x120 px.
    "painel_codigo": caminho_asset("assets/painel_codigo.png"),

    # Ícone quadrado do botão de configurações (canto superior direito).
    "icone_configuracao": caminho_asset("assets/icone_configuracao.png"),

    # Tela final de VITÓRIA (ex: porta do mainframe se abrindo).
    "tela_vitoria": caminho_asset("assets/vitoria_valvulas.png"),

    # Tela final de DERROTA (ex: painel de alarme, fumaça saindo do
    # mainframe superaquecido).
    "tela_derrota": caminho_asset("assets/derrota_valvulas.png"),

    # (Opcional) Fonte .ttf com estilo retrô/tecnológico. Deixe o
    # arquivo ausente para usar a fonte padrão do sistema.
    "fonte": caminho_asset("assets/fonte_jogo.ttf"),
}


# =====================================================================
# 3. FUNÇÕES AUXILIARES DE CARREGAMENTO (COM PLACEHOLDER AUTOMÁTICO)
# =====================================================================
def carregar_imagem(caminho, tamanho, cor_placeholder, texto_placeholder):
    """
    Tenta carregar uma imagem do disco e redimensioná-la para 'tamanho'
    (tupla largura, altura). Se o arquivo não existir (porque você
    ainda não adicionou o asset), gera uma superfície colorida com um
    texto no lugar, para que o jogo continue funcionando durante os
    testes.
    """
    if caminho and os.path.isfile(caminho):
        imagem = pygame.image.load(caminho).convert_alpha()
        return pygame.transform.smoothscale(imagem, tamanho)

    # --- PLACEHOLDER (usado enquanto o asset real não existe) ---
    superficie = pygame.Surface(tamanho, pygame.SRCALPHA)
    superficie.fill(cor_placeholder)
    pygame.draw.rect(superficie, PRETO, superficie.get_rect(), width=3)

    fonte = pygame.font.SysFont("arial", 16, bold=True)
    linhas = texto_placeholder.split("\n")
    y = tamanho[1] // 2 - (len(linhas) * 20) // 2
    for linha in linhas:
        texto_render = fonte.render(linha, True, PRETO)
        rect_texto = texto_render.get_rect(center=(tamanho[0] // 2, y))
        superficie.blit(texto_render, rect_texto)
        y += 20
    return superficie


def carregar_fonte(caminho, tamanho):
    """Carrega uma fonte customizada (.ttf) se disponível, ou usa uma
    fonte padrão do sistema como alternativa."""
    if caminho and os.path.isfile(caminho):
        return pygame.font.Font(caminho, tamanho)
    return pygame.font.SysFont("consolas", tamanho)


# =====================================================================
# 4. O ENIGMA: CÓDIGO REVELADO APÓS MODERNIZAR O MAINFRAME
# =====================================================================
# Troque livremente por qualquer código de 4 dígitos -- por exemplo,
# um ano marcante da história da computação. 1943 é o ano em que o
# Colossus (o computador a válvulas que inspirou esta fase) entrou em
# operação, mas fique à vontade para usar outro.
CODIGO_PAINEL = "1943"

TOTAL_VALVULAS = 8


# =====================================================================
# 5. CLASSE: JOGADOR (AVATAR CONTROLÁVEL NA CENA 1)
# =====================================================================
class Jogador:
    """Avatar do jogador. Pode se mover manualmente (teclado) ou
    automaticamente até um destino (quando o jogador clica em um
    objeto interativo, como o mainframe)."""

    VELOCIDADE = 4
    INTERVALO_ANIMACAO_MS = 150

    def __init__(self, frame_parado, frames_andando, posicao_inicial):
        self.frame_parado = frame_parado
        self.frames_andando = frames_andando
        self.indice_animacao = 0
        self.tempo_ultimo_frame = pygame.time.get_ticks()

        self.imagem = self.frame_parado
        self.rect = self.imagem.get_rect(topleft=posicao_inicial)
        self.olhando_para_esquerda = False

        self.destino = None
        self.movendo_automaticamente = False

    def mover_ate(self, destino):
        """Inicia o deslocamento automático do jogador até o ponto
        'destino' (tupla x, y). Chamado quando o jogador clica em um
        objeto interativo, como o mainframe."""
        self.destino = destino
        self.movendo_automaticamente = True

    def mover(self, teclas, limites):
        """Move o jogador (manual ou automaticamente) e atualiza a
        animação. Retorna True no frame exato em que o destino
        automático é alcançado."""
        chegou_ao_destino = False

        if self.movendo_automaticamente:
            dx = self._calcular_direcao_para_destino()
            esta_andando = (dx != 0)
            if not esta_andando:
                self.movendo_automaticamente = False
                chegou_ao_destino = True
        else:
            dx = 0
            if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
                dx -= self.VELOCIDADE
            if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
                dx += self.VELOCIDADE
            esta_andando = (dx != 0)

        if dx < 0:
            self.olhando_para_esquerda = True
        elif dx > 0:
            self.olhando_para_esquerda = False

        self.rect.x = max(limites.left, min(self.rect.x + dx, limites.right - self.rect.width))

        self._atualizar_sprite(esta_andando)
        return chegou_ao_destino

    def _calcular_direcao_para_destino(self):
        alvo_x, _ = self.destino
        centro_x, _ = self.rect.center
        delta_x = alvo_x - centro_x

        if abs(delta_x) <= self.VELOCIDADE:
            return 0

        return self.VELOCIDADE if delta_x > 0 else -self.VELOCIDADE

    def _atualizar_sprite(self, esta_andando):
        if not esta_andando:
            imagem_base = self.frame_parado
            self.indice_animacao = 0
        else:
            agora = pygame.time.get_ticks()
            if agora - self.tempo_ultimo_frame >= self.INTERVALO_ANIMACAO_MS:
                self.indice_animacao = (self.indice_animacao + 1) % len(self.frames_andando)
                self.tempo_ultimo_frame = agora
            imagem_base = self.frames_andando[self.indice_animacao]

        if self.olhando_para_esquerda:
            self.imagem = pygame.transform.flip(imagem_base, True, False)
        else:
            self.imagem = imagem_base

    def desenhar(self, tela):
        tela.blit(self.imagem, self.rect)


# =====================================================================
# 6. CLASSE PRINCIPAL: O JOGO
# =====================================================================
class Jogo:
    """Controla o laço principal (game loop), a máquina de estados das
    cenas e o cronômetro da fase."""

    MENU = "menu"
    CENA1 = "cena1"
    CENA_DESAFIO = "cena_desafio"
    VITORIA = "vitoria"
    DERROTA = "derrota"

    POSICAO_INICIAL_JOGADOR = (80, ALTURA - 300)

    def __init__(self, inventario=None, character_image=None, character_name=None, genero="m"):
        """
        Segue o mesmo contrato usado pelo menu geral do jogo para
        chamar qualquer fase (veja Fase 4, `Jogo.__init__`):

            modulo.Jogo(
                character_image=CHARACTER_IMAGES.get(self.personagem_index),
                character_name=self.get_personagem_name(self.personagem_index),
                genero="m" if self.personagem_index == 0 else "f",
            ).executar()
        """
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Mainframe Superaquecido - Válvulas x Transistores")
        self.relogio = pygame.time.Clock()

        # --- Inventário (recebido para manter compatibilidade entre
        # fases, mesmo que esta fase não colecione nenhum item novo) ---
        self.inventario = inventario if inventario is not None else Inventario()

        # --- Personagem escolhido no MENU GERAL, recebido via `genero` ---
        self.genero = genero if genero in ("m", "f") else "m"
        self.personagem_escolhido = 1 if self.genero == "m" else 2

        self.character_image = character_image
        self.character_name = character_name or (
            "Personagem 1" if self.personagem_escolhido == 1 else "Personagem 2"
        )

        # --- Ícone do botão de configurações ---
        self.img_config = carregar_imagem(
            ASSETS["icone_configuracao"], (36, 36), CINZA_CLARO, "CONFIG",
        )
        self.img_config_hover = carregar_imagem(
            ASSETS["icone_configuracao"], (42, 42), CINZA_CLARO, "CONFIG",
        )

        # --- Fontes ---
        self.fonte_titulo = carregar_fonte(ASSETS["fonte"], 30)
        self.fonte_texto = carregar_fonte(ASSETS["fonte"], 26)
        self.fonte_pequena = carregar_fonte(ASSETS["fonte"], 20)
        self.fonte_codigo = carregar_fonte(ASSETS["fonte"], 40)

        # --- Imagens de fundo ---
        self.img_fundo_intro = carregar_imagem(
            ASSETS["fundo_intro"], (LARGURA, ALTURA), PRETO, "FUNDO DA INTRO",
        )
        self.img_fundo_cena1 = carregar_imagem(
            ASSETS["fundo_cena1"], (LARGURA, ALTURA), (40, 40, 46),
            "FUNDO DA CENA 1\n(sala do mainframe)",
        )
        self.img_fundo_desafio = carregar_imagem(
            ASSETS["fundo_desafio"], (LARGURA, ALTURA), (30, 30, 36),
            "FUNDO DO DESAFIO\n(mainframe aberto)",
        )
        self.img_vitoria = carregar_imagem(
            ASSETS["tela_vitoria"], (LARGURA, ALTURA), VERDE, "TELA DE VITÓRIA",
        )
        self.img_derrota = carregar_imagem(
            ASSETS["tela_derrota"], (LARGURA, ALTURA), VERMELHO, "TELA DE DERROTA",
        )

        # --- Sprites de cena ---
        self.img_computador = carregar_imagem(
            ASSETS["computador"], (128, 135), (60, 60, 68), "MAINFRAME\n(fechado)",
        )
        self.img_valvula = carregar_imagem(
            ASSETS["valvula"], (70, 100), LARANJA_VALVULA, "VÁLVULA",
        )
        self.img_transistor = carregar_imagem(
            ASSETS["transistor"], (70, 100), AZUL_TRANSISTOR, "TRANSISTOR",
        )
        self.img_caixa_transistores = carregar_imagem(
            ASSETS["caixa_transistores"], (200, 260), (110, 90, 70),
            "CAIXA DE\nTRANSISTORES\nNOVOS",
        )
        self.img_painel_codigo = carregar_imagem(
            ASSETS["painel_codigo"], (260, 120), (25, 60, 40), "",
        )

        # --- Sprites do personagem (2 opções, escolhidas no menu geral) ---
        self.img_avatar_parado = carregar_imagem(
            ASSETS["avatar_parado"], (138, 288), CINZA, "PARADO",
        )
        self.img_avatar_andando1 = carregar_imagem(
            ASSETS["avatar_andando1"], (138, 288), CINZA, "ANDANDO 1",
        )
        self.img_avatar_andando2 = carregar_imagem(
            ASSETS["avatar_andando2"], (138, 288), CINZA, "ANDANDO 2",
        )
        self.img_avatar2_parado = carregar_imagem(
            ASSETS["avatar2_parado"], (138, 288), (120, 70, 70), "PARADO 2",
        )
        self.img_avatar2_andando1 = carregar_imagem(
            ASSETS["avatar2_andando1"], (138, 288), (120, 70, 70), "ANDANDO 2.1",
        )
        self.img_avatar2_andando2 = carregar_imagem(
            ASSETS["avatar2_andando2"], (138, 288), (120, 70, 70), "ANDANDO 2.2",
        )

        self.opcoes_personagens = [
            {
                "nome": "Personagem 1",
                "parado": self.img_avatar_parado,
                "andando": [self.img_avatar_andando1, self.img_avatar_andando2],
            },
            {
                "nome": "Personagem 2",
                "parado": self.img_avatar2_parado,
                "andando": [self.img_avatar2_andando1, self.img_avatar2_andando2],
            },
        ]

        opcao_personagem = self.opcoes_personagens[self.personagem_escolhido - 1]
        self.jogador = Jogador(
            frame_parado=opcao_personagem["parado"],
            frames_andando=opcao_personagem["andando"],
            posicao_inicial=self.POSICAO_INICIAL_JOGADOR,
        )

        # --- NPC (Tommy Flowers, engenheiro do Colossus) ---
        self.img_npc = carregar_imagem(
            ASSETS["npc"], (168, 288), (110, 90, 130), "NPC",
        )
        self.rect_npc = self.img_npc.get_rect(midleft=(410, ALTURA - 175))
        self.npc_chat = NPCChatbot(
            rect_npc=self.rect_npc,
            nome_npc="Tommy Flowers",
            contexto_fase=(
                "Você é Tommy Flowers, engenheiro britânico que projetou o "
                "Colossus, dentro de um jogo de escape room educativo. "
                "Responda SOMENTE perguntas relacionadas a esta fase: o "
                "mainframe a válvulas que está superaquecendo e precisa ser "
                "modernizado, trocando as 8 válvulas por transistores novos "
                "guardados numa caixa ao lado do mainframe. Se o jogador "
                "perguntar por que trocar válvulas por transistores, explique "
                "de forma simples que transistores são menores, mais "
                "confiáveis e esquentam muito menos que válvulas. Se o "
                "jogador perguntar algo fora desse tema, responda "
                "educadamente que só pode falar sobre esta fase. Responda "
                "sempre em português, em no máximo 3 frases curtas, sem "
                "nunca revelar diretamente o código do painel."
            ),
        )

        # --- Botão "Iniciar" do menu ---
        self.botao_iniciar = pygame.Rect(0, 0, 220, 60)
        self.botao_iniciar.center = (LARGURA // 2, ALTURA - 90)

        # --- Botões "Reiniciar" das telas de Vitória e Derrota ---
        self.botao_continuar_vitoria = pygame.Rect(0, 0, 260, 60)
        self.botao_continuar_vitoria.center = (LARGURA // 2, ALTURA // 2 + 140)

        self.botao_reiniciar_derrota = pygame.Rect(0, 0, 260, 60)
        self.botao_reiniciar_derrota.center = (LARGURA // 2, ALTURA // 2 + 140)

        # --- Elementos da CENA 1 ---
        self.limites_sala = pygame.Rect(0, 0, LARGURA, ALTURA)
        self.rect_computador = self.img_computador.get_rect(midright=(LARGURA - 232, ALTURA - 170))
        self.ponto_interacao_computador = (
            self.rect_computador.left - 40,
            self.rect_computador.bottom - 20,
        )
        self.proximo_estado_ao_chegar = None

        # --- Elementos da CENA_DESAFIO: 8 encaixes de válvula, em uma
        # grade de 4 colunas x 2 linhas, centralizados na metade
        # esquerda da tela (a caixa de transistores fica à direita) ---
        self.valvulas = []
        colunas, linhas = 4, 2
        espaco_x, espaco_y = 130, 150
        origem_x = 90
        origem_y = 160
        indice = 0
        for linha in range(linhas):
            for coluna in range(colunas):
                rect = self.img_valvula.get_rect(
                    center=(origem_x + coluna * espaco_x, origem_y + linha * espaco_y)
                )
                self.valvulas.append({"id": indice, "rect": rect, "trocada": False})
                indice += 1

        # Caixa de transistores, decorativa, à direita da grade
        self.rect_caixa_transistores = self.img_caixa_transistores.get_rect(
            midright=(LARGURA - 40, ALTURA // 2)
        )

        # Painel do código, aparece centralizado quando o sistema é
        # modernizado (funciona também como "porta": clicar nele leva
        # à Vitória).
        self.rect_painel_codigo = self.img_painel_codigo.get_rect(
            center=(LARGURA // 2, ALTURA - 90)
        )

        self.sistema_modernizado = False

        # --- Estado do jogo ---
        self.estado = Jogo.MENU
        self.ticks_inicio = None

    # -----------------------------------------------------------------
    # CONTROLE DE TEMPO
    # -----------------------------------------------------------------
    def iniciar_cronometro(self):
        """Marca o instante em que a fase começa a contar. Chamado ao
        sair do menu."""
        self.ticks_inicio = pygame.time.get_ticks()

    def tempo_restante_segundos(self):
        """Calcula quantos segundos ainda restam com base no tempo
        decorrido desde o início da fase."""
        decorrido_ms = pygame.time.get_ticks() - self.ticks_inicio
        restante = TEMPO_LIMITE_SEGUNDOS - (decorrido_ms // 1000)
        return max(0, restante)

    def desenhar_cronometro(self):
        """Desenha o cronômetro (mm:ss) no canto superior, mudando
        para vermelho nos últimos 30 segundos."""
        restante = self.tempo_restante_segundos()
        minutos, segundos = divmod(restante, 60)
        texto = f"{minutos:02d}:{segundos:02d}"
        cor = VERMELHO if restante <= 30 else BRANCO

        fundo_rect = pygame.Rect(LARGURA // 2 - 55, 15, 110, 40)
        pygame.draw.rect(self.tela, (0, 0, 0, 150), fundo_rect, border_radius=8)
        render = self.fonte_texto.render(texto, True, cor)
        self.tela.blit(render, render.get_rect(center=fundo_rect.center))

    # -----------------------------------------------------------------
    # TELA: MENU INICIAL (INTRODUÇÃO)
    # -----------------------------------------------------------------
    def desenhar_menu(self):
        self.tela.blit(self.img_fundo_intro, (0, 0))

        linhas_frase = [
            "O computador continua usando válvulas",
            "e está superaquecendo.",
            "Substitua todas pelas novas peças.",
        ]
        y = ALTURA // 2 - 120
        for linha in linhas_frase:
            render = self.fonte_titulo.render(linha, True, BRANCO)
            self.tela.blit(render, render.get_rect(center=(LARGURA // 2, y)))
            y += 46

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_iniciar.collidepoint(mouse_pos) else LARANJA_VALVULA

        pygame.draw.rect(self.tela, cor_botao, self.botao_iniciar, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_iniciar, width=2, border_radius=10)

        texto_botao = self.fonte_texto.render("Iniciar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_iniciar.center))

        instrucao = self.fonte_pequena.render(
            "Clique em Iniciar ou pressione ENTER", True, CINZA_CLARO,
        )
        self.tela.blit(instrucao, instrucao.get_rect(center=(LARGURA // 2, self.botao_iniciar.bottom + 35)))

    # -----------------------------------------------------------------
    # TELA: CENA 1 - SALA + PERSONAGEM + NPC + MAINFRAME FECHADO
    # -----------------------------------------------------------------
    def desenhar_cena1(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect_computador.collidepoint(mouse_pos):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        self.tela.blit(self.img_fundo_cena1, (0, 0))
        self.tela.blit(self.img_computador, self.rect_computador)
        self.tela.blit(self.img_npc, self.rect_npc)
        self.jogador.desenhar(self.tela)

        self.desenhar_cronometro()
        config_fase5.desenhar_icone(self.tela, self.img_config, self.img_config_hover)

        # --- Chatbot do NPC ---
        if self.npc_chat.perto_do_jogador(self.jogador.rect) and not self.npc_chat.dialogo_aberto:
            self.npc_chat.desenhar_dica_interacao(self.tela, self.fonte_pequena)
        self.npc_chat.desenhar(self.tela, self.fonte_texto, self.fonte_pequena, LARGURA, ALTURA)

    def atualizar_cena1(self, teclas):
        if self.npc_chat.dialogo_aberto:
            return
        chegou = self.jogador.mover(teclas, self.limites_sala)
        if chegou and self.proximo_estado_ao_chegar is not None:
            proximo = self.proximo_estado_ao_chegar
            self.proximo_estado_ao_chegar = None
            self.estado = proximo

    # -----------------------------------------------------------------
    # TELA: CENA_DESAFIO - MAINFRAME ABERTO (VÁLVULAS X TRANSISTORES)
    # -----------------------------------------------------------------
    def _valvulas_restantes(self):
        return sum(1 for v in self.valvulas if not v["trocada"])

    def desenhar_cena_desafio(self):
        self.tela.blit(self.img_fundo_desafio, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        sobre_valvula_clicavel = any(
            (not v["trocada"]) and v["rect"].collidepoint(mouse_pos) for v in self.valvulas
        )
        sobre_painel_clicavel = self.sistema_modernizado and self.rect_painel_codigo.collidepoint(mouse_pos)
        if sobre_valvula_clicavel or sobre_painel_clicavel:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # --- Caixa de transistores (decorativa) ---
        self.tela.blit(self.img_caixa_transistores, self.rect_caixa_transistores)

        # --- Grade de válvulas / transistores ---
        tempo_ms = pygame.time.get_ticks()
        for valvula in self.valvulas:
            rect = valvula["rect"]
            if valvula["trocada"]:
                self.tela.blit(self.img_transistor, rect)
            else:
                # Brilho pulsante atrás da válvula ainda ligada, para
                # reforçar a ideia de "válvula brilhando" mesmo com
                # placeholder (o brilho é só um círculo semi-transparente
                # com o alfa oscilando ao longo do tempo).
                alfa = int(90 + 60 * math.sin(tempo_ms / 250 + valvula["id"]))
                raio = max(rect.width, rect.height) // 2 + 12
                brilho = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                pygame.draw.circle(brilho, (*LARANJA_VALVULA, max(0, alfa)), (raio, raio), raio)
                self.tela.blit(brilho, brilho.get_rect(center=rect.center))
                self.tela.blit(self.img_valvula, rect)

        # --- Contador de válvulas restantes ---
        restantes = self._valvulas_restantes()
        texto_contador = self.fonte_texto.render(
            f"Válvulas restantes: {restantes}/{TOTAL_VALVULAS}", True, BRANCO,
        )
        self.tela.blit(texto_contador, texto_contador.get_rect(midtop=(LARGURA // 2, 70)))

        if self.sistema_modernizado:
            texto_ok = self.fonte_texto.render("Sistema modernizado.", True, VERDE)
            self.tela.blit(texto_ok, texto_ok.get_rect(midtop=(LARGURA // 2, 100)))

            # --- Painel com o código, funciona também como "porta" ---
            self.tela.blit(self.img_painel_codigo, self.rect_painel_codigo)
            texto_codigo = self.fonte_codigo.render(CODIGO_PAINEL, True, VERDE)
            self.tela.blit(texto_codigo, texto_codigo.get_rect(center=self.rect_painel_codigo.center))

            dica = self.fonte_pequena.render(
                "Clique no painel para abrir a porta", True, CINZA_CLARO,
            )
            self.tela.blit(dica, dica.get_rect(midtop=(LARGURA // 2, self.rect_painel_codigo.bottom + 10)))
        else:
            dica = self.fonte_pequena.render(
                "Clique em cada válvula acesa para trocá-la por um transistor  |  ESC volta",
                True, CINZA_CLARO,
            )
            self.tela.blit(dica, dica.get_rect(midbottom=(LARGURA // 2, ALTURA - 15)))

        self.desenhar_cronometro()
        config_fase5.desenhar_icone(self.tela, self.img_config, self.img_config_hover)

    def trocar_valvula_em(self, pos):
        """Se `pos` (posição do clique) cair sobre uma válvula ainda não
        trocada, substitui por transistor. Quando a última for trocada,
        marca o sistema como modernizado."""
        if self.sistema_modernizado:
            return
        for valvula in self.valvulas:
            if not valvula["trocada"] and valvula["rect"].collidepoint(pos):
                valvula["trocada"] = True
                break
        if self._valvulas_restantes() == 0:
            self.sistema_modernizado = True

    def abrir_porta_se_clicada(self, pos):
        """Se o painel/porta estiver aceso e o clique cair sobre ele,
        vai para a Vitória e salva o progresso (estrelas + tempo)."""
        if self.sistema_modernizado and self.rect_painel_codigo.collidepoint(pos):
            self.estado = Jogo.VITORIA
            tempo_restante = self.tempo_restante_segundos()
            estrelas = _calcular_estrelas(tempo_restante)
            tempo_gasto = TEMPO_LIMITE_SEGUNDOS - tempo_restante
            _salvar_progresso(estrelas, _formatar_tempo(tempo_gasto))

    # -----------------------------------------------------------------
    # TELAS FINAIS: VITÓRIA / DERROTA
    # -----------------------------------------------------------------
    def desenhar_vitoria(self):
        self.tela.blit(self.img_vitoria, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_continuar_vitoria.collidepoint(mouse_pos) else LARANJA_VALVULA

        pygame.draw.rect(self.tela, cor_botao, self.botao_continuar_vitoria, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_continuar_vitoria, width=2, border_radius=10)

        texto_botao = self.fonte_texto.render("Continuar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_continuar_vitoria.center))

    def desenhar_derrota(self):
        self.tela.blit(self.img_derrota, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_reiniciar_derrota.collidepoint(mouse_pos) else LARANJA_VALVULA

        pygame.draw.rect(self.tela, cor_botao, self.botao_reiniciar_derrota, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_reiniciar_derrota, width=2, border_radius=10)

        texto_botao = self.fonte_texto.render("Tentar novamente", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_reiniciar_derrota.center))

        dica = self.fonte_pequena.render("(ou pressione R)", True, BRANCO)
        self.tela.blit(dica, dica.get_rect(center=(LARGURA // 2, self.botao_reiniciar_derrota.bottom + 25)))

    # -----------------------------------------------------------------
    # REINÍCIO DA FASE
    # -----------------------------------------------------------------
    def reiniciar(self):
        """Reseta a posição do jogador, as válvulas e volta ao menu
        inicial, permitindo jogar novamente."""
        self.jogador.rect.topleft = self.POSICAO_INICIAL_JOGADOR
        for valvula in self.valvulas:
            valvula["trocada"] = False
        self.sistema_modernizado = False
        self.proximo_estado_ao_chegar = None
        self.estado = Jogo.MENU
        self.ticks_inicio = None

    # -----------------------------------------------------------------
    # LAÇO PRINCIPAL DO JOGO
    # -----------------------------------------------------------------
    def executar(self):
        rodando = True
        saiu_por_fechar_janela = False
        while rodando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    saiu_por_fechar_janela = True
                    rodando = False

                elif evento.type == pygame.KEYDOWN:
                    if self.estado == Jogo.MENU and evento.key == pygame.K_RETURN:
                        self.iniciar_cronometro()
                        audio_fase5.iniciar_musica_fundo()
                        self.estado = Jogo.CENA1

                    elif self.estado == Jogo.CENA1:
                        if self.npc_chat.dialogo_aberto:
                            self.npc_chat.tratar_evento(evento)
                        elif evento.key == pygame.K_e and self.npc_chat.perto_do_jogador(self.jogador.rect):
                            self.npc_chat.abrir_dialogo()

                    elif self.estado == Jogo.CENA_DESAFIO and evento.key == pygame.K_ESCAPE:
                        self.estado = Jogo.CENA1

                    elif self.estado in (Jogo.VITORIA, Jogo.DERROTA) and evento.key == pygame.K_r:
                        self.reiniciar()

                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    # Botão de configurações: sempre acessível em qualquer
                    # cena jogável. O painel É o "jogo pausado".
                    if self.estado not in (Jogo.MENU, Jogo.VITORIA, Jogo.DERROTA) and config_fase5.icone_rect(LARGURA).collidepoint(evento.pos):
                        resultado_config = config_fase5.abrir_painel_config(
                            self.tela, self.relogio, self.img_config, self.img_config_hover,
                        )
                        if resultado_config == "sair":
                            rodando = False

                    elif self.estado == Jogo.MENU and self.botao_iniciar.collidepoint(evento.pos):
                        self.iniciar_cronometro()
                        audio_fase5.iniciar_musica_fundo()
                        self.estado = Jogo.CENA1

                    elif self.estado == Jogo.CENA1 and self.rect_computador.collidepoint(evento.pos):
                        self.jogador.mover_ate(self.ponto_interacao_computador)
                        self.proximo_estado_ao_chegar = Jogo.CENA_DESAFIO

                    elif self.estado == Jogo.CENA_DESAFIO and self.sistema_modernizado and self.rect_painel_codigo.collidepoint(evento.pos):
                        self.abrir_porta_se_clicada(evento.pos)

                    elif self.estado == Jogo.CENA_DESAFIO:
                        self.trocar_valvula_em(evento.pos)

                    elif self.estado == Jogo.VITORIA and self.botao_continuar_vitoria.collidepoint(evento.pos):
                        return "vitoria"

                    elif self.estado == Jogo.DERROTA and self.botao_reiniciar_derrota.collidepoint(evento.pos):
                        self.reiniciar()

            # --- Verificação do cronômetro (vale para CENA1 e CENA_DESAFIO) ---
            if self.estado in (Jogo.CENA1, Jogo.CENA_DESAFIO) and self.ticks_inicio is not None:
                if self.tempo_restante_segundos() <= 0:
                    self.estado = Jogo.DERROTA

            # --- Atualização de lógica por estado ---
            if self.estado == Jogo.CENA1:
                teclas = pygame.key.get_pressed()
                self.atualizar_cena1(teclas)

            # --- Desenho por estado ---
            if self.estado == Jogo.MENU:
                self.desenhar_menu()
            elif self.estado == Jogo.CENA1:
                self.desenhar_cena1()
            elif self.estado == Jogo.CENA_DESAFIO:
                self.desenhar_cena_desafio()
            elif self.estado == Jogo.VITORIA:
                self.desenhar_vitoria()
            elif self.estado == Jogo.DERROTA:
                self.desenhar_derrota()

            pygame.display.flip()
            self.relogio.tick(FPS)

        # Fechar a JANELA (evento QUIT) encerra o programa inteiro, igual
        # já acontece nas outras fases (Fase_4/Fase_5/Fase_1/Fase_3/Fase_6/
        # Fase_10). Sair pela tela de configurações ("Sair") devolve
        # controle ao menu geral (None) em vez de matar o processo -- sem
        # isso, o botão "Sair" do painel de configurações encerraria o
        # jogo inteiro em vez de voltar ao mapa de fases.
        if saiu_por_fechar_janela:
            pygame.quit()
            sys.exit()
        return None


# =====================================================================
# 7. PONTO DE ENTRADA DESTA FASE PARA O MENU GERAL
# =====================================================================
def run(character_image=None, character_name=None, genero="m", inventario=None):
    """
    Ponto de entrada desta fase, pronto para ser chamado pelo menu
    geral do jogo (Pygame/menu/jogo.py) -- mesmo contrato usado pela
    Fase 4 (run_fase4/run), Fase 2 e Fase 9:

        modulo.Jogo(
            character_image=CHARACTER_IMAGES.get(self.personagem_index),
            character_name=self.get_personagem_name(self.personagem_index),
            genero="m" if self.personagem_index == 0 else "f",
        ).executar()

    Retorno: a string "vitoria" quando o jogador vence e clica no
    botão "Continuar" da tela de vitória (nada quando a janela é
    fechada, pois o próprio laço encerra o programa nesse caso).
    """
    jogo = Jogo(
        inventario=inventario,
        character_image=character_image,
        character_name=character_name,
        genero=genero,
    )
    return jogo.executar()


def run_padrao():
    """Roda esta fase isolada, fora do menu geral, com o Personagem 1
    como opção padrão (genero="m") -- útil para testar sozinha, sem
    precisar abrir o jogo completo nem passar por nenhum menu."""
    return run(genero="m")


# =====================================================================
# 8. PONTO DE ENTRADA DO PROGRAMA (rodando este arquivo sozinho)
# =====================================================================
if __name__ == "__main__":
    run_padrao()
