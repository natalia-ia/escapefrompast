"""
=====================================================================
Fase_3: A ERA ELETROMECÂNICA DE HERMAN HOLLERITH (cartões perfurados)
=====================================================================

CONTEXTO DA FASE
-----------------
O jogador (a) achava que estava voltando para o presente, mas a
cápsula do tempo parou nesta época: a era das máquinas de tabulação de
Herman Hollerith. Para religar a máquina que alimenta o combustível da
cápsula, é preciso primeiro coletar a caixa de cartões perfurados e
depois decifrar o código escondido em um dos cartões.

ESTRUTURA DO JOGO (máquina de estados)
---------------------------------------
MENU        -> tela de introdução em tom sépia com o texto de contexto
               e o botão "Iniciar".
CENA1       -> sala de 1890 com a caixa de cartões perfurados (item
               colecionável), o personagem, o NPC (Herman Hollerith) e
               a máquina de tabulação. A máquina só fica clicável
               depois que a caixa é coletada.
CENA_CARTAO -> close-up de um cartão perfurado com o enigma (o mesmo
               esquema de blocos de 5 bits por letra da Fase 4, com a
               dica "Pode ter relação com o alfabeto."). O jogador
               digita a palavra decifrada e pressiona ENTER.
VITORIA     -> aparece se o jogador decifrar corretamente DENTRO do
               tempo -- tela simples, só com o texto de vitória.
DERROTA     -> aparece se o tempo acabar antes da resposta correta.

COMO VOCÊ VAI PERSONALIZAR
---------------------------
1. Gere/baixe as imagens (e a fonte sépia) e salve-as numa pasta
   "assets/" ao lado deste arquivo (ou ajuste os caminhos no
   dicionário ASSETS).
2. Enquanto uma imagem não existir, o jogo desenha automaticamente um
   retângulo colorido com um texto no lugar dela (placeholder).
3. Troque PALAVRA_SOLUCAO por qualquer palavra (maiúscula, sem
   acentos) para gerar um enigma novo automaticamente.

Requisitos: pip install pygame
Execução:   python fase3_final.py
=====================================================================
"""

import json
import os
import string
import sys
import pygame
from inventario import Inventario, ItemColecionavel
from npc_chatbot import NPCChatbot
import audio_fase5
import config_fase5

# =====================================================================
# 1. CONFIGURAÇÕES GERAIS DA JANELA E DO JOGO
# =====================================================================
LARGURA, ALTURA = 960, 600
FPS = 60

# Tempo total da fase, em segundos (6 minutos)
TEMPO_LIMITE_SEGUNDOS = 6 * 60


# Cores utilitárias (RGB) usadas em textos e placeholders
BRANCO        = (245, 245, 240)
PRETO         = (15, 15, 15)
CINZA         = (90, 90, 90)
CINZA_CLARO   = (180, 180, 180)
VERDE         = (60, 170, 90)
VERMELHO      = (190, 60, 60)
AMARELO_SEPIA = (196, 164, 96)   # tom sépia da era das tabuladoras
MARROM_CARTAO = (150, 120, 80)   # tom do papelão do cartão perfurado
BG_COLOR      = (8, 10, 22)


# =====================================================================
# 2. CAMINHOS DOS ASSETS -> PREENCHA AQUI COM SUAS IMAGENS
# =====================================================================
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))


def caminho_asset(nome_relativo):
    """Monta o caminho absoluto de um asset a partir da pasta 'assets'
    ao lado deste arquivo .py."""
    return os.path.join(PASTA_DO_SCRIPT, nome_relativo)


# ---------------------------------------------------------------------------
# Progresso (estrelas + tempo) -- mesmo arquivo/formato compartilhado das
# outras fases: {"estrelas": 1-3, "completo": true, "tempo": "MM:SS"}.
# ---------------------------------------------------------------------------
_PYGAME_DIR = os.path.dirname(PASTA_DO_SCRIPT)
PROGRESSO_PATH = os.path.join(_PYGAME_DIR, "progresso.json")
PROGRESSO_CHAVE_FASE = "fase_3"


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
    salvo (mesma regra usada nas outras fases)."""
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
    # Fundo da tela de MENU/INTRODUÇÃO, em tom sépia. Sugestão: 960x600 px.
    "fundo_intro": caminho_asset("assets/fundo_intro_hollerith.png"),

    # Avatar do jogador (2 personagens selecionáveis no menu geral).
    "avatar_parado": caminho_asset("assets/personagem_parado.png"),
    "avatar_andando1": caminho_asset("assets/personagem_andando1.png"),
    "avatar_andando2": caminho_asset("assets/personagem_andando2.png"),
    "avatar2_parado": caminho_asset("assets/personagem2_parado.png"),
    "avatar2_andando1": caminho_asset("assets/personagem2_andando1.png"),
    "avatar2_andando2": caminho_asset("assets/personagem2_andando2.png"),

    # Sprite do NPC (Herman Hollerith). Fundo transparente (PNG).
    "npc": caminho_asset("assets/herman_hollerith.png"),

    # Fundo da CENA 1: sala/escritório de 1890 com a máquina de
    # tabulação e a caixa de cartões. Sugestão: 960x600 px.
    "fundo_cena1": caminho_asset("assets/sala_hollerith.png"),

    # Caixa de cartões perfurados, item colecionável clicável na Cena 1.
    "caixa_cartoes": caminho_asset("assets/caixa_cartoes.png"),

    # Ícone pequeno do item já coletado, mostrado no canto da tela
    # (botão do inventário). Pode reaproveitar a mesma imagem da caixa.
    "icone_item_caixa": caminho_asset("assets/icone_caixa_cartoes.png"),

    # Sprite da máquina de tabulação, só fica clicável depois que a
    # caixa de cartões é coletada.
    "maquina_tabuladora": caminho_asset("assets/maquina_tabuladora.png"),

    # Fundo da CENA_CARTAO: close-up de um cartão perfurado com o
    # enigma. Sugestão: 960x600 px.
    "fundo_cartao": caminho_asset("assets/cartao_perfurado_perto.png"),

    # Ícone quadrado do botão de configurações (canto superior direito).
    "icone_configuracao": caminho_asset("assets/icone_configuracao.png"),

    # Tela final de VITÓRIA (só texto por cima, ex: fundo com o
    # combustível da cápsula liberado). Sugestão: 960x600 px.
    "tela_vitoria": caminho_asset("assets/vitoria_hollerith.png"),

    # Tela final de DERROTA.
    "tela_derrota": caminho_asset("assets/derrota_hollerith.png"),

    # Fonte .ttf baixada (estilo de época). Deixe ausente para usar a
    # fonte padrão do sistema.
    "fonte": caminho_asset("assets/fonte_jogo.ttf"),
}


# =====================================================================
# 3. FUNÇÕES AUXILIARES DE CARREGAMENTO (COM PLACEHOLDER AUTOMÁTICO)
# =====================================================================
def carregar_imagem(caminho, tamanho, cor_placeholder, texto_placeholder):
    """Tenta carregar uma imagem do disco e redimensioná-la para
    'tamanho'. Se o arquivo não existir, gera um placeholder colorido
    com texto, para o jogo continuar funcionando durante os testes."""
    if caminho and os.path.isfile(caminho):
        imagem = pygame.image.load(caminho).convert_alpha()
        return pygame.transform.smoothscale(imagem, tamanho)

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
    return pygame.font.SysFont("georgia", tamanho)


# =====================================================================
# 4. LÓGICA DO ENIGMA (O CARTÃO PERFURADO)
# =====================================================================
# Mesmo esquema da Fase 4: a máquina "perfura" o cartão em blocos de 5
# bits, cada bloco representando um número de 1 a 26 (posição da letra
# no alfabeto: A=1, B=2 ... Z=26). O jogador vê os furos (ou a
# ausência deles) e deve descobrir a palavra -- por isso a dica
# "Pode ter relação com o alfabeto.".
#
# Troque livremente por qualquer palavra em maiúsculas (sem acentos)
# para gerar um enigma novo.
ALFABETO = string.ascii_uppercase  # "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

PALAVRA_SOLUCAO = "CARVAO"  # <-- troque aqui para mudar o enigma


def letra_para_binario(letra):
    """Converte uma letra (A-Z) no código binário de 5 bits
    correspondente à sua posição no alfabeto (A=1 -> 00001,
    B=2 -> 00010, ..., Z=26 -> 11010)."""
    indice = ALFABETO.index(letra.upper()) + 1
    return format(indice, "05b")


def gerar_cartao_perfurado(palavra):
    """Gera a lista de blocos binários (o 'cartão perfurado') a partir
    da palavra-solução. Cada elemento é uma string de 5 dígitos
    ('0'/'1') representando uma letra da palavra -- '1' = furo,
    '0' = sem furo."""
    return [letra_para_binario(letra) for letra in palavra]


CARTAO_PERFURADO = gerar_cartao_perfurado(PALAVRA_SOLUCAO)


# =====================================================================
# 5. CLASSE: CAIXA DE TEXTO PARA A RESPOSTA DO JOGADOR
# =====================================================================
class CaixaDeTexto:
    """Campo de entrada de texto simples para o jogador digitar a
    palavra decifrada. Aceita apenas letras (A-Z) e BACKSPACE."""

    def __init__(self, rect, fonte, tamanho_maximo):
        self.rect = pygame.Rect(rect)
        self.fonte = fonte
        self.texto = ""
        self.tamanho_maximo = tamanho_maximo
        self.ativa = True

    def tratar_evento(self, evento):
        """Processa eventos de teclado enquanto a caixa está ativa.
        Retorna True quando o jogador pressiona ENTER."""
        if not self.ativa or evento.type != pygame.KEYDOWN:
            return False

        if evento.key == pygame.K_RETURN:
            return True
        elif evento.key == pygame.K_BACKSPACE:
            self.texto = self.texto[:-1]
        else:
            tecla = evento.unicode.upper()
            if tecla.isalpha() and len(self.texto) < self.tamanho_maximo:
                self.texto += tecla
        return False

    def desenhar(self, tela):
        pygame.draw.rect(tela, BRANCO, self.rect, border_radius=6)
        pygame.draw.rect(tela, PRETO, self.rect, width=2, border_radius=6)
        texto_render = self.fonte.render(self.texto, True, PRETO)
        tela.blit(
            texto_render,
            (self.rect.x + 10, self.rect.y + (self.rect.height - texto_render.get_height()) // 2),
        )
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = self.rect.x + 10 + texto_render.get_width() + 2
            pygame.draw.line(
                tela, PRETO,
                (cursor_x, self.rect.y + 8),
                (cursor_x, self.rect.y + self.rect.height - 8), 2,
            )


# =====================================================================
# 6. CLASSE: JOGADOR (AVATAR CONTROLÁVEL NA CENA 1)
# =====================================================================
class Jogador:
    """Avatar do jogador. Pode se mover manualmente (teclado) ou
    automaticamente até um destino (quando o jogador clica em um
    objeto interativo, como a caixa de cartões ou a máquina)."""

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
        self.destino = destino
        self.movendo_automaticamente = True

    def mover(self, teclas, limites):
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
# 7. CLASSE PRINCIPAL: O JOGO
# =====================================================================
class Jogo:
    """Controla o laço principal (game loop), a máquina de estados das
    cenas e o cronômetro da fase."""

    MENU = "menu"
    CENA1 = "cena1"
    CENA_CARTAO = "cena_cartao"
    VITORIA = "vitoria"
    DERROTA = "derrota"

    POSICAO_INICIAL_JOGADOR = (80, ALTURA - 300)

    NOME_ITEM_CAIXA = "Caixa de Cartões Perfurados"

    def __init__(self, inventario=None, character_image=None, character_name=None, genero="m"):
        """
        Segue o mesmo contrato usado pelo menu geral do jogo para
        chamar qualquer fase (veja Fase 4 / Fase válvulas):

            modulo.Jogo(
                character_image=CHARACTER_IMAGES.get(self.personagem_index),
                character_name=self.get_personagem_name(self.personagem_index),
                genero="m" if self.personagem_index == 0 else "f",
            ).executar()
        """
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Fase 3 - A era de Hollerith")
        self.relogio = pygame.time.Clock()

        # --- Inventário de colecionáveis (arquivo externo inventario.py) ---
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
        self.fonte_titulo = carregar_fonte(ASSETS["fonte"], 28)
        self.fonte_texto = carregar_fonte(ASSETS["fonte"], 26)
        self.fonte_pequena = carregar_fonte(ASSETS["fonte"], 20)

        # --- Imagens de fundo ---
        self.img_fundo_intro = carregar_imagem(
            ASSETS["fundo_intro"], (LARGURA, ALTURA), AMARELO_SEPIA, "FUNDO DA INTRO\n(tom sépia)",
        )
        self.img_fundo_cena1 = carregar_imagem(
            ASSETS["fundo_cena1"], (LARGURA, ALTURA), AMARELO_SEPIA,
            "FUNDO DA CENA 1\n(sala de Hollerith)",
        )
        self.img_fundo_cartao = carregar_imagem(
            ASSETS["fundo_cartao"], (LARGURA, ALTURA), MARROM_CARTAO,
            "FUNDO DO CARTÃO\n(close-up)",
        )
        self.img_vitoria = carregar_imagem(
            ASSETS["tela_vitoria"], (LARGURA, ALTURA), VERDE, "TELA DE VITÓRIA",
        )
        self.img_derrota = carregar_imagem(
            ASSETS["tela_derrota"], (LARGURA, ALTURA), VERMELHO, "TELA DE DERROTA",
        )

        # --- Sprites de cena ---
        self.img_caixa_cartoes = carregar_imagem(
            ASSETS["caixa_cartoes"], (140, 110), MARROM_CARTAO, "CAIXA DE\nCARTÕES",
        )
        self.img_icone_item_caixa = carregar_imagem(
            ASSETS["icone_item_caixa"], (56, 56), MARROM_CARTAO, "CARTÕES",
        )
        self.img_maquina_tabuladora = carregar_imagem(
            ASSETS["maquina_tabuladora"], (190, 210), (90, 80, 70), "MÁQUINA DE\nTABULAÇÃO",
        )

        # --- Sprites do personagem ---
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

        # --- NPC (Herman Hollerith) ---
        self.img_npc = carregar_imagem(
            ASSETS["npc"], (138, 288), (110, 90, 70), "NPC",
        )
        self.rect_npc = self.img_npc.get_rect(midleft=(500, ALTURA - 180))
        self.npc_chat = NPCChatbot(
            rect_npc=self.rect_npc,
            nome_npc="Herman Hollerith",
            contexto_fase=(
                "Você é Herman Hollerith, inventor da máquina de tabulação de "
                "cartões perfurados, dentro de um jogo de escape room "
                "educativo. Responda SOMENTE perguntas relacionadas a esta "
                "fase: a caixa de cartões perfurados que o jogador precisa "
                "coletar, a máquina de tabulação (que só liga depois da "
                "caixa coletada) e o enigma escondido em um dos cartões, "
                "onde cada bloco de furos representa uma letra do alfabeto "
                "(5 furos possíveis por letra, A=1 até Z=26). Se o jogador "
                "perguntar sobre como ler o cartão, dê a dica de que os "
                "furos têm relação com o alfabeto, sem revelar a palavra "
                "nem o código diretamente. Se o jogador perguntar algo fora "
                "desse tema, responda educadamente que só pode falar sobre "
                "esta fase. Responda sempre em português, em no máximo 3 "
                "frases curtas."
            ),
        )

        # --- Botão "Iniciar" do menu ---
        self.botao_iniciar = pygame.Rect(0, 0, 220, 60)
        self.botao_iniciar.center = (LARGURA // 2, ALTURA - 90)

        # --- Botão "Tentar novamente" da tela de Derrota ---
        self.botao_reiniciar_derrota = pygame.Rect(0, 0, 260, 60)
        self.botao_reiniciar_derrota.center = (LARGURA // 2, ALTURA // 2 + 140)

        # --- Elementos da CENA 1 ---
        self.limites_sala = pygame.Rect(0, 0, LARGURA, ALTURA)

        self.rect_caixa_cartoes = self.img_caixa_cartoes.get_rect(midbottom=(360, ALTURA - 150))
        self.ponto_interacao_caixa = (
            self.rect_caixa_cartoes.centerx,
            self.rect_caixa_cartoes.bottom + 10,
        )

        self.rect_maquina = self.img_maquina_tabuladora.get_rect(midright=(LARGURA - 60, ALTURA - 260))
        self.ponto_interacao_maquina = (
            self.rect_maquina.left - 40,
            self.rect_maquina.bottom - 20,
        )

        # --- Ícone do item coletado, no canto da tela (mesmo espírito
        # do botão de inventário das outras fases: clicar abre/fecha um
        # pequeno painel mostrando o item já coletado) ---
        self.botao_inventario = pygame.Rect(0, 0, 70, 70)
        self.botao_inventario.bottomright = (LARGURA - 20, ALTURA - 20)
        self.mostrar_painel_inventario = False

        self.proximo_estado_ao_chegar = None
        self.acao_ao_chegar = None  # "coletar_caixa" ou None
        self.mensagem_dica_cena1 = ""  # feedback ao clicar na máquina trancada

        # --- Caixa de texto da CENA_CARTAO (resposta do enigma) ---
        self.caixa_resposta = CaixaDeTexto(
            rect=(LARGURA // 2 - 150, 430, 300, 50),
            fonte=self.fonte_texto,
            tamanho_maximo=len(PALAVRA_SOLUCAO),
        )
        self.mensagem_erro = ""

        # --- Estado do jogo ---
        self.estado = Jogo.MENU
        self.ticks_inicio = None

    # -----------------------------------------------------------------
    # CONTROLE DE TEMPO
    # -----------------------------------------------------------------
    def iniciar_cronometro(self):
        self.ticks_inicio = pygame.time.get_ticks()

    def tempo_restante_segundos(self):
        decorrido_ms = pygame.time.get_ticks() - self.ticks_inicio
        restante = TEMPO_LIMITE_SEGUNDOS - (decorrido_ms // 1000)
        return max(0, restante)

    def desenhar_cronometro(self):
        restante = self.tempo_restante_segundos()
        minutos, segundos = divmod(restante, 60)
        texto = f"{minutos:02d}:{segundos:02d}"
        cor = VERMELHO if restante <= 30 else BRANCO

        fundo_rect = pygame.Rect(LARGURA // 2 - 55, 15, 110, 40)
        pygame.draw.rect(self.tela, (0, 0, 0, 150), fundo_rect, border_radius=8)
        render = self.fonte_texto.render(texto, True, cor)
        self.tela.blit(render, render.get_rect(center=fundo_rect.center))

    # -----------------------------------------------------------------
    # TELA: MENU INICIAL (INTRODUÇÃO EM TOM SÉPIA)
    # -----------------------------------------------------------------
    def desenhar_menu(self):
        self.tela.blit(self.img_fundo_intro, (0, 0))

        # Uma camada semi-transparente escura por trás do texto ajuda a
        # leitura em cima de qualquer fundo sépia que você adicionar.
        camada = pygame.Surface((LARGURA, 230), pygame.SRCALPHA)
        camada.fill((30, 22, 10, 150))
        self.tela.blit(camada, (0, ALTURA // 2 - 165))

        linhas_frase = [
            "Pensei que estivesse retornando ao ano do presente,",
            "mas percebi que parei no tempo. Agora preciso decifrar",
            "o código desses cartões que vão liberar a máquina com",
            "combustível que alimenta a cápsula do tempo.",
        ]
        y = ALTURA // 2 - 130
        for linha in linhas_frase:
            render = self.fonte_titulo.render(linha, True, BRANCO)
            self.tela.blit(render, render.get_rect(center=(LARGURA // 2, y)))
            y += 40

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_iniciar.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_iniciar, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_iniciar, width=2, border_radius=10)

        texto_botao = self.fonte_texto.render("Iniciar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_iniciar.center))

        instrucao = self.fonte_pequena.render(
            "Clique em Iniciar ou pressione ENTER", True, CINZA_CLARO,
        )
        self.tela.blit(instrucao, instrucao.get_rect(center=(LARGURA // 2, self.botao_iniciar.bottom + 35)))

    # -----------------------------------------------------------------
    # TELA: CENA 1 - SALA + CAIXA DE CARTÕES + PERSONAGEM + NPC + MÁQUINA
    # -----------------------------------------------------------------
    def _caixa_coletada(self):
        return self.inventario.possui(self.NOME_ITEM_CAIXA)

    def desenhar_cena1(self):
        mouse_pos = pygame.mouse.get_pos()
        pontos_clicaveis = []
        if not self._caixa_coletada():
            pontos_clicaveis.append(self.rect_caixa_cartoes)
        if self._caixa_coletada():
            pontos_clicaveis.append(self.rect_maquina)
        if any(rect.collidepoint(mouse_pos) for rect in pontos_clicaveis):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        self.tela.blit(self.img_fundo_cena1, (0, 0))

        # A caixa de cartões some da cena assim que é coletada (foi
        # para o inventário, no canto da tela).
        if not self._caixa_coletada():
            self.tela.blit(self.img_caixa_cartoes, self.rect_caixa_cartoes)

        # A máquina aparece "apagada" (mais escura) até a caixa ser
        # coletada, reforçando visualmente que ainda não está liberada.
        if self._caixa_coletada():
            self.tela.blit(self.img_maquina_tabuladora, self.rect_maquina)
        else:
            sombra = self.img_maquina_tabuladora.copy()
            escurecida = pygame.Surface(sombra.get_size(), pygame.SRCALPHA)
            escurecida.fill((0, 0, 0, 140))
            sombra.blit(escurecida, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.tela.blit(sombra, self.rect_maquina)

        self.tela.blit(self.img_npc, self.rect_npc)
        self.jogador.desenhar(self.tela)

        self.desenhar_cronometro()
        self.desenhar_icone_inventario()
        config_fase5.desenhar_icone(self.tela, self.img_config, self.img_config_hover)

        if self.mensagem_dica_cena1:
            aviso = self.fonte_pequena.render(self.mensagem_dica_cena1, True, AMARELO_SEPIA)
            self.tela.blit(aviso, aviso.get_rect(midbottom=(LARGURA // 2, ALTURA - 15)))

        if self.npc_chat.perto_do_jogador(self.jogador.rect) and not self.npc_chat.dialogo_aberto:
            self.npc_chat.desenhar_dica_interacao(self.tela, self.fonte_pequena)
        self.npc_chat.desenhar(self.tela, self.fonte_texto, self.fonte_pequena, LARGURA, ALTURA)

        if self.mostrar_painel_inventario:
            self.desenhar_painel_inventario()

    def atualizar_cena1(self, teclas):
        if self.npc_chat.dialogo_aberto:
            return
        chegou = self.jogador.mover(teclas, self.limites_sala)
        if not chegou:
            return

        if self.acao_ao_chegar == "coletar_caixa":
            self.acao_ao_chegar = None
            self._coletar_caixa()
        elif self.proximo_estado_ao_chegar is not None:
            proximo = self.proximo_estado_ao_chegar
            self.proximo_estado_ao_chegar = None
            self.estado = proximo

    def _coletar_caixa(self):
        """Adiciona a caixa de cartões perfurados ao inventário (usando
        o Inventario/ItemColecionavel de inventario.py). A caixa some da
        cena e passa a aparecer só como ícone no canto da tela."""
        if self._caixa_coletada():
            return
        item = ItemColecionavel(
            nome=self.NOME_ITEM_CAIXA,
            descricao="Uma caixa cheia de cartões perfurados. Um deles parece ter um código escondido.",
        )
        self.inventario.adicionar(item)

    # -----------------------------------------------------------------
    # ÍCONE / PAINEL DO INVENTÁRIO (CANTO DA TELA)
    # -----------------------------------------------------------------
    def desenhar_icone_inventario(self):
        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.rect(self.tela, (30, 24, 16), self.botao_inventario, border_radius=12)
        cor_borda = AMARELO_SEPIA if self.botao_inventario.collidepoint(mouse_pos) else CINZA_CLARO
        pygame.draw.rect(self.tela, cor_borda, self.botao_inventario, width=2, border_radius=12)

        if self._caixa_coletada():
            icone = pygame.transform.smoothscale(self.img_icone_item_caixa, (50, 50))
            self.tela.blit(icone, icone.get_rect(center=self.botao_inventario.center))
        else:
            interrogacao = self.fonte_texto.render("?", True, CINZA_CLARO)
            self.tela.blit(interrogacao, interrogacao.get_rect(center=self.botao_inventario.center))

    def desenhar_painel_inventario(self):
        painel_rect = pygame.Rect(0, 0, 320, 220)
        painel_rect.bottomright = (self.botao_inventario.left - 10, self.botao_inventario.bottom)

        superficie = pygame.Surface(painel_rect.size, pygame.SRCALPHA)
        superficie.fill((20, 16, 10, 230))
        self.tela.blit(superficie, painel_rect.topleft)
        pygame.draw.rect(self.tela, AMARELO_SEPIA, painel_rect, width=2, border_radius=10)

        titulo = self.fonte_pequena.render("Itens coletados", True, AMARELO_SEPIA)
        self.tela.blit(titulo, titulo.get_rect(midtop=(painel_rect.centerx, painel_rect.top + 12)))

        if self.inventario.quantidade() == 0:
            vazio = self.fonte_pequena.render("(nenhum item ainda)", True, CINZA_CLARO)
            self.tela.blit(vazio, vazio.get_rect(center=painel_rect.center))
        else:
            y = painel_rect.top + 55
            for item in self.inventario.itens:
                nome_render = self.fonte_pequena.render(f"- {item.nome}", True, BRANCO)
                self.tela.blit(nome_render, (painel_rect.left + 20, y))
                y += 28

        dica = self.fonte_pequena.render("Clique no ícone para fechar", True, CINZA_CLARO)
        self.tela.blit(dica, dica.get_rect(midbottom=(painel_rect.centerx, painel_rect.bottom - 12)))

    # -----------------------------------------------------------------
    # TELA: CENA_CARTAO - CLOSE-UP DO CARTÃO PERFURADO + ENIGMA
    # -----------------------------------------------------------------
    def desenhar_cena_cartao(self):
        self.tela.blit(self.img_fundo_cartao, (0, 0))
        self.desenhar_cronometro()
        config_fase5.desenhar_icone(self.tela, self.img_config, self.img_config_hover)

        titulo = self.fonte_texto.render("Decifre o código do cartão", True, BRANCO)
        self.tela.blit(titulo, titulo.get_rect(midtop=(LARGURA // 2, 40)))

        dica = self.fonte_pequena.render("Dica: Pode ter relação com o alfabeto.", True, AMARELO_SEPIA)
        self.tela.blit(dica, dica.get_rect(midtop=(LARGURA // 2, 80)))

        # --- Desenha o cartão com os furos (blocos de 5 bits, um por
        # letra da palavra-solução) ---
        largura_bloco = 46
        espaco_entre_blocos = 14
        largura_total = len(CARTAO_PERFURADO) * largura_bloco + (len(CARTAO_PERFURADO) - 1) * espaco_entre_blocos
        x_inicial = LARGURA // 2 - largura_total // 2
        y_topo_furos = 150
        espaco_entre_furos = 30
        raio_furo = 9

        cartao_rect = pygame.Rect(x_inicial - 20, y_topo_furos - 30, largura_total + 40, 5 * espaco_entre_furos + 60)
        pygame.draw.rect(self.tela, MARROM_CARTAO, cartao_rect, border_radius=6)
        pygame.draw.rect(self.tela, PRETO, cartao_rect, width=2, border_radius=6)

        for indice_bloco, bloco in enumerate(CARTAO_PERFURADO):
            x_bloco = x_inicial + indice_bloco * (largura_bloco + espaco_entre_blocos) + largura_bloco // 2
            for indice_bit, bit in enumerate(bloco):
                y_furo = y_topo_furos + indice_bit * espaco_entre_furos
                if bit == "1":
                    pygame.draw.circle(self.tela, PRETO, (x_bloco, y_furo), raio_furo)
                else:
                    pygame.draw.circle(self.tela, PRETO, (x_bloco, y_furo), raio_furo, width=2)

        # --- Caixa de resposta ---
        instrucao = self.fonte_pequena.render(
            "Digite a palavra decifrada e pressione ENTER  |  ESC volta", True, CINZA_CLARO,
        )
        self.tela.blit(instrucao, instrucao.get_rect(midtop=(LARGURA // 2, self.caixa_resposta.rect.top - 30)))
        self.caixa_resposta.desenhar(self.tela)

        if self.mensagem_erro:
            erro = self.fonte_pequena.render(self.mensagem_erro, True, VERMELHO)
            self.tela.blit(erro, erro.get_rect(midtop=(LARGURA // 2, self.caixa_resposta.rect.bottom + 15)))

    def validar_resposta(self):
        """Compara o texto digitado com PALAVRA_SOLUCAO. Se estiver
        correto, vai para a Vitória e salva o progresso (estrelas +
        tempo, calculados com o tempo que sobrou no timer)."""
        if self.caixa_resposta.texto == PALAVRA_SOLUCAO:
            self.estado = Jogo.VITORIA
            tempo_restante = self.tempo_restante_segundos()
            estrelas = _calcular_estrelas(tempo_restante)
            tempo_gasto = TEMPO_LIMITE_SEGUNDOS - tempo_restante
            _salvar_progresso(estrelas, _formatar_tempo(tempo_gasto))
        else:
            self.mensagem_erro = "Código incorreto. Tente novamente!"
            self.caixa_resposta.texto = ""

    # -----------------------------------------------------------------
    # TELAS FINAIS: VITÓRIA / DERROTA
    # -----------------------------------------------------------------
    def desenhar_vitoria(self):
        """Tela de vitória simples, apenas com o texto -- sem botões
        nem elementos extras. ENTER continua para o menu principal."""
        self.tela.blit(self.img_vitoria, (0, 0))

        linhas = [
            "Você decifrou o código do cartão!",
            "A máquina liberou o combustível da cápsula do tempo.",
        ]
        y = ALTURA // 2 - 30
        for linha in linhas:
            render = self.fonte_titulo.render(linha, True, BRANCO)
            self.tela.blit(render, render.get_rect(center=(LARGURA // 2, y)))
            y += 44

        instrucao = self.fonte_pequena.render("Pressione ENTER para continuar", True, CINZA_CLARO)
        self.tela.blit(instrucao, instrucao.get_rect(center=(LARGURA // 2, y + 20)))

    def desenhar_derrota(self):
        self.tela.blit(self.img_derrota, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_reiniciar_derrota.collidepoint(mouse_pos) else AMARELO_SEPIA

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
        """Reseta a posição do jogador e a caixa de resposta e volta ao
        menu inicial. Note que o item já coletado no inventário NÃO é
        removido (mesmo espírito das outras fases: o inventário
        acompanha o jogador entre tentativas/fases)."""
        self.jogador.rect.topleft = self.POSICAO_INICIAL_JOGADOR
        self.caixa_resposta.texto = ""
        self.mensagem_erro = ""
        self.mensagem_dica_cena1 = ""
        self.proximo_estado_ao_chegar = None
        self.acao_ao_chegar = None
        self.mostrar_painel_inventario = False
        self.estado = Jogo.MENU
        self.ticks_inicio = None

    # -----------------------------------------------------------------
    # LAÇO PRINCIPAL DO JOGO
    # -----------------------------------------------------------------
    def executar(self):
        rodando = True
        while rodando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
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

                    elif self.estado == Jogo.CENA_CARTAO:
                        if evento.key == pygame.K_ESCAPE:
                            self.estado = Jogo.CENA1
                        else:
                            enter_pressionado = self.caixa_resposta.tratar_evento(evento)
                            if enter_pressionado:
                                self.validar_resposta()

                    elif self.estado == Jogo.VITORIA and evento.key == pygame.K_RETURN:
                        return "vitoria"

                    elif self.estado == Jogo.DERROTA and evento.key == pygame.K_r:
                        self.reiniciar()

                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    # Botão de configurações: sempre acessível em qualquer
                    # cena jogável.
                    if self.estado in (Jogo.CENA1, Jogo.CENA_CARTAO) and config_fase5.icone_rect(LARGURA).collidepoint(evento.pos):
                        resultado_config = config_fase5.abrir_painel_config(
                            self.tela, self.relogio, self.img_config, self.img_config_hover,
                        )
                        if resultado_config == "sair":
                            rodando = False

                    elif self.estado == Jogo.MENU and self.botao_iniciar.collidepoint(evento.pos):
                        self.iniciar_cronometro()
                        audio_fase5.iniciar_musica_fundo()
                        self.estado = Jogo.CENA1

                    # Ícone do inventário -> abre/fecha o painel (Cena 1)
                    elif self.estado == Jogo.CENA1 and self.botao_inventario.collidepoint(evento.pos):
                        self.mostrar_painel_inventario = not self.mostrar_painel_inventario

                    # Clique na caixa de cartões (ainda não coletada) -> anda
                    # até ela e coleta ao chegar
                    elif (self.estado == Jogo.CENA1 and not self._caixa_coletada()
                          and self.rect_caixa_cartoes.collidepoint(evento.pos)):
                        self.jogador.mover_ate(self.ponto_interacao_caixa)
                        self.acao_ao_chegar = "coletar_caixa"
                        self.mensagem_dica_cena1 = ""

                    # Clique na máquina: só funciona se a caixa já foi
                    # coletada -- senão, mostra uma dica.
                    elif self.estado == Jogo.CENA1 and self.rect_maquina.collidepoint(evento.pos):
                        if self._caixa_coletada():
                            self.jogador.mover_ate(self.ponto_interacao_maquina)
                            self.proximo_estado_ao_chegar = Jogo.CENA_CARTAO
                            self.mensagem_dica_cena1 = ""
                        else:
                            self.mensagem_dica_cena1 = "Colete a caixa de cartões perfurados primeiro."

                    elif self.estado == Jogo.DERROTA and self.botao_reiniciar_derrota.collidepoint(evento.pos):
                        self.reiniciar()

                    # Clique em qualquer lugar da tela de Vitória também
                    # continua (a tela só tem texto, sem botão).
                    elif self.estado == Jogo.VITORIA:
                        return "vitoria"

            # --- Verificação do cronômetro (vale para CENA1 e CENA_CARTAO) ---
            if self.estado in (Jogo.CENA1, Jogo.CENA_CARTAO) and self.ticks_inicio is not None:
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
            elif self.estado == Jogo.CENA_CARTAO:
                self.desenhar_cena_cartao()
            elif self.estado == Jogo.VITORIA:
                self.desenhar_vitoria()
            elif self.estado == Jogo.DERROTA:
                self.desenhar_derrota()

            pygame.display.flip()
            self.relogio.tick(FPS)

        pygame.quit()
        sys.exit()


# =====================================================================
# 8. PONTO DE ENTRADA DESTA FASE PARA O MENU GERAL
# =====================================================================
def run(character_image=None, character_name=None, genero="m", inventario=None):
    """
    Ponto de entrada da Fase 3, pronto para ser chamado pelo menu geral
    do jogo (Pygame/menu/jogo.py) -- mesmo contrato usado pela Fase 4 e
    pela fase das válvulas:

        modulo.Jogo(
            character_image=CHARACTER_IMAGES.get(self.personagem_index),
            character_name=self.get_personagem_name(self.personagem_index),
            genero="m" if self.personagem_index == 0 else "f",
        ).executar()

    Retorno: a string "vitoria" quando o jogador vence e sai da tela de
    vitória (via ENTER ou clique -- a tela só tem texto, sem botão).
    """
    jogo = Jogo(
        inventario=inventario,
        character_image=character_image,
        character_name=character_name,
        genero=genero,
    )
    return jogo.executar()


def run_padrao():
    """Roda a Fase 3 isolada, fora do menu geral, com o Personagem 1
    como opção padrão (genero="m")."""
    return run(genero="m")


# =====================================================================
# 9. PONTO DE ENTRADA DO PROGRAMA (rodando este arquivo sozinho)
# =====================================================================
if __name__ == "__main__":
    run_padrao()
