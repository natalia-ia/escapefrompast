import pygame
import sys
import json
import threading
import queue
import urllib.request
import urllib.error

pygame.init()

LARGURA, ALTURA = 960, 600
CINZA = (150, 150, 150)
BRANCO = (240, 240, 240)
VERDE = (60, 170, 90)
VERMELHO = (180, 60, 60)
AZUL = (70, 110, 200)
PRETO = (20, 20, 20)

ASSETS = {
    "fundo": "assets/cenario/cenario_fase3.png",
    "corpo_personagem": "assets/decoracao/corpo do personagem.png",
    "cartoes": "assets/interativos/cartoes.png",
    "icone_chatbot": "assets/interativos/icone_chatbot.png",
    "icone_inventario": "assets/interativos/icone_inventario.png",
    "icone_configuracoes": "assets/interativos/icone_configuracoes.png",
    "maquina_tabulacao": "assets/interativos/maquina_tabulacao.png",
    "painel_config": "assets/interativos/painel_config.png",
    "gaveta_fechada": "assets/interativos/gaveta_fechada.png",
    "gaveta_aberta": "assets/interativos/gaveta_aberta.png",
    "objetivo": "assets/interativos/objetivo.png",
    "painel_ampliado": "assets/interativos/painel_ampliado.png",
    "processando3": "assets/interativos/processando3.png",
    "saindo": "assets/interativos/saindo.png",
    # Tela de introdução (antes do jogo começar).
    "fundo_intro": "assets/cenario/cena1.png",
    # Fundo da cena final (jogador anda até a máquina do tempo).
    "fundo_final": "assets/cenario/cena2.png",
    # Cena final: máquina do tempo aberta (antes de entrar) e fechada
    # (depois que o jogador entra), usadas na conclusão da fase 3.
    "maquina_tempo_aberta": "assets/interativos/maquina_do_tempo2.png",
    "maquina_tempo_fechada": "assets/interativos/maquina_do_tempo.png",
    # Único documento que existe no cenário. Mostra o objetivo da missão
    # (usa a mesma imagem "objetivo" já carregada para a tela ampliada).
    "p1_parado": "assets/personagem1/p1_parada.png",
    "p1_andando1": "assets/personagem1/p1_andando.png",
    "p1_andando2": "assets/personagem1/p1_andando2.png",
    "p2_parado": "assets/personagem2/p2_parado.png",
    "p2_andando1": "assets/personagem2/p2_andando.png",
    "p2_andando2": "assets/personagem2/p2_andando2.png",
    "musica_ambiente": "assets/musicas/ambiente.mp3",
    "som_click": "assets/musicas/sons/click.mp3",
}

# Tela ampliada aberta ao interagir com cada objeto do cenário.
# "chatbot" não está aqui: ele abre o chat de texto livre do Hermann.
TELAS_AMPLIADAS = {
    "documento objetivo": "documento_objetivo",
    "painel config": "painel",
    "maquina tabulacao": "maquina",
    "gaveta": "gaveta",
    "inventario": "inventario",
    "configuracoes": "configuracoes",
}

TAMANHO_ZOOM = (700, 480)
RAIO_INTERACAO = 40

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODELO = "qwen2.5:3b-instruct"
OLLAMA_TIMEOUT_SEGUNDOS = 20
NPC_RAIO_INTERACAO = 60
CHAT_HISTORICO_VISIVEL = 3

# Base do Hermann. A cada pergunta, uma dica sobre o passo atual da
# missão (calculada a partir do progresso do jogador) é anexada aqui.
PROMPT_SISTEMA_HERMANN = (
    "Voce e o Professor Hermann, cientista de dados do ano de 1880, "
    "especialista em maquinas de tabulacao por cartoes perfurados. "
    "Voce trata o jogador como um colega cientista, e SEMPRE se refere "
    "a ele chamando-o de 'cientista' (nunca de 'professor' ou outro "
    "titulo). Missao do cientista: configurar uma maquina de tabulacao "
    "para contar apenas os registros de 'trabalhadores adultos', usando "
    "cartoes perfurados guardados numa gaveta trancada com cadeado. "
    "Responda SEMPRE em portugues, em no maximo 2 frases curtas, tom "
    "simpatico e um pouco formal. De dicas sutis sobre o passo atual "
    "descrito abaixo, mas NUNCA revele a combinacao do cadeado nem a "
    "configuracao exata do painel. Se a pergunta nao tiver relacao com "
    "a sala ou a missao, responda que prefere focar no trabalho e traga "
    "o assunto de volta a tabulacao."
)

# Texto exibido no balão de fala do Hermann na tela de introdução
# (antes, esse texto era a primeira mensagem automática do chat).
TEXTO_INTRO_HERMANN = (
    "Bem-vindo(a), cientista! Estamos em 1880 e a Sociedade de "
    "Estatistica precisa da sua ajuda: configure a maquina de "
    "tabulacao para contar apenas os registros de trabalhadores "
    "adultos. Os cartoes perfurados estao guardados na gaveta da "
    "escrivaninha, mas ela esta trancada. Boa sorte, cientista!"
)

COLUNAS_DISPONIVEIS = ["Homem", "Mulher", "Adulto", "Criança", "Trabalhador", "Estudante"]
MODOS_DISPONIVEIS = ["Contar", "Classificar", "Somar"]

COLUNAS_CORRETAS = {"Adulto", "Trabalhador"}
MODO_CORRETO = "Contar"
RESULTADO_CORRETO = 4  # "4 registros", conforme o GDD

DURACAO_PROCESSAMENTO_MS = 1400

# Tempo limite da fase, mostrado no cronômetro do canto superior direito.
TEMPO_LIMITE_MS = 5 * 60 * 1000

CADEADO_GAVETA_CORRETO = (2, 4)  # resposta da charada = "24" (horas do dia)


def carregar_imagem(caminho, tamanho, cor_fallback=CINZA, label=""):
    try:
        imagem = pygame.image.load(caminho).convert_alpha()
        imagem = pygame.transform.scale(imagem, tamanho)
        return imagem
    except (pygame.error, FileNotFoundError):
        img = pygame.Surface(tamanho)
        img.fill(cor_fallback)
        if label:
            font = pygame.font.SysFont(None, 20)
            texto = font.render(label, True, (225, 225, 225))
            img.blit(texto, texto.get_rect(center=(tamanho[0] // 2, tamanho[1] // 2)))
        return img


def criar_hitbox_invisivel(tamanho):
    superficie = pygame.Surface(tamanho, pygame.SRCALPHA)
    superficie.fill((0, 0, 0, 0))
    return superficie


def quebrar_texto(texto, fonte, largura_max):
    palavras = texto.split(" ")
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        teste = (linha_atual + " " + palavra).strip()
        if fonte.size(teste)[0] <= largura_max:
            linha_atual = teste
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual)
    return linhas


class Jogador:

    VELOCIDADE = 4
    INTERVALO_ANIMACAO_MS = 150

    def __init__(self, frame_parado, frames_andando, posicao_inicial):
        self.frame_parado = frame_parado
        self.frames_andando = frames_andando
        self.indice_animacao = 0
        self.tempo_ultimo_frame = pygame.time.get_ticks()

        self.imagem = self.frame_parado
        self.rect = self.imagem.get_rect(topleft=posicao_inicial)

    def mover(self, teclas, limites):
        dx = dy = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx -= self.VELOCIDADE
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx += self.VELOCIDADE

        esta_andando = dx != 0 or dy != 0

        self.rect.x = max(limites.left, min(self.rect.x + dx, limites.right - self.rect.width))
        self.rect.y = max(limites.top, min(self.rect.y + dy, limites.bottom - self.rect.height))

        self._atualizar_sprite(esta_andando, dx)

    def _atualizar_sprite(self, esta_andando, dx=0):
        if not esta_andando:
            self.imagem = self.frame_parado
            self.indice_animacao = 0
            return

        agora = pygame.time.get_ticks()
        if agora - self.tempo_ultimo_frame >= self.INTERVALO_ANIMACAO_MS:
            self.indice_animacao = (self.indice_animacao + 1) % len(self.frames_andando)
            self.tempo_ultimo_frame = agora

        self.imagem = self.frames_andando[self.indice_animacao]

        if dx < 0:
            self.imagem = pygame.transform.flip(self.imagem, True, False)

    def desenhar(self, tela):
        tela.blit(self.imagem, self.rect)


class Jogo:
    def __init__(self, personagem_escolhido=1):
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Escape.from_past()")
        self.clock = pygame.time.Clock()
        self.rodando = True

        # Controla qual "tela" está ativa: introdução, jogo principal
        # ou a cena final de conclusão da fase.
        self.fase = "intro"

        self.font_titulo = pygame.font.SysFont(None, 34)
        self.font_texto = pygame.font.SysFont(None, 24)
        self.font_pequena = pygame.font.SysFont(None, 20)

        # Estado dos enigmas (segue o GDD) + enigma da gaveta.
        self.estado = {
            "documento_objetivo_lido": False,
            "documento_colunas_lido": False,
            "painel_configurado": False,
            "config_correta": False,
            "tabulacao_concluida": False,
            "peca_liberada": False,
            "gaveta_destrancada": False,
            "gaveta_aberta": False,
            "cartoes_coletados": False,
        }

        # Itens que o jogador vai acumulando (mostrados na tela de
        # inventário). Cada item é um dict com nome + descrição curta.
        self.itens_inventario = []

        self.painel_modo_selecionado = None
        self.painel_colunas_selecionadas = set()
        self.painel_mensagem = ""

        self.maquina_processando = False
        self.maquina_processamento_inicio = 0
        self.maquina_mensagem = "Pegue os cartoes perfurados e configure o painel para iniciar."

        self.gaveta_valores = [0, 0]
        self.gaveta_mensagem = "Gire os discos e clique em Testar."

        # Chat com o Professor Hermann (IA local via Ollama).
        self.chat_ativo = False
        self.chat_input = ""
        self.chat_historico = []
        self.chat_carregando = False
        self.chat_resposta_queue = queue.Queue()

        self.tela_ampliada_atual = None

        self.zoom_rect = pygame.Rect(0, 0, *TAMANHO_ZOOM)
        self.zoom_rect.center = (LARGURA // 2, ALTURA // 2)

        self.botao_fechar_tamanho = 32
        self.botao_fechar_rect = pygame.Rect(
            self.zoom_rect.right - self.botao_fechar_tamanho - 10,
            self.zoom_rect.top + 10,
            self.botao_fechar_tamanho,
            self.botao_fechar_tamanho,
        )

        self.img_objetivo = carregar_imagem(ASSETS["objetivo"], TAMANHO_ZOOM, CINZA, "objetivo")
        self.img_documento_colunas = carregar_imagem(ASSETS["objetivo"], TAMANHO_ZOOM, CINZA, "documento colunas")
        self.img_painel_fundo = carregar_imagem(ASSETS["painel_ampliado"], TAMANHO_ZOOM, CINZA, "painel")
        self.img_maquina_fundo = carregar_imagem(ASSETS["processando3"], TAMANHO_ZOOM, CINZA, "maquina")
        self.img_recompensa = carregar_imagem(ASSETS["saindo"], TAMANHO_ZOOM, CINZA, "recompensa")
        self.img_gaveta_fechada_zoom = carregar_imagem(ASSETS["gaveta_fechada"], TAMANHO_ZOOM, CINZA, "gaveta fechada")
        self.img_gaveta_aberta_zoom = carregar_imagem(ASSETS["gaveta_aberta"], TAMANHO_ZOOM, CINZA, "gaveta aberta")

        # Widgets do painel (checkboxes de colunas + radios de modo).
        self.painel_rects_modo = {}
        x0 = self.zoom_rect.left + 40
        y_modo = self.zoom_rect.top + 90
        largura_modo = 190
        for i, modo in enumerate(MODOS_DISPONIVEIS):
            self.painel_rects_modo[modo] = pygame.Rect(x0 + i * (largura_modo + 10), y_modo, largura_modo, 32)

        self.painel_rects_colunas = {}
        y_coluna = self.zoom_rect.top + 150
        for i, coluna in enumerate(COLUNAS_DISPONIVEIS):
            self.painel_rects_colunas[coluna] = pygame.Rect(x0, y_coluna + i * 38, 260, 30)

        self.painel_botao_confirmar = pygame.Rect(
            self.zoom_rect.centerx - 90, self.zoom_rect.bottom - 55, 180, 40
        )

        self.maquina_botao_iniciar = pygame.Rect(
            self.zoom_rect.centerx - 90, self.zoom_rect.bottom - 130, 180, 40
        )
        self.maquina_botao_compartimento = pygame.Rect(
            self.zoom_rect.centerx - 110, self.zoom_rect.bottom - 75, 220, 40
        )

        # Widgets do cadeado da gaveta (2 discos, cada um 0-9).
        largura_disco = 90
        espaco_discos = 30
        total_discos = largura_disco * 2 + espaco_discos
        x_disco0 = self.zoom_rect.centerx - total_discos // 2
        y_disco = self.zoom_rect.top + 180

        self.gaveta_rects_disco = [
            pygame.Rect(x_disco0, y_disco, largura_disco, 70),
            pygame.Rect(x_disco0 + largura_disco + espaco_discos, y_disco, largura_disco, 70),
        ]
        self.gaveta_setas_cima = [
            pygame.Rect(r.left, r.top - 34, r.width, 28) for r in self.gaveta_rects_disco
        ]
        self.gaveta_setas_baixo = [
            pygame.Rect(r.left, r.bottom + 6, r.width, 28) for r in self.gaveta_rects_disco
        ]
        self.gaveta_botao_testar = pygame.Rect(
            self.zoom_rect.centerx - 90, self.zoom_rect.bottom - 90, 180, 40
        )
        self.gaveta_area_cartoes = pygame.Rect(
            self.zoom_rect.centerx - 100, self.zoom_rect.top + 260, 200, 120
        )

        self.img_cartoes_mundo = carregar_imagem(ASSETS["cartoes"], (150, 90), CINZA, "cartoes")
        self.cartoes_mundo_pos = (460, 425)

        self.img_cartoes_zoom = carregar_imagem(
            ASSETS["cartoes"], (self.gaveta_area_cartoes.width, self.gaveta_area_cartoes.height),
            CINZA, "cartoes"
        )

        # Ícone pequeno usado para representar os cartões perfurados
        # dentro da tela de inventário.
        self.img_cartoes_inventario = carregar_imagem(ASSETS["cartoes"], (48, 48), CINZA, "cartoes")

        self.fundo = carregar_imagem(ASSETS["fundo"], (LARGURA, ALTURA), label="sala")

        self.decoracao = []

        self.personagem_cenario = carregar_imagem(
            ASSETS["corpo_personagem"], (350, 350), CINZA, "personagem cenario"
        )
        self.personagem_cenario_pos = (540, 240)
        self.npc_rect = self.personagem_cenario.get_rect(topleft=self.personagem_cenario_pos)

        # Objetos "mundo" exigem aproximação + tecla E; "hud" é clicado com o mouse.
        self.interativos = [
            {
                "img": carregar_imagem(ASSETS["maquina_tabulacao"], (300, 300), CINZA, "maquina tabulacao"),
                "pos": (0, 280),
                "nome": "maquina tabulacao",
                "tipo": "mundo",
                "desenhar": True,
            },
            {
                "img": carregar_imagem(ASSETS["painel_config"], (320, 220), CINZA, "painel config"),
                "pos": (330, 120),
                "nome": "painel config",
                "tipo": "mundo",
                "desenhar": True,
            },
            {
                "img": criar_hitbox_invisivel((110, 90)),
                "pos": (480, 420),
                "nome": "gaveta",
                "tipo": "mundo",
                "desenhar": False,
            },
            # O documento objetivo fica escondido (invisível) entre os
            # livros da prateleira — só a área de interação existe.
            {
                "img": criar_hitbox_invisivel((95, 90)),
                "pos": (850, 455),
                "nome": "documento objetivo",
                "tipo": "mundo",
                "desenhar": False,
            },
            {
                "img": carregar_imagem(ASSETS["icone_inventario"], (80, 80), CINZA, "inventario"),
                "pos": (15, 15),
                "nome": "inventario",
                "tipo": "hud",
                "desenhar": True,
            },
            {
                "img": carregar_imagem(ASSETS["icone_configuracoes"], (80, 80), CINZA, "config"),
                "pos": (175, 15),
                "nome": "configuracoes",
                "tipo": "hud",
                "desenhar": True,
            },
            {
                "img": carregar_imagem(ASSETS["icone_chatbot"], (80, 80), CINZA, "chatbot"),
                "pos": (90, 15),
                "nome": "chatbot",
                "tipo": "hud",
                "desenhar": True,
            },
        ]

        prefixo = "p1" if personagem_escolhido == 1 else "p2"

        self.img_avatar_parado = carregar_imagem(ASSETS[f"{prefixo}_parado"], (138, 288), CINZA, "PARADO")
        self.img_avatar_andando1 = carregar_imagem(ASSETS[f"{prefixo}_andando1"], (138, 288), CINZA, "ANDANDO1")
        self.img_avatar_andando2 = carregar_imagem(ASSETS[f"{prefixo}_andando2"], (138, 288), CINZA, "ANDANDO2")

        self.jogador = Jogador(
            frame_parado=self.img_avatar_parado,
            frames_andando=[self.img_avatar_andando1, self.img_avatar_andando2],
            posicao_inicial=(80, ALTURA - 200),
        )

        # -------------------------------------------------------------
        # Tela de introdução (fase == "intro")
        # -------------------------------------------------------------
        self.fundo_intro = carregar_imagem(ASSETS["fundo_intro"], (LARGURA, ALTURA), label="fundo intro 1880")
        self.fundo_final = carregar_imagem(ASSETS["fundo_final"], (LARGURA, ALTURA), label="fundo final")

        self.hermann_intro_img = carregar_imagem(
            ASSETS["corpo_personagem"], (600, 600), CINZA, "hermann"
        )
        self.hermann_intro_pos = (LARGURA - 500, ALTURA - 400)
        self.hermann_intro_rect = self.hermann_intro_img.get_rect(topleft=self.hermann_intro_pos)

        self.botao_iniciar_jogo_rect = pygame.Rect(0, 0, 220, 50)
        self.botao_iniciar_jogo_rect.center = (LARGURA // 2, ALTURA - 50)

        # -------------------------------------------------------------
        # Cena final (fase == "final"): jogador anda até a máquina do
        # tempo e entra nela para concluir a fase.
        # -------------------------------------------------------------
        tamanho_maquina_tempo = (280, 320)
        self.maquina_tempo_aberta = carregar_imagem(
            ASSETS["maquina_tempo_aberta"], tamanho_maquina_tempo, CINZA, "maquina tempo aberta"
        )
        self.maquina_tempo_fechada = carregar_imagem(
            ASSETS["maquina_tempo_fechada"], tamanho_maquina_tempo, CINZA, "maquina tempo fechada"
        )
        self.maquina_tempo_pos = (LARGURA - 340, ALTURA - 380)
        self.maquina_tempo_rect = self.maquina_tempo_aberta.get_rect(topleft=self.maquina_tempo_pos)

        self.final_estado = "andando"  # "andando" -> "fechando" -> "concluido"
        self.final_transicao_inicio = 0
        self.final_duracao_fechando_ms = 900

        # -------------------------------------------------------------
        # Cronômetro da fase (5 minutos). Começa a contar quando o
        # jogador sai da tela de introdução.
        # -------------------------------------------------------------
        self.tempo_inicio_jogo = None
        self.tempo_esgotado = False

        self.botao_reiniciar_rect = pygame.Rect(0, 0, 220, 50)
        self.botao_reiniciar_rect.center = (LARGURA // 2, ALTURA // 2 + 60)

        # -------------------------------------------------------------
        # Configurações (som) + widgets da tela de configurações.
        # -------------------------------------------------------------
        self.volume_musica = 70  # 0-100
        self.sons_ativados = True

        self.config_botao_vol_menos = pygame.Rect(
            self.zoom_rect.left + 260, self.zoom_rect.top + 110, 36, 36
        )
        self.config_botao_vol_mais = pygame.Rect(
            self.zoom_rect.left + 380, self.zoom_rect.top + 110, 36, 36
        )
        self.config_checkbox_sons = pygame.Rect(
            self.zoom_rect.left + 40, self.zoom_rect.top + 180, 26, 26
        )
        self.config_botao_reiniciar = pygame.Rect(
            self.zoom_rect.centerx - 110, self.zoom_rect.bottom - 90, 220, 40
        )

        try:
            pygame.mixer.music.load(ASSETS["musica_ambiente"])
            pygame.mixer.music.set_volume(self.volume_musica / 100)
            pygame.mixer.music.play(-1)
        except pygame.error:
            print("Aviso: não foi possível carregar a música de ambiente.")

        try:
            self.som_click = pygame.mixer.Sound(ASSETS["som_click"])
        except pygame.error:
            self.som_click = None
            print("Aviso: não foi possível carregar o som de clique.")

    def _tocar_click(self):
        if self.sons_ativados and self.som_click:
            self.som_click.play()

    # =================================================================
    # INVENTÁRIO
    # =================================================================
    def _adicionar_item_inventario(self, nome, icone, descricao=""):
        """Adiciona um item ao inventário, evitando duplicar o mesmo nome."""
        if any(item["nome"] == nome for item in self.itens_inventario):
            return
        self.itens_inventario.append({"nome": nome, "icone": icone, "descricao": descricao})

    # =================================================================
    # TELA DE INTRODUÇÃO
    # =================================================================
    def _processar_evento_intro(self, evento):
        iniciar = False
        if evento.type == pygame.MOUSEBUTTONDOWN and self.botao_iniciar_jogo_rect.collidepoint(evento.pos):
            iniciar = True
        elif evento.type == pygame.KEYDOWN and evento.key in (
            pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE
        ):
            iniciar = True

        if iniciar:
            self._tocar_click()
            self._iniciar_fase_jogando()

    def _iniciar_fase_jogando(self):
        self.fase = "jogando"
        self.tempo_inicio_jogo = pygame.time.get_ticks()
        self.tempo_esgotado = False

    def _desenhar_intro(self):
        self.tela.blit(self.fundo_intro, (0, 0))
        self.tela.blit(self.hermann_intro_img, self.hermann_intro_pos)

        titulo = self.font_titulo.render("Escape.from_past()", True, BRANCO)
        self.tela.blit(titulo, (30, 30))

        largura_balao = 460
        linhas = quebrar_texto(TEXTO_INTRO_HERMANN, self.font_pequena, largura_balao - 30)
        altura_balao = 46 + len(linhas) * 22

        balao = pygame.Rect(0, 0, largura_balao, altura_balao)
        balao.left = max(120, self.hermann_intro_rect.left - largura_balao - 20)
        balao.top = max(120, self.hermann_intro_rect.top - 10)

        overlay = pygame.Surface(balao.size, pygame.SRCALPHA)
        overlay.fill((20, 20, 25, 225))
        self.tela.blit(overlay, balao.topleft)
        pygame.draw.rect(self.tela, BRANCO, balao, width=2, border_radius=10)

        nome = self.font_texto.render("Professor Hermann", True, (255, 210, 120))
        self.tela.blit(nome, (balao.left + 15, balao.top + 8))

        y = balao.top + 34
        for linha in linhas:
            render = self.font_pequena.render(linha, True, BRANCO)
            self.tela.blit(render, (balao.left + 15, y))
            y += 22

        pygame.draw.rect(self.tela, VERDE, self.botao_iniciar_jogo_rect, border_radius=8)
        texto_botao = self.font_texto.render("Iniciar Jogo", True, BRANCO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_iniciar_jogo_rect.center))

    # =================================================================
    # CENA FINAL (máquina do tempo / conclusão da fase 3)
    # =================================================================
    def _iniciar_fase_final(self):
        self.fase = "final"
        self.final_estado = "andando"
        self.jogador.rect.topleft = (80, ALTURA - 200)
        self.jogador._atualizar_sprite(False)

    def _processar_evento_final(self, evento):
        # Não há cliques ou teclas especiais nessa cena além do
        # movimento (tratado em _atualizar_final).
        pass

    def _atualizar_final(self):
        if self.final_estado == "andando":
            teclas = pygame.key.get_pressed()
            limites = self.tela.get_rect()
            self.jogador.mover(teclas, limites)

            if self.jogador.rect.colliderect(self.maquina_tempo_rect):
                self.final_estado = "fechando"
                self.final_transicao_inicio = pygame.time.get_ticks()
                self._tocar_click()

        elif self.final_estado == "fechando":
            agora = pygame.time.get_ticks()
            if agora - self.final_transicao_inicio >= self.final_duracao_fechando_ms:
                self.final_estado = "concluido"

    def _desenhar_final(self):
        self.tela.blit(self.fundo_final, (0, 0))

        if self.final_estado == "andando":
            self.tela.blit(self.maquina_tempo_aberta, self.maquina_tempo_pos)
            self.jogador.desenhar(self.tela)

            area_interacao = self.maquina_tempo_rect.inflate(RAIO_INTERACAO * 2, RAIO_INTERACAO * 2)
            if area_interacao.colliderect(self.jogador.rect):
                dica = self.font_pequena.render("Entre na máquina", True, BRANCO)
                self.tela.blit(
                    dica,
                    (self.maquina_tempo_rect.centerx - dica.get_width() // 2, self.maquina_tempo_rect.top - 24),
                )
        else:
            self.tela.blit(self.maquina_tempo_fechada, self.maquina_tempo_pos)

        if self.final_estado == "concluido":
            overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            self.tela.blit(overlay, (0, 0))

            titulo = self.font_titulo.render("Fase 3 concluída!", True, BRANCO)
            self.tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, ALTURA // 2 - 20)))

            subtitulo = self.font_pequena.render(
                "O cientista viajou no tempo com a peça recuperada.", True, (220, 220, 220)
            )
            self.tela.blit(subtitulo, subtitulo.get_rect(center=(LARGURA // 2, ALTURA // 2 + 20)))

    # =================================================================
    # CRONÔMETRO / TEMPO ESGOTADO
    # =================================================================
    def _tempo_restante_ms(self):
        if self.tempo_inicio_jogo is None:
            return TEMPO_LIMITE_MS
        decorrido = pygame.time.get_ticks() - self.tempo_inicio_jogo
        return max(0, TEMPO_LIMITE_MS - decorrido)

    def _desenhar_cronometro(self):
        restante_ms = self._tempo_restante_ms()
        minutos = restante_ms // 60000
        segundos = (restante_ms // 1000) % 60
        texto = f"{minutos:02d}:{segundos:02d}"

        cor = VERMELHO if restante_ms <= 30_000 else BRANCO
        render = self.font_texto.render(texto, True, cor)

        caixa = pygame.Rect(0, 0, render.get_width() + 24, 36)
        caixa.topright = (LARGURA - 15, 15)

        overlay = pygame.Surface(caixa.size, pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 190))
        self.tela.blit(overlay, caixa.topleft)
        pygame.draw.rect(self.tela, cor, caixa, width=1, border_radius=6)
        self.tela.blit(render, render.get_rect(center=caixa.center))

    def _processar_evento_tempo_esgotado(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and self.botao_reiniciar_rect.collidepoint(evento.pos):
            self._tocar_click()
            self._reiniciar_jogo()
        elif evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._reiniciar_jogo()

    def _desenhar_tempo_esgotado(self):
        self.tela.blit(self.fundo, (0, 0))

        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.tela.blit(overlay, (0, 0))

        titulo = self.font_titulo.render("Tempo esgotado!", True, VERMELHO)
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, ALTURA // 2 - 60)))

        subtitulo = self.font_texto.render(
            "Os 5 minutos acabaram. Você precisa reiniciar o jogo.", True, BRANCO
        )
        self.tela.blit(subtitulo, subtitulo.get_rect(center=(LARGURA // 2, ALTURA // 2 - 10)))

        pygame.draw.rect(self.tela, VERMELHO, self.botao_reiniciar_rect, border_radius=8)
        texto_botao = self.font_texto.render("Reiniciar jogo", True, BRANCO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_reiniciar_rect.center))

    def _reiniciar_jogo(self):
        """Restaura todo o progresso e volta para a tela de introdução."""
        self.estado = {
            "documento_objetivo_lido": False,
            "documento_colunas_lido": False,
            "painel_configurado": False,
            "config_correta": False,
            "tabulacao_concluida": False,
            "peca_liberada": False,
            "gaveta_destrancada": False,
            "gaveta_aberta": False,
            "cartoes_coletados": False,
        }
        self.itens_inventario = []

        self.painel_modo_selecionado = None
        self.painel_colunas_selecionadas = set()
        self.painel_mensagem = ""

        self.maquina_processando = False
        self.maquina_processamento_inicio = 0
        self.maquina_mensagem = "Pegue os cartoes perfurados e configure o painel para iniciar."

        self.gaveta_valores = [0, 0]
        self.gaveta_mensagem = "Gire os discos e clique em Testar."

        self.chat_ativo = False
        self.chat_input = ""
        self.chat_historico = []
        self.chat_carregando = False

        self.tela_ampliada_atual = None

        self.final_estado = "andando"
        self.final_transicao_inicio = 0

        self.tempo_inicio_jogo = None
        self.tempo_esgotado = False

        self.jogador.rect.topleft = (80, ALTURA - 200)
        self.jogador._atualizar_sprite(False)

        self.fase = "intro"

    # =================================================================
    # CONFIGURAÇÕES
    # =================================================================
    def _clicar_configuracoes(self, pos):
        if self.config_botao_vol_menos.collidepoint(pos):
            self.volume_musica = max(0, self.volume_musica - 10)
            pygame.mixer.music.set_volume(self.volume_musica / 100)
            return

        if self.config_botao_vol_mais.collidepoint(pos):
            self.volume_musica = min(100, self.volume_musica + 10)
            pygame.mixer.music.set_volume(self.volume_musica / 100)
            return

        if self.config_checkbox_sons.collidepoint(pos):
            self.sons_ativados = not self.sons_ativados
            return

        if self.config_botao_reiniciar.collidepoint(pos):
            self._reiniciar_jogo()
            return

    def _desenhar_configuracoes(self):
        titulo = self.font_titulo.render("Configurações", True, BRANCO)
        self.tela.blit(titulo, (self.zoom_rect.left + 40, self.zoom_rect.top + 40))

        rotulo_musica = self.font_texto.render("Volume da música", True, BRANCO)
        self.tela.blit(rotulo_musica, (self.zoom_rect.left + 40, self.zoom_rect.top + 118))

        pygame.draw.rect(self.tela, AZUL, self.config_botao_vol_menos, border_radius=6)
        menos = self.font_texto.render("-", True, BRANCO)
        self.tela.blit(menos, menos.get_rect(center=self.config_botao_vol_menos.center))

        valor_rect = pygame.Rect(
            self.config_botao_vol_menos.right + 8, self.config_botao_vol_menos.top,
            self.config_botao_vol_mais.left - self.config_botao_vol_menos.right - 16, 36,
        )
        pygame.draw.rect(self.tela, (60, 60, 60), valor_rect, border_radius=6)
        pygame.draw.rect(self.tela, BRANCO, valor_rect, width=1, border_radius=6)
        valor_texto = self.font_texto.render(f"{self.volume_musica}%", True, BRANCO)
        self.tela.blit(valor_texto, valor_texto.get_rect(center=valor_rect.center))

        pygame.draw.rect(self.tela, AZUL, self.config_botao_vol_mais, border_radius=6)
        mais = self.font_texto.render("+", True, BRANCO)
        self.tela.blit(mais, mais.get_rect(center=self.config_botao_vol_mais.center))

        pygame.draw.rect(
            self.tela, VERDE if self.sons_ativados else (60, 60, 60),
            self.config_checkbox_sons, border_radius=4,
        )
        pygame.draw.rect(self.tela, BRANCO, self.config_checkbox_sons, width=1, border_radius=4)
        if self.sons_ativados:
            check = self.font_pequena.render("X", True, BRANCO)
            self.tela.blit(check, check.get_rect(center=self.config_checkbox_sons.center))

        rotulo_sons = self.font_texto.render("Efeitos sonoros (cliques)", True, BRANCO)
        self.tela.blit(
            rotulo_sons, (self.config_checkbox_sons.right + 10, self.config_checkbox_sons.top - 2)
        )

        pygame.draw.rect(self.tela, VERMELHO, self.config_botao_reiniciar, border_radius=6)
        texto_reiniciar = self.font_texto.render("Reiniciar jogo", True, BRANCO)
        self.tela.blit(texto_reiniciar, texto_reiniciar.get_rect(center=self.config_botao_reiniciar.center))

    # =================================================================
    # ZOOM
    # =================================================================
    def abrir_zoom(self, modo):
        self.tela_ampliada_atual = modo
        if modo == "documento_objetivo":
            self.estado["documento_objetivo_lido"] = True
        elif modo == "documento_colunas":
            self.estado["documento_colunas_lido"] = True

    def fechar_zoom(self):
        if self.tela_ampliada_atual == "recompensa" and self.estado["peca_liberada"]:
            self.tela_ampliada_atual = None
            self._iniciar_fase_final()
            return
        self.tela_ampliada_atual = None

    # =================================================================
    # EVENTOS
    # =================================================================
    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False
                continue

            if self.fase == "intro":
                self._processar_evento_intro(evento)
                continue

            if self.fase == "final":
                self._processar_evento_final(evento)
                continue

            if self.fase == "tempo_esgotado":
                self._processar_evento_tempo_esgotado(evento)
                continue

            if self.chat_ativo:
                self._processar_evento_chat(evento)
                continue

            if self.tela_ampliada_atual is not None:
                self._processar_evento_zoom(evento)
                continue

            if evento.type == pygame.MOUSEBUTTONDOWN:
                for obj in self.interativos:
                    if obj.get("tipo") != "hud":
                        continue
                    rect = obj["img"].get_rect(topleft=obj["pos"])
                    if rect.collidepoint(evento.pos):
                        self._tocar_click()
                        if obj["nome"] == "chatbot":
                            self._abrir_chat_npc()
                        else:
                            modo_zoom = TELAS_AMPLIADAS.get(obj["nome"])
                            if modo_zoom:
                                self.abrir_zoom(modo_zoom)
                        break

            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_e:
                objeto_proximo = self._objeto_interativo_proximo()
                if objeto_proximo is not None:
                    self._tocar_click()
                    modo_zoom = TELAS_AMPLIADAS.get(objeto_proximo["nome"])
                    if modo_zoom:
                        self.abrir_zoom(modo_zoom)
                elif self._npc_proximo():
                    self._abrir_chat_npc()

    def _objeto_interativo_proximo(self):
        melhor_objeto = None
        menor_distancia = None

        for obj in self.interativos:
            if obj.get("tipo") != "mundo":
                continue

            rect = obj["img"].get_rect(topleft=obj["pos"])
            area_interacao = rect.inflate(RAIO_INTERACAO * 2, RAIO_INTERACAO * 2)

            if not area_interacao.colliderect(self.jogador.rect):
                continue

            dx = rect.centerx - self.jogador.rect.centerx
            dy = rect.centery - self.jogador.rect.centery
            distancia = (dx * dx + dy * dy) ** 0.5

            if menor_distancia is None or distancia < menor_distancia:
                menor_distancia = distancia
                melhor_objeto = obj

        return melhor_objeto

    def _npc_proximo(self):
        area_interacao = self.npc_rect.inflate(NPC_RAIO_INTERACAO * 2, NPC_RAIO_INTERACAO * 2)
        return area_interacao.colliderect(self.jogador.rect)

    def _processar_evento_zoom(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self.fechar_zoom()
            return

        if evento.type != pygame.MOUSEBUTTONDOWN:
            return

        if self.botao_fechar_rect.collidepoint(evento.pos):
            self.fechar_zoom()
            return

        if self.tela_ampliada_atual == "painel":
            self._clicar_painel(evento.pos)
        elif self.tela_ampliada_atual == "maquina":
            self._clicar_maquina(evento.pos)
        elif self.tela_ampliada_atual == "gaveta":
            self._clicar_gaveta(evento.pos)
        elif self.tela_ampliada_atual == "configuracoes":
            self._clicar_configuracoes(evento.pos)

    def _clicar_painel(self, pos):
        for modo, rect in self.painel_rects_modo.items():
            if rect.collidepoint(pos):
                self.painel_modo_selecionado = modo
                return

        for coluna, rect in self.painel_rects_colunas.items():
            if rect.collidepoint(pos):
                if coluna in self.painel_colunas_selecionadas:
                    self.painel_colunas_selecionadas.remove(coluna)
                else:
                    self.painel_colunas_selecionadas.add(coluna)
                return

        if self.painel_botao_confirmar.collidepoint(pos):
            if self.painel_modo_selecionado is None or not self.painel_colunas_selecionadas:
                self.painel_mensagem = "Selecione um modo e ao menos uma coluna."
                return

            self.estado["painel_configurado"] = True
            self.estado["config_correta"] = (
                self.painel_modo_selecionado == MODO_CORRETO
                and self.painel_colunas_selecionadas == COLUNAS_CORRETAS
            )
            self.painel_mensagem = "Configuração salva. Você já pode iniciar a máquina."
            self.maquina_mensagem = "Painel configurado. Pressione Iniciar."

    def _clicar_maquina(self, pos):
        if self.maquina_botao_iniciar.collidepoint(pos):
            if not self.estado["cartoes_coletados"]:
                self.maquina_mensagem = (
                    "Voce ainda nao tem os cartoes perfurados. "
                    "Eles estao na gaveta trancada da escrivaninha."
                )
                return
            if not self.estado["painel_configurado"]:
                self.maquina_mensagem = "Configure o painel antes de iniciar a tabulação."
                return
            if self.maquina_processando:
                return
            self.maquina_processando = True
            self.maquina_processamento_inicio = pygame.time.get_ticks()
            self.maquina_mensagem = "Processando cartões..."
            return

        if self.estado["tabulacao_concluida"] and self.estado["config_correta"]:
            if self.maquina_botao_compartimento.collidepoint(pos):
                self.estado["peca_liberada"] = True
                self._adicionar_item_inventario(
                    "Peça da Máquina do Tempo",
                    self.img_cartoes_inventario,
                    "Obtida ao concluir a tabulação corretamente.",
                )
                self.abrir_zoom("recompensa")

    def _clicar_gaveta(self, pos):
        if not self.estado["gaveta_destrancada"]:
            for i, rect in enumerate(self.gaveta_setas_cima):
                if rect.collidepoint(pos):
                    self.gaveta_valores[i] = (self.gaveta_valores[i] + 1) % 10
                    return
            for i, rect in enumerate(self.gaveta_setas_baixo):
                if rect.collidepoint(pos):
                    self.gaveta_valores[i] = (self.gaveta_valores[i] - 1) % 10
                    return

            if self.gaveta_botao_testar.collidepoint(pos):
                if tuple(self.gaveta_valores) == CADEADO_GAVETA_CORRETO:
                    self.estado["gaveta_destrancada"] = True
                    self.gaveta_mensagem = "Clique! A gaveta destrancou."
                else:
                    self.gaveta_mensagem = "Combinação errada. Pense na pista do chatbot."
            return

        if not self.estado["gaveta_aberta"]:
            self.estado["gaveta_aberta"] = True
            self.gaveta_mensagem = "Gaveta aberta. Pegue os cartões perfurados."
            return

        if not self.estado["cartoes_coletados"] and self.gaveta_area_cartoes.collidepoint(pos):
            self.estado["cartoes_coletados"] = True
            self._adicionar_item_inventario(
                "Cartões perfurados",
                self.img_cartoes_inventario,
                "Usados para configurar a máquina de tabulação.",
            )
            self.gaveta_mensagem = "Cartões perfurados coletados! Já podem ser usados na máquina."
            self.maquina_mensagem = "Cartões prontos. Configure o painel e pressione Iniciar."

    # =================================================================
    # CHAT COM O PROFESSOR HERMANN (Ollama)
    # =================================================================
    def _abrir_chat_npc(self):
        self.chat_ativo = True
        self.chat_input = ""
        self._tocar_click()

    def _fechar_chat_npc(self):
        self.chat_ativo = False
        self.chat_input = ""

    def _processar_evento_chat(self, evento):
        if evento.type == pygame.TEXTINPUT:
            if len(self.chat_input) < 200:
                self.chat_input += evento.text
            return

        if evento.type != pygame.KEYDOWN:
            return

        if evento.key == pygame.K_ESCAPE:
            self._fechar_chat_npc()
            return

        if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._enviar_pergunta_ao_professor()
            return

        if evento.key == pygame.K_BACKSPACE:
            self.chat_input = self.chat_input[:-1]
            return

    def _construir_prompt_sistema(self):
        """Monta o prompt do Hermann com uma dica sobre o passo atual
        da missão, seguindo a ordem real de resolução dos enigmas."""
        if not self.estado["documento_objetivo_lido"]:
            passo_atual = (
                "O cientista ainda não leu o documento que explica o "
                "objetivo da missão. Dê a dica de que esse documento "
                "está escondido entre os livros da prateleira da sala, "
                "sem dizer exatamente qual livro."
            )
        elif not self.estado["gaveta_destrancada"]:
            passo_atual = (
                "O cientista precisa destrancar a gaveta da escrivaninha, "
                "fechada com um cadeado de dois dígitos. Dê apenas a "
                "pista de que a combinação tem a ver com 'quantas horas "
                "tem um dia inteiro', sem falar o número diretamente."
            )
        elif not self.estado["cartoes_coletados"]:
            passo_atual = (
                "A gaveta já está destrancada. Incentive o cientista a "
                "abri-la e pegar os cartões perfurados guardados nela."
            )
        elif not self.estado["painel_configurado"] or not self.estado["config_correta"]:
            passo_atual = (
                "O cientista precisa configurar o painel da máquina para "
                "contar apenas 'trabalhadores adultos'. Não diga o modo "
                "nem as colunas certas; apenas lembre que ele deve ligar "
                "a missão (contar trabalhadores adultos) às colunas do "
                "documento que já leu."
            )
        elif not self.estado["gaveta_destrancada"]:
            passo_atual = (
                "O cientista precisa destrancar a gaveta da escrivaninha, "
                "fechada com um cadeado numerico de dois digitos (0 a 9 "
                "cada). Nao existe nenhuma etiqueta, nota ou pista escrita "
                "na gaveta ou na sala — a unica pista que voce pode dar e "
                "verbal: a combinacao tem a ver com 'quantas horas tem um "
                "dia inteiro'. Nao invente objetos que nao foram citados "
                "aqui. Nao diga o numero diretamente."
            )
        else:
            passo_atual = (
                "O cientista já concluiu a tabulação corretamente. "
                "Parabenize-o pelo trabalho."
            )

        return PROMPT_SISTEMA_HERMANN + " Passo atual da missão: " + passo_atual

    def _enviar_pergunta_ao_professor(self):
        pergunta = self.chat_input.strip()
        if not pergunta or self.chat_carregando:
            return

        self.chat_historico.append(("jogador", pergunta))
        self.chat_input = ""
        self.chat_carregando = True

        prompt_sistema = self._construir_prompt_sistema()
        thread = threading.Thread(
            target=self._consultar_ollama, args=(pergunta, prompt_sistema), daemon=True
        )
        thread.start()

    def _consultar_ollama(self, pergunta, prompt_sistema):
        mensagens = [{"role": "system", "content": prompt_sistema}]

        for autor, texto in self.chat_historico[-6:]:
            papel = "user" if autor == "jogador" else "assistant"
            mensagens.append({"role": papel, "content": texto})

        payload = {
            "model": OLLAMA_MODELO,
            "messages": mensagens,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 100,
            },
        }
        dados = json.dumps(payload).encode("utf-8")
        requisicao = urllib.request.Request(
            OLLAMA_URL, data=dados, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(requisicao, timeout=OLLAMA_TIMEOUT_SEGUNDOS) as resposta:
                corpo = json.loads(resposta.read().decode("utf-8"))
                texto_resposta = corpo.get("message", {}).get("content", "").strip()
                if not texto_resposta:
                    texto_resposta = (
                        "Hmm, minhas ideias fugiram por um instante. "
                        "Pode repetir a pergunta?"
                    )
        except Exception as e:
            print(f"[ERRO OLLAMA] {type(e).__name__}: {e}")
            texto_resposta = (
                "(Nao consegui falar com o Professor Hermann agora — "
                "verifique se o Ollama esta rodando com o modelo "
                f"'{OLLAMA_MODELO}' instalado.)"
            )
        self.chat_resposta_queue.put(texto_resposta)

    # =================================================================
    # ATUALIZAR
    # =================================================================
    def atualizar(self):
        if self.fase == "intro":
            return

        if self.fase == "final":
            self._atualizar_final()
            return

        if self.fase == "tempo_esgotado":
            return

        if self._tempo_restante_ms() <= 0:
            self.tempo_esgotado = True
            self.fase = "tempo_esgotado"
            return

        try:
            resposta = self.chat_resposta_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            self.chat_historico.append(("hermann", resposta))
            self.chat_carregando = False

        if self.maquina_processando:
            agora = pygame.time.get_ticks()
            if agora - self.maquina_processamento_inicio >= DURACAO_PROCESSAMENTO_MS:
                self.maquina_processando = False
                self.estado["tabulacao_concluida"] = True
                if self.estado["config_correta"]:
                    self.maquina_mensagem = (
                        f"Tabulação concluída! Total encontrado: {RESULTADO_CORRETO} registros."
                    )
                else:
                    self.maquina_mensagem = (
                        "Resultado inconsistente. Reconfigure o painel e tente novamente."
                    )
                    self.estado["painel_configurado"] = False
                    self.estado["tabulacao_concluida"] = False

        if self.tela_ampliada_atual is not None or self.chat_ativo:
            return

        teclas = pygame.key.get_pressed()
        limites = self.tela.get_rect()
        self.jogador.mover(teclas, limites)

    # =================================================================
    # DESENHAR
    # =================================================================
    def desenhar(self):
        if self.fase == "intro":
            self._desenhar_intro()
            pygame.display.update()
            return

        if self.fase == "final":
            self._desenhar_final()
            pygame.display.update()
            return

        if self.fase == "tempo_esgotado":
            self._desenhar_tempo_esgotado()
            pygame.display.update()
            return

        self.tela.blit(self.fundo, (0, 0))

        for img, pos in self.decoracao:
            self.tela.blit(img, pos)

        self.tela.blit(self.personagem_cenario, self.personagem_cenario_pos)

        for obj in self.interativos:
            if obj.get("desenhar", True):
                self.tela.blit(obj["img"], obj["pos"])

        if self.estado["gaveta_aberta"] and not self.estado["cartoes_coletados"]:
            self.tela.blit(self.img_cartoes_mundo, self.cartoes_mundo_pos)

        self.jogador.desenhar(self.tela)

        if self.tela_ampliada_atual is None and not self.chat_ativo:
            self._desenhar_dica_interacao()

        if self.chat_ativo:
            self._desenhar_chat_npc()

        if self.tela_ampliada_atual is not None:
            self._desenhar_moldura_zoom()
            if self.tela_ampliada_atual == "documento_objetivo":
                self._desenhar_documento(
                    self.img_objetivo,
                    "Documento: Objetivo da Tabulação",
                    [
                        '"Conte apenas os registros de trabalhadores adultos."',
                        "Os cartoes perfurados necessarios estao guardados na "
                        "gaveta da escrivaninha, trancada com um cadeado.",
                    ],
                )
            elif self.tela_ampliada_atual == "documento_colunas":
                linhas = [f"Coluna {i + 1}: {c}" for i, c in enumerate(COLUNAS_DISPONIVEIS)]
                self._desenhar_documento(
                    self.img_documento_colunas,
                    "Documento: Significado das Colunas",
                    ["Cada coluna representa um dado do cartão perfurado."] + linhas,
                )
            elif self.tela_ampliada_atual == "painel":
                self._desenhar_painel()
            elif self.tela_ampliada_atual == "maquina":
                self._desenhar_maquina()
            elif self.tela_ampliada_atual == "gaveta":
                self._desenhar_gaveta()
            elif self.tela_ampliada_atual == "inventario":
                self._desenhar_inventario()
            elif self.tela_ampliada_atual == "recompensa":
                self._desenhar_recompensa()
            elif self.tela_ampliada_atual == "configuracoes":
                self._desenhar_configuracoes()

        self._desenhar_cronometro()

        pygame.display.update()

    def _desenhar_dica_interacao(self):
        objeto_proximo = self._objeto_interativo_proximo()
        if objeto_proximo is not None:
            rect_referencia = objeto_proximo["img"].get_rect(topleft=objeto_proximo["pos"])
            texto_dica = "Aperte E"
        elif self._npc_proximo():
            rect_referencia = self.npc_rect
            texto_dica = "Aperte E para conversar"
        else:
            return

        centro_x = rect_referencia.centerx
        topo_y = rect_referencia.top - 14

        texto = self.font_pequena.render(texto_dica, True, BRANCO)
        largura_balao = texto.get_width() + 20
        balao = pygame.Rect(0, 0, largura_balao, 26)
        balao.center = (centro_x, max(topo_y, 20))

        overlay = pygame.Surface(balao.size, pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 190))
        self.tela.blit(overlay, balao.topleft)
        pygame.draw.rect(self.tela, BRANCO, balao, width=1, border_radius=6)
        self.tela.blit(texto, texto.get_rect(center=balao.center))

    def _desenhar_chat_npc(self):
        largura_caixa = 460
        linhas_renderizadas = []

        historico_visivel = self.chat_historico[-CHAT_HISTORICO_VISIVEL:]
        for autor, texto in historico_visivel:
            prefixo = "Voce: " if autor == "jogador" else "Prof. Hermann: "
            cor = (200, 220, 255) if autor == "jogador" else BRANCO
            for linha in quebrar_texto(prefixo + texto, self.font_pequena, largura_caixa - 30):
                linhas_renderizadas.append((linha, cor))

        if self.chat_carregando:
            linhas_renderizadas.append(("Prof. Hermann esta pensando...", (210, 200, 150)))

        altura_historico = len(linhas_renderizadas) * 20
        altura_caixa = 100 + altura_historico

        caixa = pygame.Rect(0, 0, largura_caixa, altura_caixa)
        caixa.centerx = self.npc_rect.centerx

        topo_desejado = self.npc_rect.top - 10 - altura_caixa
        caixa.top = max(10, topo_desejado)
        caixa.left = max(10, min(caixa.left, LARGURA - largura_caixa - 10))

        overlay = pygame.Surface(caixa.size, pygame.SRCALPHA)
        overlay.fill((20, 20, 25, 225))
        self.tela.blit(overlay, caixa.topleft)
        pygame.draw.rect(self.tela, BRANCO, caixa, width=2, border_radius=10)

        titulo = self.font_texto.render("Professor Hermann", True, (255, 210, 120))
        self.tela.blit(titulo, (caixa.left + 15, caixa.top + 10))

        y = caixa.top + 38
        for linha, cor in linhas_renderizadas:
            render = self.font_pequena.render(linha, True, cor)
            self.tela.blit(render, (caixa.left + 15, y))
            y += 20

        campo_input = pygame.Rect(caixa.left + 15, caixa.bottom - 55, caixa.width - 30, 28)
        pygame.draw.rect(self.tela, (250, 250, 250), campo_input, border_radius=4)
        pygame.draw.rect(self.tela, (100, 100, 100), campo_input, width=1, border_radius=4)

        cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        texto_input = self.font_pequena.render(self.chat_input + cursor, True, (20, 20, 20))
        self.tela.blit(texto_input, (campo_input.left + 8, campo_input.top + 6))

        dica = self.font_pequena.render("Enter: enviar   |   ESC: sair", True, (200, 200, 200))
        self.tela.blit(dica, (caixa.left + 15, caixa.bottom - 22))

    def _desenhar_moldura_zoom(self):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.tela.blit(overlay, (0, 0))

        moldura = self.zoom_rect.inflate(20, 20)
        pygame.draw.rect(self.tela, (30, 30, 30), moldura, border_radius=8)
        pygame.draw.rect(self.tela, (200, 200, 200), moldura, width=2, border_radius=8)

        pygame.draw.rect(self.tela, VERMELHO, self.botao_fechar_rect, border_radius=6)
        texto_x = self.font_texto.render("X", True, BRANCO)
        self.tela.blit(texto_x, texto_x.get_rect(center=self.botao_fechar_rect.center))

    def _desenhar_documento(self, imagem, titulo, linhas_texto):
        self.tela.blit(imagem, self.zoom_rect)

        caixa_texto = pygame.Rect(self.zoom_rect.left, self.zoom_rect.bottom - 130, self.zoom_rect.width, 130)
        pygame.draw.rect(self.tela, (0, 0, 0, 200), caixa_texto)
        overlay = pygame.Surface(caixa_texto.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.tela.blit(overlay, caixa_texto.topleft)

        titulo_render = self.font_titulo.render(titulo, True, BRANCO)
        self.tela.blit(titulo_render, (caixa_texto.left + 15, caixa_texto.top + 8))

        y = caixa_texto.top + 45
        for linha in linhas_texto:
            for sub in quebrar_texto(linha, self.font_pequena, caixa_texto.width - 30):
                render = self.font_pequena.render(sub, True, BRANCO)
                self.tela.blit(render, (caixa_texto.left + 15, y))
                y += 22

    def _desenhar_painel(self):
        self.tela.blit(self.img_painel_fundo, self.zoom_rect)

        titulo = self.font_titulo.render("Painel de Configuração", True, BRANCO)
        self.tela.blit(titulo, (self.zoom_rect.left + 40, self.zoom_rect.top + 45))

        rotulo_modo = self.font_pequena.render("Modo:", True, BRANCO)
        self.tela.blit(rotulo_modo, (self.zoom_rect.left + 40, self.zoom_rect.top + 68))

        for modo, rect in self.painel_rects_modo.items():
            selecionado = modo == self.painel_modo_selecionado
            cor_fundo = AZUL if selecionado else (60, 60, 60)
            pygame.draw.rect(self.tela, cor_fundo, rect, border_radius=6)
            pygame.draw.rect(self.tela, BRANCO, rect, width=1, border_radius=6)
            texto = self.font_pequena.render(modo, True, BRANCO)
            self.tela.blit(texto, texto.get_rect(center=rect.center))

        rotulo_colunas = self.font_pequena.render("Colunas:", True, BRANCO)
        self.tela.blit(rotulo_colunas, (self.zoom_rect.left + 40, self.zoom_rect.top + 128))

        for coluna, rect in self.painel_rects_colunas.items():
            marcado = coluna in self.painel_colunas_selecionadas
            caixa = pygame.Rect(rect.left, rect.top + 4, 22, 22)
            pygame.draw.rect(self.tela, VERDE if marcado else (60, 60, 60), caixa, border_radius=4)
            pygame.draw.rect(self.tela, BRANCO, caixa, width=1, border_radius=4)
            if marcado:
                texto_check = self.font_pequena.render("X", True, BRANCO)
                self.tela.blit(texto_check, texto_check.get_rect(center=caixa.center))

            texto_label = self.font_pequena.render(coluna, True, BRANCO)
            self.tela.blit(texto_label, (caixa.right + 10, rect.top + 3))

        pygame.draw.rect(self.tela, VERDE, self.painel_botao_confirmar, border_radius=6)
        texto_confirmar = self.font_texto.render("Confirmar", True, BRANCO)
        self.tela.blit(texto_confirmar, texto_confirmar.get_rect(center=self.painel_botao_confirmar.center))

        if self.painel_mensagem:
            for i, linha in enumerate(quebrar_texto(self.painel_mensagem, self.font_pequena, self.zoom_rect.width - 80)):
                msg = self.font_pequena.render(linha, True, BRANCO)
                self.tela.blit(msg, (self.zoom_rect.left + 40, self.painel_botao_confirmar.top - 45 + i * 20))

    def _desenhar_maquina(self):
        self.tela.blit(self.img_maquina_fundo, self.zoom_rect)

        titulo = self.font_titulo.render("Máquina de Tabulação", True, BRANCO)
        self.tela.blit(titulo, (self.zoom_rect.left + 40, self.zoom_rect.top + 30))

        for i, linha in enumerate(quebrar_texto(self.maquina_mensagem, self.font_texto, self.zoom_rect.width - 80)):
            msg = self.font_texto.render(linha, True, BRANCO)
            self.tela.blit(msg, (self.zoom_rect.left + 40, self.zoom_rect.top + 80 + i * 26))

        cor_botao = (120, 120, 120) if self.maquina_processando else AZUL
        pygame.draw.rect(self.tela, cor_botao, self.maquina_botao_iniciar, border_radius=6)
        texto_iniciar = self.font_texto.render(
            "Processando..." if self.maquina_processando else "Iniciar", True, BRANCO
        )
        self.tela.blit(texto_iniciar, texto_iniciar.get_rect(center=self.maquina_botao_iniciar.center))

        if self.estado["tabulacao_concluida"] and self.estado["config_correta"]:
            pygame.draw.rect(self.tela, VERDE, self.maquina_botao_compartimento, border_radius=6)
            texto_compartimento = self.font_texto.render("Abrir compartimento", True, BRANCO)
            self.tela.blit(
                texto_compartimento, texto_compartimento.get_rect(center=self.maquina_botao_compartimento.center)
            )

    def _desenhar_gaveta(self):
        if self.estado["gaveta_destrancada"]:
            fundo = self.img_gaveta_aberta_zoom if self.estado["gaveta_aberta"] else self.img_gaveta_fechada_zoom
        else:
            fundo = self.img_gaveta_fechada_zoom
        self.tela.blit(fundo, self.zoom_rect)

        titulo = self.font_titulo.render("Gaveta da Escrivaninha", True, BRANCO)
        self.tela.blit(titulo, (self.zoom_rect.left + 40, self.zoom_rect.top + 30))

        if not self.estado["gaveta_destrancada"]:
            for i, rect in enumerate(self.gaveta_rects_disco):
                pygame.draw.rect(self.tela, (60, 60, 60), rect, border_radius=8)
                pygame.draw.rect(self.tela, BRANCO, rect, width=2, border_radius=8)
                texto_digito = self.font_titulo.render(str(self.gaveta_valores[i]), True, BRANCO)
                self.tela.blit(texto_digito, texto_digito.get_rect(center=rect.center))

            for rect in self.gaveta_setas_cima:
                pygame.draw.rect(self.tela, AZUL, rect, border_radius=6)
                seta = self.font_texto.render("^", True, BRANCO)
                self.tela.blit(seta, seta.get_rect(center=rect.center))

            for rect in self.gaveta_setas_baixo:
                pygame.draw.rect(self.tela, AZUL, rect, border_radius=6)
                seta = self.font_texto.render("v", True, BRANCO)
                self.tela.blit(seta, seta.get_rect(center=rect.center))

            pygame.draw.rect(self.tela, VERDE, self.gaveta_botao_testar, border_radius=6)
            texto_testar = self.font_texto.render("Testar", True, BRANCO)
            self.tela.blit(texto_testar, texto_testar.get_rect(center=self.gaveta_botao_testar.center))

        elif self.estado["gaveta_aberta"] and not self.estado["cartoes_coletados"]:
            self.tela.blit(self.img_cartoes_zoom, self.gaveta_area_cartoes)
            pygame.draw.rect(self.tela, BRANCO, self.gaveta_area_cartoes, width=2, border_radius=6)
            texto_cartoes = self.font_texto.render("Clique para pegar", True, BRANCO)
            self.tela.blit(texto_cartoes, (self.gaveta_area_cartoes.left, self.gaveta_area_cartoes.bottom + 5))
        for i, linha in enumerate(quebrar_texto(self.gaveta_mensagem, self.font_pequena, self.zoom_rect.width - 80)):
            msg = self.font_pequena.render(linha, True, BRANCO)
            self.tela.blit(msg, (self.zoom_rect.left + 40, self.zoom_rect.bottom - 40 + i * 20))

    def _desenhar_inventario(self):
        # Fundo simples (não há arte dedicada para o inventário).
        pygame.draw.rect(self.tela, (35, 33, 38), self.zoom_rect)

        titulo = self.font_titulo.render("Inventário", True, BRANCO)
        self.tela.blit(titulo, (self.zoom_rect.left + 40, self.zoom_rect.top + 35))

        if not self.itens_inventario:
            vazio = self.font_texto.render("Nenhum item coletado ainda.", True, (200, 200, 200))
            self.tela.blit(vazio, (self.zoom_rect.left + 40, self.zoom_rect.top + 100))
            return

        y = self.zoom_rect.top + 90
        largura_slot = self.zoom_rect.width - 80
        altura_slot = 64
        espaco = 12

        for item in self.itens_inventario:
            slot = pygame.Rect(self.zoom_rect.left + 40, y, largura_slot, altura_slot)
            pygame.draw.rect(self.tela, (55, 55, 60), slot, border_radius=8)
            pygame.draw.rect(self.tela, BRANCO, slot, width=1, border_radius=8)

            icone = pygame.transform.scale(item["icone"], (48, 48))
            self.tela.blit(icone, (slot.left + 8, slot.top + 8))

            nome_render = self.font_texto.render(item["nome"], True, BRANCO)
            self.tela.blit(nome_render, (slot.left + 68, slot.top + 8))

            if item["descricao"]:
                desc_render = self.font_pequena.render(item["descricao"], True, (200, 200, 200))
                self.tela.blit(desc_render, (slot.left + 68, slot.top + 34))

            y += altura_slot + espaco
            if y > self.zoom_rect.bottom - altura_slot:
                break

    def _desenhar_recompensa(self):
        self.tela.blit(self.img_recompensa, self.zoom_rect)

        caixa_texto = pygame.Rect(self.zoom_rect.left, self.zoom_rect.bottom - 90, self.zoom_rect.width, 90)
        overlay = pygame.Surface(caixa_texto.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.tela.blit(overlay, caixa_texto.topleft)

        titulo = self.font_titulo.render("Peça da Máquina do Tempo obtida!", True, BRANCO)
        self.tela.blit(titulo, (caixa_texto.left + 15, caixa_texto.top + 15))

        subtitulo = self.font_pequena.render(
            "Você concluiu a tabulação corretamente. A fase está completa.", True, BRANCO
        )
        self.tela.blit(subtitulo, (caixa_texto.left + 15, caixa_texto.top + 50))

    def rodar(self):
        while self.rodando:
            self.processar_eventos()
            self.atualizar()
            self.desenhar()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    jogo = Jogo(personagem_escolhido=2)
    jogo.rodar()
