"""
=====================================================================
Fase_4: A MÁQUINA DE TURING (1936) 
=====================================================================

CONTEXTO DA FASE
-----------------
Estamos em 1936. O jogador (a) acorda em uma sala e encontra, ao lado,
a Máquina de Turing. Para sair, precisa decifrar um código gerado pela
máquina (uma "fita" com blocos de 0s e 1s) dentro de um tempo limite
de 5 minutos.

ESTRUTURA DO JOGO (máquina de estados)
---------------------------------------
MENU      -> tela inicial, pressione ENTER para começar
CENA1     -> sala com o personagem (avatar) e a Máquina de Turing ao
             lado. O jogador anda até a máquina e pressiona E para
             interagir.
CENA2     -> close-up da máquina + o enigma (a "fita" binária). O
             jogador digita a palavra decifrada e pressiona ENTER.
VITORIA   -> aparece se o jogador decifrar corretamente DENTRO do
             tempo -> "Você concluiu, parabéns!"
DERROTA   -> aparece se o tempo (10 min) acabar antes da resposta
             correta -> "Que pena! Você não concluiu"

COMO VOCÊ VAI PERSONALIZAR
---------------------------
1. Gere/baixe as imagens e salve-as numa pasta "assets/" ao lado deste
   arquivo (ou ajuste os caminhos).
2. Preencha o dicionário ASSETS (logo abaixo) com os caminhos dos
   arquivos.
3. Enquanto uma imagem não existir, o jogo desenha automaticamente um
   retângulo colorido com um texto no lugar dela (placeholder), então
   você pode testar a lógica do jogo antes de ter todas as artes prontas.

Requisitos: pip install pygame
Execução:   python escape_room_turing.py
=====================================================================
"""

import os
import string
import sys
import math
import pygame
from inventario import Inventario, ItemColecionavel
from npc_chatbot import NPCChatbot

# =====================================================================
# 1. CONFIGURAÇÕES GERAIS DA JANELA E DO JOGO
# =====================================================================
LARGURA, ALTURA = 960, 600
FPS = 60

# Tempo total da fase, em segundos (5 minutos)
TEMPO_LIMITE_SEGUNDOS = 5 * 60
FADE_DURATION_SECONDS = 0.35 # transição de tela

# Cores utilitárias (RGB) usadas em textos e placeholders
BRANCO      = (245, 245, 240)
PRETO       = (15, 15, 15)
CINZA       = (90, 90, 90)
CINZA_CLARO = (180, 180, 180)
VERDE       = (60, 170, 90)
VERMELHO    = (190, 60, 60)
AMARELO_SEPIA = (196, 164, 96)   # tom "vintage" para combinar com 1936
AZUL_TURING   = (70, 110, 150)
BG_COLOR = (8, 10, 22)


# =====================================================================
# 2. CAMINHOS DOS ASSETS -> PREENCHA AQUI COM SUAS IMAGENS
# =====================================================================
# Dica: crie uma pasta "assets" ao lado deste arquivo .py e salve suas
# imagens lá dentro. Formatos aceitos: .png (recomendado, com
# transparência) ou .jpg.

# Garante que os caminhos de assets funcionem não importa de onde o
# script seja executado (ex: terminal na raiz do projeto, ou o botão
# "Run" do VS Code) — usamos a pasta onde ESTE ARQUIVO está salvo
# como referência, e não a pasta de onde o programa foi chamado.
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))

def caminho_asset(nome_relativo):
    """Monta o caminho absoluto de um asset a partir da pasta 'assets'
    ao lado deste arquivo .py."""
    return os.path.join(PASTA_DO_SCRIPT, nome_relativo)


ASSETS = {
    # Fundo da tela de MENU/INTRODUÇÃO inicial.
    # Sugestão de tamanho: 960x600 px (igual à janela do jogo).
    "fundo_intro": caminho_asset("assets/fundo_intro.png"),

    # Avatar do jogador (spritesheet simples ou imagem única).
    # Sugestão de tamanho: 64x96 px, fundo transparente (PNG).
    "avatar_parado": caminho_asset("assets/personagem_parado.png"),
    "avatar_andando1": caminho_asset("assets/personagem_andando1.png"),
    "avatar_andando2": caminho_asset("assets/personagem_andando2.png"),

    # Sprite do NPC (personagem parado na sala, sem interação por
    # enquanto). Fundo transparente (PNG). Mesmo tamanho do avatar.
    "npc": caminho_asset("assets/professor_turing.png"),

    # Fundo da CENA 1: uma sala de 1936 (mobília de época, janela,
    # penumbra) com espaço vazio de um dos lados para a máquina.
    # Sugestão de tamanho: 960x600 px (igual à janela do jogo).
    "fundo_cena1": caminho_asset("assets/sala_1936.png"),
    "livro": caminho_asset("assets/livro.png"),
    "fundo_cena_dica": caminho_asset("assets/cena_dica.png"),

    # Sprite da Máquina de Turing que fica "dentro" da Cena 1
    # (parada, aguardando interação). Fundo transparente (PNG).
    "maquina": caminho_asset("assets/maquina_turing.png"),

    # Fundo da CENA DA DICA 2: o bilhete que saiu da máquina,
    # revelando que a senha da cápsula do tempo é "Bombe".
    "fundo_cena_dica2": caminho_asset("assets/cena_dica2_bilhete.png"),

    # Fundo da CENA 2: close-up da máquina, mostrando o painel/fita
    # onde o enigma binário será exibido por cima.
    # Sugestão de tamanho: 960x600 px.
    "fundo_cena2": caminho_asset("assets/maquina_perto.png"),

    # Fundo da CENA 3: continuação da sala da Cena 1 (mesmo ambiente,
    # "mais um pedaço" da sala), com espaço para o computador.
    # Sugestão de tamanho: 960x600 px.
    "fundo_cena3": caminho_asset("assets/sala_1936_parte2.png"),

    # Sprite do computador, objeto clicável da Cena 3 (mesma posição
    # da máquina na Cena 1). Fundo transparente (PNG).
    "computador": caminho_asset("assets/computador.png"),

    # Fundo da CENA 4: close-up do computador/cápsula, com a caixa
    # de validação da senha "Bombe". Sugestão de tamanho: 960x600 px.
    "fundo_cena4": caminho_asset("assets/computador_perto.png"),

    # Ícone de seta, usado na Cena 1 para ir até a Cena 3.
    "seta_direita": caminho_asset("assets/seta_direita.png"),

    # Tela final de VITÓRIA (ex: porta se abrindo, luz do lado de fora).
    "tela_vitoria": caminho_asset("assets/vitoria.png"),

    # Tela final de DERROTA (ex: sala escurecendo, relógio parado).
    "tela_derrota": caminho_asset("assets/derrota.png"),

    # (Opcional) Fonte .ttf com estilo de "máquina de escrever" de
    # época. Deixe None para usar a fonte padrão do sistema.
    "fonte": caminho_asset("assets/fonte_jogo.ttf")
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

    Retorna:
        pygame.Surface pronta para ser desenhada com screen.blit(...)
    """
    if caminho and os.path.isfile(caminho):
        imagem = pygame.image.load(caminho).convert_alpha()
        return pygame.transform.smoothscale(imagem, tamanho)

    # --- PLACEHOLDER (usado enquanto o asset real não existe) ---
    superficie = pygame.Surface(tamanho, pygame.SRCALPHA)
    superficie.fill(cor_placeholder)
    pygame.draw.rect(superficie, PRETO, superficie.get_rect(), width=3)

    fonte = pygame.font.SysFont("arial", 18, bold=True)
    linhas = texto_placeholder.split("\n")
    y = tamanho[1] // 2 - (len(linhas) * 22) // 2
    for linha in linhas:
        texto_render = fonte.render(linha, True, PRETO)
        rect_texto = texto_render.get_rect(center=(tamanho[0] // 2, y))
        superficie.blit(texto_render, rect_texto)
        y += 22
    return superficie


def carregar_fonte(caminho, tamanho):
    """Carrega uma fonte customizada (.ttf) se disponível, ou usa uma
    fonte padrão do sistema como alternativa."""
    if caminho and os.path.isfile(caminho):
        return pygame.font.Font(caminho, tamanho)
    return pygame.font.SysFont("georgia", tamanho)


# =====================================================================
# 4. LÓGICA DO ENIGMA (A "FITA" DA MÁQUINA DE TURING)
# =====================================================================
# A ideia do enigma: a máquina "imprime" uma fita com blocos de 5 bits.
# Cada bloco de 5 bits representa um número de 1 a 26, que corresponde
# à posição de uma letra no alfabeto (A=1, B=2, C=3 ... Z=26). O
# jogador precisa converter cada bloco binário na letra correspondente
# e formar a palavra-código.
#
# Você pode trocar livremente a PALAVRA_SOLUCAO abaixo por qualquer
# outra palavra em maiúsculas (sem acentos) para gerar um enigma novo
# automaticamente — a fita binária é calculada a partir dela.

ALFABETO = string.ascii_uppercase  # "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

PALAVRA_SOLUCAO = "ATAQUE"  # <-- troque aqui para mudar o enigma

def letra_para_binario(letra):
    """Converte uma letra (A-Z) no código binário de 5 bits
    correspondente à sua posição no alfabeto (A=1 -> 00001,
    B=2 -> 00010, ..., Z=26 -> 11010)."""
    indice = ALFABETO.index(letra.upper()) + 1
    return format(indice, "05b")


def gerar_fita_binaria(palavra):
    """Gera a lista de blocos binários (a 'fita' da máquina) a partir
    da palavra-solução. Cada elemento da lista é uma string de 5
    dígitos ('0'/'1') representando uma letra da palavra."""
    return [letra_para_binario(letra) for letra in palavra]


FITA_BINARIA = gerar_fita_binaria(PALAVRA_SOLUCAO)

# Senha da cápsula do tempo, revelada no bilhete da Cena de Dica 2 e
# usada para validar a resposta na Cena 4 (não tem "quebra-cabeça",
# é só conferir se o jogador digitou a palavra certa).
SENHA_CAPSULA = "BOMBE"


# =====================================================================
# 5. CLASSE: CAIXA DE TEXTO PARA A RESPOSTA DO JOGADOR (CENA 2)
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
        Retorna True quando o jogador pressiona ENTER (pedindo para
        validar a resposta)."""
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
        # Cursor piscante simples
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
    objeto interativo, como a Máquina de Turing)."""

    VELOCIDADE = 4
    INTERVALO_ANIMACAO_MS = 150

    def __init__(self, frame_parado, frames_andando, posicao_inicial):
        self.frame_parado = frame_parado
        self.frames_andando = frames_andando
        self.indice_animacao = 0
        self.tempo_ultimo_frame = pygame.time.get_ticks()
        

        self.imagem = self.frame_parado
        self.rect = self.imagem.get_rect(topleft=posicao_inicial)
        self.olhando_para_esquerda = False  # direção atual do personagem
        
        # --- Controle do movimento automático (point-and-click) ---
        self.destino = None
        self.movendo_automaticamente = False

    def mover_ate(self, destino):
        """Inicia o deslocamento automático do jogador até o ponto
        'destino' (tupla x, y). Chamado quando o jogador clica em um
        objeto interativo, como a máquina."""
        self.destino = destino
        self.movendo_automaticamente = True

    def mover(self, teclas, limites):
        """Move o jogador (manual ou automaticamente) e atualiza a
        animação. Retorna True no frame exato em que o destino
        automático é alcançado (para o Jogo saber que deve trocar
        de cena)."""
        
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
        """Calcula o próximo passo (dx) na direção do destino, apenas no
        eixo X. Retorna 0 quando já está perto o suficiente (chegou)."""
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

            # Espelha horizontalmente se o personagem estiver olhando para a esquerda
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

    # Estados possíveis da fase
    MENU = "menu"
    CENA1 = "cena1"
    CENA2 = "cena2"
    CENA_DICA = "cena_dica"
    CENA_DICA_2 = "cena_dica_2"
    CENA3 = "cena3"
    CENA4 = "cena4"
    VITORIA = "vitoria"
    DERROTA = "derrota"


    def __init__(self, inventario=None):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Fase 4 - Os fundamentos teóricos")
        self.relogio = pygame.time.Clock()

        # --- Inventário de colecionáveis --- (ADICIONE ESSE BLOCO)
        self.inventario = inventario if inventario is not None else Inventario()

        # --- Fontes ---
        self.fonte_titulo = carregar_fonte(ASSETS["fonte"], 30)
        self.fonte_texto = carregar_fonte(ASSETS["fonte"], 26)
        self.fonte_pequena = carregar_fonte(ASSETS["fonte"], 20)

        # --- Carregamento de imagens (com placeholder automático) ---
        self.img_fundo_intro = carregar_imagem(
            ASSETS["fundo_intro"], (LARGURA, ALTURA), PRETO, "FUNDO DA INTRO",
        )
        self.img_fundo_cena1 = carregar_imagem(
            ASSETS["fundo_cena1"], (LARGURA, ALTURA), AMARELO_SEPIA,
            "FUNDO DA CENA 1\n(sala de 1936)",
        )
        self.img_fundo_cena2 = carregar_imagem(
            ASSETS["fundo_cena2"], (LARGURA, ALTURA), (60, 60, 70),
            "FUNDO DA CENA 2\n(close-up da máquina)",
        )
        self.img_maquina = carregar_imagem(
            ASSETS["maquina"], (200, 146), AZUL_TURING, "MÁQUINA DE\nTURING",
        )

        # --- Assets da CENA 3 (continuação da sala) e CENA 4 (computador de perto) ---
        self.img_fundo_cena3 = carregar_imagem(
            ASSETS["fundo_cena3"], (LARGURA, ALTURA), AMARELO_SEPIA,
            "FUNDO DA CENA 3\n(continuação da sala)",
        )
        self.img_computador = carregar_imagem(
            ASSETS["computador"], (150, 100), AZUL_TURING, "COMPUTADOR",
        )
        self.img_fundo_cena4 = carregar_imagem(
            ASSETS["fundo_cena4"], (LARGURA, ALTURA), (60, 60, 70),
            "FUNDO DA CENA 4\n(close-up do computador)",
        )
        # Seta de navegação (Cena 1 -> Cena 3). Enquanto não houver
        # imagem própria, é desenhado um triângulo simples no lugar
        # (veja desenhar_seta_avancar).
        self.img_seta_direita = carregar_imagem(
            ASSETS["seta_direita"], (60, 60), (0, 0, 0), "",
        ) if os.path.isfile(ASSETS["seta_direita"]) else None
        self.img_avatar_parado = carregar_imagem(
            ASSETS["avatar_parado"], (138, 288), CINZA, "PARADO",
        )
        self.img_avatar_andando1 = carregar_imagem(
            ASSETS["avatar_andando1"], (138, 288), CINZA, "ANDANDO 1",
        )
        self.img_avatar_andando2 = carregar_imagem(
            ASSETS["avatar_andando2"], (138, 288), CINZA, "ANDANDO 2",
        )

        self.jogador = Jogador(
            frame_parado=self.img_avatar_parado,
            frames_andando=[self.img_avatar_andando1, self.img_avatar_andando2],
            posicao_inicial=(80, ALTURA - 300),
        )

        self.img_npc = carregar_imagem(
            ASSETS["npc"], (138, 288), (110, 90, 130), "NPC",
        )
        self.img_livro = carregar_imagem(
            ASSETS["livro"], (50, 60), AMARELO_SEPIA, "LIVRO",
        )
        self.img_fundo_cena_dica = carregar_imagem(
            ASSETS["fundo_cena_dica"], (LARGURA, ALTURA), (70, 55, 40),
            "FUNDO DA CENA\nDE DICA",
        )
        self.img_fundo_cena_dica2 = carregar_imagem(
            ASSETS["fundo_cena_dica2"], (LARGURA, ALTURA), (60, 45, 30),
            "FUNDO DA CENA DE\nDICA 2 (bilhete)",
        )
        self.img_vitoria = carregar_imagem(
            ASSETS["tela_vitoria"], (LARGURA, ALTURA), VERDE, "TELA DE VITÓRIA",
        )
        self.img_derrota = carregar_imagem(
            ASSETS["tela_derrota"], (LARGURA, ALTURA), VERMELHO, "TELA DE DERROTA",
        )
        # Botão "Iniciar" do menu
        self.botao_iniciar = pygame.Rect(0, 0, 220, 60)
        self.botao_iniciar.center = (LARGURA - 270, 500)

        # Botões "Reiniciar" das telas de Vitória e Derrota
        self.botao_reiniciar_vitoria = pygame.Rect(0, 0, 260, 60)
        self.botao_reiniciar_vitoria.center = (LARGURA // 2, ALTURA // 2 + 120)

        self.botao_reiniciar_derrota = pygame.Rect(0, 0, 260, 60)
        self.botao_reiniciar_derrota.center = (LARGURA - 300, ALTURA // 2 + 120)

        # --- Elementos de cena ---
        limites_sala = pygame.Rect(0, 0, LARGURA, ALTURA)
        
        self.limites_sala = limites_sala

        # Posição da máquina dentro da Cena 1 e sua "zona de interação"
        self.rect_maquina = self.img_maquina.get_rect(midright=(LARGURA - 60, ALTURA - 260))
        self.zona_interacao = self.rect_maquina.inflate(60, 60)  # área um pouco maior ao redor

        # Posição do NPC na Cena 1   
        self.rect_npc = self.img_npc.get_rect(midleft=(500, ALTURA - 180))
        # --- Chatbot do NPC (Professor Turing) integrado à IA local (Ollama) ---
        self.npc_chat = NPCChatbot(
            rect_npc=self.rect_npc,
            nome_npc="Professor Turing",
            contexto_fase=(
                "Você é o Alan Turing, em 1936, considerado Pai da computação, dentro de um jogo de chronos "
                "escape educativo. Responda SOMENTE perguntas relacionadas à Fase 4: "
                "a Máquina de Turing, o enigma da fita binária (blocos de 5 bits que "
                "representam letras do alfabeto, A=1 a Z=26), e o contexto histórico "
                "de 1936. Alan Turing deu um nome à máquina de criptografia que conseguiu decodificar "
                "mensagens do inimigo : chamada BOMBE.  Se o jogador perguntar algo fora desse tema, responda "
                "educadamente que só pode falar sobre esta fase. "
                "Responda sempre em português,  em no máximo 3 frases curtas, sem "
                "nunca revelar diretamente a palavra-solução do enigma e nem a senha."
            ),
        )

        # Ponto onde o jogador vai parar ao clicar na máquina (um pouco à
        # esquerda dela, para não ficar "dentro" do sprite)
        self.ponto_interacao_maquina = (
        self.rect_maquina.left - 40,
        self.rect_maquina.bottom - 20,
        )

        self.rect_livro = self.img_livro.get_rect(midbottom=(375, ALTURA - 208))
        self.ponto_interacao_livro = (
            self.rect_livro.centerx,
            self.rect_livro.bottom + 10,
        )

        # --- Seta de navegação na CENA 1 (direita, centralizada verticalmente) ---
        # Leva o jogador até a CENA 3 (continuação da sala).
        self.rect_seta_avancar = pygame.Rect(0, 0, 56, 56)
        self.rect_seta_avancar.midright = (LARGURA - 15, ALTURA // 2)
        self.ponto_interacao_seta = (
            self.rect_seta_avancar.left - 40,
            self.jogador.rect.centery,
        )

        # --- Objeto "computador" na CENA 3 (mesma posição da máquina na Cena 1) ---
        self.rect_computador = self.img_computador.get_rect(midright=(LARGURA - 33, ALTURA - 262))
        self.ponto_interacao_computador = (
            self.rect_computador.left - 20,
            self.rect_computador.bottom - 5,
        )

        # --- Botões "Voltar" da CENA 3 (-> Cena 1) e CENA 4 (-> Cena 3) ---
        self.botao_voltar_cena3 = pygame.Rect(0, 0, 160, 50)
        self.botao_voltar_cena3.bottomleft = (30, ALTURA - 30)

        self.botao_voltar_cena4 = pygame.Rect(0, 0, 160, 50)
        self.botao_voltar_cena4.bottomleft = (30, ALTURA - 30)

        # --- Caixa de texto da CENA 4 (validação da senha da cápsula) ---
        self.caixa_resposta_cena4 = CaixaDeTexto(
            rect=(LARGURA // 2 - 150, 230, 300, 50),
            fonte=self.fonte_texto,
            tamanho_maximo=len(SENHA_CAPSULA),
        )
        self.mensagem_erro_cena4 = ""

        self.proximo_estado_ao_chegar = None

        self.botao_voltar_dica = pygame.Rect(0, 0, 160, 50)
        self.botao_voltar_dica.bottomleft = (30, ALTURA - 30)

        # Caixa de texto da Cena 2 (resposta do enigma)
        self.caixa_resposta = CaixaDeTexto(
            rect=(LARGURA // 2 - 150, 430, 300, 50),
            fonte=self.fonte_texto,
            tamanho_maximo=len(PALAVRA_SOLUCAO),
        )
        self.botao_voltar_dica2 = pygame.Rect(0, 0, 160, 50)
        self.botao_voltar_dica2.bottomleft = (30, ALTURA - 30)

        # --- Bilhete clicável dentro da Cena de Dica 2 ---
        # Controla se o jogador já coletou o bilhete (evita coletar
        # de novo, e muda a aparência do cursor sobre ele)
        self.bilhete_coletado = False

        # AJUSTE essas coordenadas para coincidir com onde o bilhete
        # aparece visualmente na sua imagem de fundo (cena_dica2_bilhete.png)
        self.rect_bilhete = pygame.Rect(0, 0, 220, 140)
        self.rect_bilhete.center = (LARGURA // 2, ALTURA // 2 + 60)

        # --- Ícone de inventário (canto inferior direito, sempre visível) ---
        self.botao_inventario = pygame.Rect(0, 0, 70, 70)
        self.botao_inventario.bottomright = (LARGURA - 20, ALTURA - 20)
        self.mostrar_painel_inventario = False  # controla se o painel está aberto
        # Guarda, a cada quadro, os rects clicáveis de cada item desenhado no
        # painel do inventário (preenchido em desenhar_painel_inventario),
        # para permitir clicar num item e reabrir sua tela associada
        # (ex.: clicar no "Bilhete" reabre a Cena de Dica 2).
        self.rects_itens_inventario = []

        # --- Estado do jogo ---
        self.estado = Jogo.MENU
        self.mensagem_erro = ""  # feedback quando a resposta está errada
        self.ticks_inicio = None  # marca de tempo de quando a fase começou

    # -----------------------------------------------------------------
    # CONTROLE DE TEMPO
    # -----------------------------------------------------------------
    def iniciar_cronometro(self):
        """Marca o instante em que a fase (o cronômetro de 10 min)
        começa a contar. Chamado ao sair do menu."""
        self.ticks_inicio = pygame.time.get_ticks()

    def tempo_restante_segundos(self):
        """Calcula quantos segundos ainda restam com base no tempo
        decorrido desde o início da fase."""
        decorrido_ms = pygame.time.get_ticks() - self.ticks_inicio
        restante = TEMPO_LIMITE_SEGUNDOS - (decorrido_ms // 1000)
        return max(0, restante)

    def desenhar_cronometro(self):
        """Desenha o cronômetro (mm:ss) no canto superior direito da
        tela, mudando para vermelho nos últimos 30 segundos."""
        restante = self.tempo_restante_segundos()
        minutos, segundos = divmod(restante, 60)
        texto = f"{minutos:02d}:{segundos:02d}"
        cor = VERMELHO if restante <= 30 else BRANCO

        fundo_rect = pygame.Rect(LARGURA - 130, 15, 110, 40)
        pygame.draw.rect(self.tela, (0, 0, 0, 150), fundo_rect, border_radius=8)
        render = self.fonte_texto.render(texto, True, cor)
        self.tela.blit(render, render.get_rect(center=fundo_rect.center))

    # -----------------------------------------------------------------
    # TELA: MENU INICIAL
    # -----------------------------------------------------------------
    
    def desenhar_menu(self):
        self.tela.blit(self.img_fundo_intro, (0, 0))
        titulo = self.fonte_titulo.render("Fase 04 - Máquina de Turing", True, BRANCO)
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA - 280, 170)))


    # --- Botão "Iniciar" (muda de cor quando o mouse passa por cima) ---
        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_iniciar.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_iniciar, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_iniciar, width=2, border_radius=10)

        texto_botao = self.fonte_texto.render("Iniciar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_iniciar.center))

    # Deixei a dica do ENTER também, como alternativa ao clique
        instrucao = self.fonte_pequena.render(
        "Clique em Iniciar ou pressione ENTER", True, CINZA_CLARO,
        )
        self.tela.blit(instrucao, instrucao.get_rect(center=(LARGURA - 270, 550)))

    # -----------------------------------------------------------------
    # TELA: CENA 1 - SALA + PERSONAGEM + MÁQUINA
    # -----------------------------------------------------------------
    def desenhar_cena1(self):
        
        mouse_pos = pygame.mouse.get_pos()
        if (self.rect_maquina.collidepoint(mouse_pos) or self.rect_livro.collidepoint(mouse_pos)
                or self.rect_seta_avancar.collidepoint(mouse_pos)):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        self.tela.blit(self.img_fundo_cena1, (0, 0))
        self.tela.blit(self.img_maquina, self.rect_maquina)
        
        self.tela.blit(self.img_npc, self.rect_npc)
        self.tela.blit(self.img_livro, self.rect_livro)
        self.jogador.desenhar(self.tela)
        self.desenhar_seta_avancar(self.rect_seta_avancar)
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()
        
        # --- Chatbot do NPC ---
        if self.npc_chat.perto_do_jogador(self.jogador.rect) and not self.npc_chat.dialogo_aberto:
            self.npc_chat.desenhar_dica_interacao(self.tela, self.fonte_pequena)
        self.npc_chat.desenhar(self.tela, self.fonte_texto, self.fonte_pequena, LARGURA, ALTURA)

        
    def atualizar_cena1(self, teclas):
        if self.npc_chat.dialogo_aberto:
            return
        chegou = self.jogador.mover(teclas, self.limites_sala)
        if chegou and self.proximo_estado_ao_chegar is not None:
            self.mensagem_erro = ""
            proximo = self.proximo_estado_ao_chegar
            self.proximo_estado_ao_chegar = None
            if proximo == Jogo.CENA3:
                # Entra na Cena 3 pelo lado esquerdo, como se estivesse
                # continuando a andar para a "parte 2" da sala.
                self.jogador.rect.topleft = (40, self.jogador.rect.top)
            self.estado = proximo

    def desenhar_seta_avancar(self, rect):
        """Desenha o ícone de seta (usa a imagem em ASSETS['seta_direita']
        se existir; senão desenha um triângulo simples no lugar) usado
        para navegar de uma cena para a próxima (ex: Cena 1 -> Cena 3)."""
        if self.img_seta_direita is not None:
            self.tela.blit(self.img_seta_direita, rect)
            return

        # --- Placeholder: círculo escuro + triângulo apontando p/ direita ---
        pygame.draw.circle(self.tela, (0, 0, 0, 140), rect.center, rect.width // 2)
        pygame.draw.circle(self.tela, AMARELO_SEPIA, rect.center, rect.width // 2, width=2)
        ponta = (rect.centerx + 12, rect.centery)
        base_superior = (rect.centerx - 8, rect.centery - 14)
        base_inferior = (rect.centerx - 8, rect.centery + 14)
        pygame.draw.polygon(self.tela, AMARELO_SEPIA, [ponta, base_superior, base_inferior])

    # -----------------------------------------------------------------
    # TELA: CENA DA DICA - APENAS IMAGEM + CRONÔMETRO + BOTÃO VOLTAR
    # -----------------------------------------------------------------
    def desenhar_cena_dica(self):
        self.tela.blit(self.img_fundo_cena_dica, (0, 0))
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_voltar_dica.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_voltar_dica, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_voltar_dica, width=2, border_radius=10)

        texto_botao = self.fonte_pequena.render("Voltar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_voltar_dica.center))

    
    # -----------------------------------------------------------------
    # TELA: CENA 2 - MÁQUINA DE PERTO + ENIGMA
    # -----------------------------------------------------------------
    def desenhar_cena2(self):
        self.tela.blit(self.img_fundo_cena2, (0, 0))
        self.desenhar_cronometro()

        titulo = self.fonte_texto.render(
            "A fita da máquina imprimiu o seguinte código:", True, BRANCO,
        )
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, 130)))

        # --- Desenha a fita binária (um bloco por letra da solução) ---
        fita_texto = "  ".join(FITA_BINARIA)
        render_fita = self.fonte_titulo.render(fita_texto, True, AZUL_TURING)
        self.tela.blit(render_fita, render_fita.get_rect(center=(LARGURA // 2, 200)))

        # --- Legenda / regra do enigma ---
        legenda_linhas = [
            "Cada bloco de 5 dígitos é um número binário.",
            "Converta o número para a posição no alfabeto (A=1, B=2, C=3 ... Z=26)",
            "e descubra a palavra escondida na fita.",
        ]
        y = 260
        for linha in legenda_linhas:
            render_linha = self.fonte_pequena.render(linha, True, PRETO)
            self.tela.blit(render_linha, render_linha.get_rect(center=(LARGURA // 2, y)))
            y += 28

        instrucao = self.fonte_pequena.render(
            f"Digite a palavra ({len(PALAVRA_SOLUCAO)} letras) e pressione ENTER:",
            True, BRANCO,
        )
        self.tela.blit(instrucao, instrucao.get_rect(center=(LARGURA // 2, 400)))

        self.caixa_resposta.desenhar(self.tela)

        if self.mensagem_erro:
            render_erro = self.fonte_pequena.render(self.mensagem_erro, True, VERMELHO)
            self.tela.blit(render_erro, render_erro.get_rect(center=(LARGURA // 2, 500)))

        dica_voltar = self.fonte_pequena.render(
            "ESC para voltar à sala", True, CINZA_CLARO,
        )
        self.tela.blit(dica_voltar, (20, ALTURA - 35))

    def validar_resposta(self):
        """Compara o texto digitado com a palavra-solução. Se estiver
        correta, avança para a tela de vitória; caso contrário, mostra
        uma mensagem de erro e limpa o campo para nova tentativa."""
        if self.caixa_resposta.texto == PALAVRA_SOLUCAO:
            self.estado = Jogo.CENA_DICA_2
        else:
            self.mensagem_erro = "Código incorreto. Tente novamente!"
            self.caixa_resposta.texto = ""

    # -----------------------------------------------------------------
    # TELA: CENA 3 - CONTINUAÇÃO DA SALA + COMPUTADOR
    # -----------------------------------------------------------------
    def desenhar_cena3(self):
        """Sala "parte 2": o jogador chega vindo da Cena 1 (pela seta) e
        encontra o computador, que leva à Cena 4."""
        mouse_pos = pygame.mouse.get_pos()
        if self.rect_computador.collidepoint(mouse_pos):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        self.tela.blit(self.img_fundo_cena3, (0, 0))
        self.tela.blit(self.img_computador, self.rect_computador)
        self.jogador.desenhar(self.tela)
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()

        # --- Botão "Voltar" (-> Cena 1) ---
        cor_botao = VERDE if self.botao_voltar_cena3.collidepoint(mouse_pos) else AMARELO_SEPIA
        pygame.draw.rect(self.tela, cor_botao, self.botao_voltar_cena3, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_voltar_cena3, width=2, border_radius=10)
        texto_botao = self.fonte_pequena.render("Voltar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_voltar_cena3.center))

    def atualizar_cena3(self, teclas):
        chegou = self.jogador.mover(teclas, self.limites_sala)
        if chegou and self.proximo_estado_ao_chegar is not None:
            self.mensagem_erro = ""
            self.estado = self.proximo_estado_ao_chegar
            self.proximo_estado_ao_chegar = None

    # -----------------------------------------------------------------
    # TELA: CENA 4 - COMPUTADOR DE PERTO + VALIDAÇÃO DA SENHA
    # -----------------------------------------------------------------
    def desenhar_cena4(self):
        """Close-up do computador/cápsula. Não há enigma aqui: o
        jogador só digita a senha já revelada no bilhete (Cena de
        Dica 2) e confirma com ENTER."""
        self.tela.blit(self.img_fundo_cena4, (0, 0))
        self.desenhar_cronometro()


        self.caixa_resposta_cena4.desenhar(self.tela)

        if self.mensagem_erro_cena4:
            render_erro = self.fonte_pequena.render(self.mensagem_erro_cena4, True, VERMELHO)
            self.tela.blit(render_erro, render_erro.get_rect(center=(LARGURA // 2, 400)))

        dica_voltar = self.fonte_pequena.render(
            "ESC para voltar", True, CINZA_CLARO,
        )
        self.tela.blit(dica_voltar, (20, ALTURA - 35))

        # --- Botão "Voltar" (-> Cena 3) ---
        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_voltar_cena4.collidepoint(mouse_pos) else AMARELO_SEPIA
        pygame.draw.rect(self.tela, cor_botao, self.botao_voltar_cena4, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_voltar_cena4, width=2, border_radius=10)
        texto_botao = self.fonte_pequena.render("Voltar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_voltar_cena4.center))

    def validar_senha_capsula(self):
        """Compara o texto digitado com SENHA_CAPSULA ('BOMBE'). Se
        estiver correta, vai DIRETO para a tela de Vitória."""
        if self.caixa_resposta_cena4.texto == SENHA_CAPSULA:
            self.estado = Jogo.VITORIA
        else:
            self.mensagem_erro_cena4 = "Senha incorreta. Tente novamente!"
            self.caixa_resposta_cena4.texto = ""

    # -----------------------------------------------------------------
    # TELA: CENA DA DICA 2 - BILHETE DA MÁQUINA 
    # -----------------------------------------------------------------
    def desenhar_cena_dica_2(self):
        """Mostra o bilhete revelado pela máquina, com a senha da
        cápsula do tempo. Abre automaticamente ao decifrar o código
        corretamente. Sem textos ou botões além do cronômetro/vidas
        e do botão 'Voltar', no rodapé esquerdo."""
        self.tela.blit(self.img_fundo_cena_dica2, (0, 0))
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()

        mouse_pos = pygame.mouse.get_pos()

        # --- Cursor de mão sobre o bilhete, só enquanto não foi coletado ---
        if not self.bilhete_coletado and self.rect_bilhete.collidepoint(mouse_pos):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # --- Dica visual: um contorno pulsando/discreto ao redor do bilhete,
        # só enquanto ele ainda pode ser coletado ---
        if not self.bilhete_coletado:
            pygame.draw.rect(self.tela, AMARELO_SEPIA, self.rect_bilhete, width=3, border_radius=6)


        cor_botao = VERDE if self.botao_voltar_dica2.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_voltar_dica2, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_voltar_dica2, width=2, border_radius=10)

        texto_botao = self.fonte_pequena.render("Voltar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_voltar_dica2.center))

    def desenhar_botao_inventario(self):
        """Ícone fixo no canto inferior direito, clicável a qualquer
        momento para abrir/fechar o painel de itens coletados."""
        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_inventario.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_inventario, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_inventario, width=2, border_radius=10)

        texto = self.fonte_pequena.render(str(self.inventario.quantidade()), True, PRETO)
        self.tela.blit(texto, texto.get_rect(center=self.botao_inventario.center))

    def desenhar_painel_inventario(self):
        """Overlay mostrando a lista de itens coletados até agora.
        Só aparece quando self.mostrar_painel_inventario é True."""
        painel_rect = pygame.Rect(0, 0, 400, 300)
        painel_rect.center = (LARGURA // 2, ALTURA // 2)

        faixa = pygame.Surface(painel_rect.size, pygame.SRCALPHA)
        faixa.fill((20, 20, 20, 230))
        self.tela.blit(faixa, painel_rect.topleft)

        pygame.draw.rect(self.tela, AMARELO_SEPIA, painel_rect, width=3, border_radius=10)

        titulo = self.fonte_texto.render("Itens coletados", True, BRANCO)
        self.tela.blit(titulo, titulo.get_rect(midtop=(painel_rect.centerx, painel_rect.top + 15)))

        # Reconstrói a lista de rects clicáveis a cada quadro (o painel
        # só é desenhado quando está aberto, então isso é barato).
        self.rects_itens_inventario = []

        if self.inventario.quantidade() == 0:
            vazio = self.fonte_pequena.render("Nenhum item ainda.", True, CINZA_CLARO)
            self.tela.blit(vazio, vazio.get_rect(center=painel_rect.center))
        else:
            y = painel_rect.top + 60
            for item in self.inventario.itens:
                nome_render = self.fonte_pequena.render(f"- {item.nome}", True, BRANCO)
                rect_item = nome_render.get_rect(topleft=(painel_rect.left + 20, y))
                self.tela.blit(nome_render, rect_item)
                self.rects_itens_inventario.append((item, rect_item.inflate(20, 8)))
                y += 30

        dica = self.fonte_pequena.render("Clique num item para vê-lo ",
                                        "clique no ícone p/ fechar", True, CINZA_CLARO)
        self.tela.blit(dica, dica.get_rect(midbottom=(painel_rect.centerx, painel_rect.bottom - 15)))

    # -----------------------------------------------------------------
    # TELAS FINAIS: VITÓRIA / DERROTA
    # -----------------------------------------------------------------
    def desenhar_vitoria(self):
        self.tela.blit(self.img_vitoria, (0, 0))
        texto = self.fonte_titulo.render("Você concluiu, parabéns!", True, BRANCO)
        sombra = self.fonte_titulo.render("Você concluiu, parabéns!", True, PRETO)
        centro = (LARGURA // 2, ALTURA // 2)
        self.tela.blit(sombra, sombra.get_rect(center=(centro[0] + 2, centro[1] + 2)))
        self.tela.blit(texto, texto.get_rect(center=centro))
        self.desenhar_botao_inventario()


    def desenhar_derrota(self):
        self.tela.blit(self.img_derrota, (0, 0))
        texto = self.fonte_titulo.render(" ", True, BRANCO)
        sombra = self.fonte_titulo.render(" ", True, PRETO)
        centro = (LARGURA // 2, ALTURA // 2)
        self.tela.blit(sombra, sombra.get_rect(center=(centro[0] + 2, centro[1] + 2)))
        self.tela.blit(texto, texto.get_rect(center=centro))

        # --- Botão "Tentar novamente" ---
        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_reiniciar_derrota.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_reiniciar_derrota, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_reiniciar_derrota, width=2, border_radius=10)

        texto_botao = self.fonte_texto.render("Tentar novamente", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_reiniciar_derrota.center))

        dica = self.fonte_pequena.render("(ou pressione R)", True, BRANCO)
        self.tela.blit(dica, dica.get_rect(center=(LARGURA - 240, self.botao_reiniciar_derrota.bottom + 25)))

    
    # -----------------------------------------------------------------
    # REINÍCIO DA FASE
    # -----------------------------------------------------------------
    def reiniciar(self):
        """Reseta a posição do jogador, o campo de resposta e volta ao
        menu inicial, permitindo jogar novamente."""
        self.jogador.rect.topleft = (80, ALTURA - 150)
        self.caixa_resposta.texto = ""
        self.caixa_resposta_cena4.texto = ""
        self.mensagem_erro = ""
        self.mensagem_erro_cena4 = ""
        self.bilhete_coletado = False
        self.estado = Jogo.MENU
        self.ticks_inicio = None
        self.proximo_estado_ao_chegar = None

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
                    if self.estado == Jogo.CENA1:
                        if self.npc_chat.dialogo_aberto:
                            self.npc_chat.tratar_evento(evento)
                        elif evento.key == pygame.K_e and self.npc_chat.perto_do_jogador(self.jogador.rect):
                            self.npc_chat.abrir_dialogo()

                    elif self.estado == Jogo.CENA2:
                        if evento.key == pygame.K_ESCAPE:
                            self.estado = Jogo.CENA1
                        else:
                            enter_pressionado = self.caixa_resposta.tratar_evento(evento)
                            if enter_pressionado:
                                self.validar_resposta()

                    elif self.estado == Jogo.CENA4:
                        if evento.key == pygame.K_ESCAPE:
                            self.estado = Jogo.CENA3
                        else:
                            enter_pressionado = self.caixa_resposta_cena4.tratar_evento(evento)
                            if enter_pressionado:
                                self.validar_senha_capsula()

                    elif self.estado in (Jogo.VITORIA, Jogo.DERROTA) and evento.key == pygame.K_r:
                        self.reiniciar()

                # --- Clique do mouse no botão do menu, na máquina, ou nos botões de reiniciar ---
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if self.estado == Jogo.MENU and self.botao_iniciar.collidepoint(evento.pos):
                        self.iniciar_cronometro()
                        self.estado = Jogo.CENA1

                    elif self.estado == Jogo.CENA1 and self.rect_maquina.collidepoint(evento.pos):
                        self.jogador.mover_ate(self.ponto_interacao_maquina)
                        self.proximo_estado_ao_chegar = Jogo.CENA2

                    # Clique na seta da Cena 1 -> anda até ela e segue para a Cena 3
                    elif self.estado == Jogo.CENA1 and self.rect_seta_avancar.collidepoint(evento.pos):
                        self.jogador.mover_ate(self.ponto_interacao_seta)
                        self.proximo_estado_ao_chegar = Jogo.CENA3

                    # Clique no computador da Cena 3 -> anda até ele e segue para a Cena 4
                    elif self.estado == Jogo.CENA3 and self.rect_computador.collidepoint(evento.pos):
                        self.jogador.mover_ate(self.ponto_interacao_computador)
                        self.proximo_estado_ao_chegar = Jogo.CENA4

                    # Botão "Voltar" da Cena 3 -> Cena 1 (posiciona o jogador perto da seta)
                    elif self.estado == Jogo.CENA3 and self.botao_voltar_cena3.collidepoint(evento.pos):
                        self.jogador.rect.midright = (self.rect_seta_avancar.left - 20, self.jogador.rect.centery)
                        self.estado = Jogo.CENA1

                    # Botão "Voltar" da Cena 4 -> Cena 3
                    elif self.estado == Jogo.CENA4 and self.botao_voltar_cena4.collidepoint(evento.pos):
                        self.estado = Jogo.CENA3

                    # Clique num item do inventário -> reabre a tela associada a ele
                    # (por enquanto só o Bilhete reabre a Cena de Dica 2; outras
                    # colaboradoras podem repetir esse padrão para os próprios itens)
                    elif self.mostrar_painel_inventario and any(
                        rect.collidepoint(evento.pos) for _, rect in self.rects_itens_inventario
                    ):
                        for item, rect in self.rects_itens_inventario:
                            if rect.collidepoint(evento.pos) and "Bilhete" in item.nome:
                                self.mostrar_painel_inventario = False
                                self.estado = Jogo.CENA_DICA_2
                                break

                    # Clique no ícone do inventário -> abre/fecha o painel
                    elif self.estado in (Jogo.CENA1, Jogo.CENA2, Jogo.CENA3, Jogo.CENA_DICA_2) and self.botao_inventario.collidepoint(evento.pos):
                        self.mostrar_painel_inventario = not self.mostrar_painel_inventario

                    # clique no bilhete -> vira colecionável
                    elif self.estado == Jogo.CENA_DICA_2 and not self.bilhete_coletado and self.rect_bilhete.collidepoint(evento.pos):
                        item_bilhete = ItemColecionavel(
                            nome="Bilhete da Máquina Turing-Engelhardt",
                            descricao="Um pedaço de papel com o código da cápsula do tempo: Bombe.",
                        )
                        self.inventario.adicionar(item_bilhete)
                        self.bilhete_coletado = True

                    # Botão "Voltar" da Cena de Dica 2 -> sempre retorna à Cena 1
                    # (tanto na primeira vez, ao pegar o bilhete, quanto ao
                    # reabrir a tela depois pelo inventário)
                    elif self.estado == Jogo.CENA_DICA_2 and self.botao_voltar_dica2.collidepoint(evento.pos):
                        self.estado = Jogo.CENA1

                    elif self.estado == Jogo.VITORIA and self.botao_reiniciar_vitoria.collidepoint(evento.pos):
                        return "vitoria"

                    elif self.estado == Jogo.CENA1 and self.rect_livro.collidepoint(evento.pos):
                        self.jogador.mover_ate(self.ponto_interacao_livro)
                        self.proximo_estado_ao_chegar = Jogo.CENA_DICA

                    elif self.estado == Jogo.CENA_DICA and self.botao_voltar_dica.collidepoint(evento.pos):
                        self.estado = Jogo.CENA1

                    elif self.estado == Jogo.VITORIA and self.botao_reiniciar_vitoria.collidepoint(evento.pos):
                        self.reiniciar()

                    elif self.estado == Jogo.DERROTA and self.botao_reiniciar_derrota.collidepoint(evento.pos):
                        self.reiniciar() 

            # --- Verificação do cronômetro (vale para CENA1, CENA2, CENA3, CENA4 e CENA_DICA) ---
            if self.estado in (Jogo.CENA1, Jogo.CENA2, Jogo.CENA3, Jogo.CENA4, Jogo.CENA_DICA) and self.ticks_inicio is not None:
                if self.tempo_restante_segundos() <= 0:
                    self.estado = Jogo.DERROTA

            # --- Atualização de lógica por estado ---
            if self.estado == Jogo.CENA1:
                teclas = pygame.key.get_pressed()
                self.atualizar_cena1(teclas)
            elif self.estado == Jogo.CENA3:
                teclas = pygame.key.get_pressed()
                self.atualizar_cena3(teclas)

            # --- Desenho por estado ---
            if self.estado == Jogo.MENU:
                self.desenhar_menu()
            elif self.estado == Jogo.CENA1:
                self.desenhar_cena1()
            elif self.estado == Jogo.CENA_DICA:
                self.desenhar_cena_dica()        
            elif self.estado == Jogo.CENA2:
                self.desenhar_cena2()
            elif self.estado == Jogo.CENA_DICA_2:
                self.desenhar_cena_dica_2()
            elif self.estado == Jogo.CENA3:
                self.desenhar_cena3()
            elif self.estado == Jogo.CENA4:
                self.desenhar_cena4()
            elif self.estado == Jogo.VITORIA:
                self.desenhar_vitoria()
            elif self.estado == Jogo.DERROTA:
                self.desenhar_derrota()
                    
            
            if self.mostrar_painel_inventario and self.estado in (Jogo.CENA1, Jogo.CENA2, Jogo.CENA3, Jogo.CENA_DICA_2):
                self.desenhar_painel_inventario()

            pygame.display.flip()
            self.relogio.tick(FPS)

        pygame.quit()
        sys.exit()


# =====================================================================
# 8. PONTO DE ENTRADA DO PROGRAMA
# =====================================================================
if __name__ == "__main__":
    jogo = Jogo()
    jogo.executar()
