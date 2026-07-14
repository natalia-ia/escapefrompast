import pygame
import sys

pygame.init()

LARGURA, ALTURA = 960, 600
CINZA = (150, 150, 150)
BRANCO = (240, 240, 240)
VERDE = (60, 170, 90)
VERMELHO = (180, 60, 60)
AZUL = (70, 110, 200)
PRETO = (20, 20, 20)

ASSETS = {
    # Cenário
    "fundo": "assets/cenario/cenario_fase3.png",

    # Decoração
    "corpo_personagem": "assets/decoracao/corpo do personagem.png",

    # Objetos interativos (versão pequena, no cenário)
    "cartoes": "assets/interativos/cartoes.png",
    "documento_codigo": "assets/interativos/documento_codigo.png",
    "icone_chatbot": "assets/interativos/icone_chatbot.png",
    "icone_inventario": "assets/interativos/icone_inventario.png",
    "maquina_tabulacao": "assets/interativos/maquina_tabulacao.png",
    "painel_config": "assets/interativos/painel_config.png",
    "gaveta_fechada": "assets/interativos/gaveta_fechada.png",
    "gaveta_aberta": "assets/interativos/gaveta_aberta.png",

    # Telas ampliadas
    "objetivo": "assets/interativos/objetivo.png",
    "painel_ampliado": "assets/interativos/painel_ampliado.png",
    "processando3": "assets/interativos/processando3.png",
    "saindo": "assets/interativos/saindo.png",
    "chatbot_tela": "assets/interativos/chatbot_tela.png",

    # Personagem 1
    "p1_parado": "assets/personagem1/p1_parada.png",
    "p1_andando1": "assets/personagem1/p1_andando.png",
    "p1_andando2": "assets/personagem1/p1_andando2.png",

    # Personagem 2
    "p2_parado": "assets/personagem2/p2_parado.png",
    "p2_andando1": "assets/personagem2/p2_andando.png",
    "p2_andando2": "assets/personagem2/p2_andando2.png",

    # Áudios
    "musica_ambiente": "assets/musicas/ambiente.mp3",
    "som_click": "assets/musicas/sons/click.mp3",
}

# ---------------------------------------------------------------
# QUAL TELA AMPLIADA (MODO) ABRE PARA CADA OBJETO INTERAGIDO
# (objetos do cenário: jogador se aproxima e aperta "E";
#  ícones de HUD: continuam sendo clicados com o mouse)
# ---------------------------------------------------------------
TELAS_AMPLIADAS = {
    "chatbot": "chatbot",                   # conversa: missão + dica do enigma da gaveta
    "documento codigo": "documento_objetivo",  # documento que revela o objetivo da missão
    "documento colunas": "documento_colunas",  # documento explicando as colunas
    "painel config": "painel",              # painel interativo
    "maquina tabulacao": "maquina",         # máquina interativa
    "gaveta": "gaveta",                     # cadeado/gaveta: aqui ficam os cartões de verdade
}

TAMANHO_ZOOM = (700, 480)

# Distância (em pixels) além da hitbox do objeto em que a interação por
# proximidade + tecla "E" já fica disponível para o jogador.
RAIO_INTERACAO = 40

# ---------------------------------------------------------------
# REGRAS DO ENIGMA PRINCIPAL (missão da tabulação)
# O documento de objetivo pede: "Conte apenas trabalhadores adultos"
# então a configuração correta é Modo = Contar, colunas = Adulto + Trabalhador
# ---------------------------------------------------------------
COLUNAS_DISPONIVEIS = ["Homem", "Mulher", "Adulto", "Criança", "Trabalhador", "Estudante"]
MODOS_DISPONIVEIS = ["Contar", "Classificar", "Somar"]

COLUNAS_CORRETAS = {"Adulto", "Trabalhador"}
MODO_CORRETO = "Contar"
RESULTADO_CORRETO = 4  # "4 registros", conforme o GDD

DURACAO_PROCESSAMENTO_MS = 1400


CADEADO_GAVETA_CORRETO = (2, 4)  # resposta da charada = "24" (horas do dia)

CONVERSA_CHATBOT = [
    ("chatbot", "Ainda bem que voce chegou! Sua missao aqui e simples: "
                "configurar a maquina de tabulacao para contar apenas os "
                "registros de trabalhadores adultos."),
    ("chatbot", "Os cartoes perfurados que voce vai usar na maquina estao "
                "guardados na gaveta da escrivaninha, mas ela esta trancada "
                "com um cadeado de dois numeros."),
    ("chatbot", "Para descobrir a combinacao, pense nisso: 'Quantas horas "
                "tem um dia inteiro, do comeco da manha ao fim da noite?'"),
    ("chatbot", "Ajuste os dois discos do cadeado para esse numero e a "
                "gaveta deve abrir, liberando os cartoes que voce precisa."),
]


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
    """Cria uma superfície totalmente transparente, do tamanho informado.

    Usada para objetos que precisam continuar clicáveis/interagíveis
    (têm um retângulo de colisão), mas que não devem aparecer
    visualmente no cenário — por exemplo a gaveta, cujo desenho já faz
    parte da arte de fundo da sala.
    """
    superficie = pygame.Surface(tamanho, pygame.SRCALPHA)
    superficie.fill((0, 0, 0, 0))
    return superficie


def quebrar_texto(texto, fonte, largura_max):
    """Quebra um texto em várias linhas para caber em uma largura máxima."""
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

        # Fontes (carregadas uma vez só)
        self.font_titulo = pygame.font.SysFont(None, 34)
        self.font_texto = pygame.font.SysFont(None, 24)
        self.font_pequena = pygame.font.SysFont(None, 20)

        # ---------------------------------------------------------------
        # ESTADO DO ENIGMA (segue o GDD) + estado da gaveta secundária
        # ---------------------------------------------------------------
        self.estado = {
            "documento_objetivo_lido": False,
            "documento_colunas_lido": False,
            "painel_configurado": False,
            "config_correta": False,
            "tabulacao_concluida": False,
            "peca_liberada": False,

            # Enigma da gaveta (independente da história principal)
            "gaveta_destrancada": False,
            "gaveta_aberta": False,
            "cartoes_coletados": False,
        }

        # Seleções atuais do jogador no painel
        self.painel_modo_selecionado = None
        self.painel_colunas_selecionadas = set()
        self.painel_mensagem = ""  # feedback ao confirmar

        # Estado da máquina
        self.maquina_processando = False
        self.maquina_processamento_inicio = 0
        self.maquina_mensagem = "Pegue os cartoes perfurados e configure o painel para iniciar."

        # Estado do cadeado da gaveta
        self.gaveta_valores = [0, 0]
        self.gaveta_mensagem = "Gire os discos e clique em Testar."

        # Índice da mensagem atual mostrada na tela do chatbot
        self.chatbot_indice_mensagem = 0

        # ---------------------------------------------------------------
        # ZOOM: geometria e imagens de fundo de cada tela ampliada
        # ---------------------------------------------------------------
        self.tela_ampliada_atual = None  # None ou string do modo (ver TELAS_AMPLIADAS)

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
        self.img_documento_colunas = carregar_imagem(ASSETS["documento_codigo"], TAMANHO_ZOOM, CINZA, "documento colunas")
        self.img_painel_fundo = carregar_imagem(ASSETS["painel_ampliado"], TAMANHO_ZOOM, CINZA, "painel")
        self.img_maquina_fundo = carregar_imagem(ASSETS["processando3"], TAMANHO_ZOOM, CINZA, "maquina")
        self.img_recompensa = carregar_imagem(ASSETS["saindo"], TAMANHO_ZOOM, CINZA, "recompensa")
        self.img_chatbot_fundo = carregar_imagem(ASSETS["chatbot_tela"], TAMANHO_ZOOM, CINZA, "chatbot")
        self.img_gaveta_fechada_zoom = carregar_imagem(ASSETS["gaveta_fechada"], TAMANHO_ZOOM, CINZA, "gaveta fechada")
        self.img_gaveta_aberta_zoom = carregar_imagem(ASSETS["gaveta_aberta"], TAMANHO_ZOOM, CINZA, "gaveta aberta")

        # ---------------------------------------------------------------
        # WIDGETS DO PAINEL (checkboxes de colunas + radios de modo)
        # ---------------------------------------------------------------
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

        # ---------------------------------------------------------------
        # WIDGETS DA MÁQUINA
        # ---------------------------------------------------------------
        self.maquina_botao_iniciar = pygame.Rect(
            self.zoom_rect.centerx - 90, self.zoom_rect.bottom - 130, 180, 40
        )
        self.maquina_botao_compartimento = pygame.Rect(
            self.zoom_rect.centerx - 110, self.zoom_rect.bottom - 75, 220, 40
        )

        # ---------------------------------------------------------------
        # WIDGETS DO CADEADO DA GAVETA (2 discos, cada um 0-9)
        # ---------------------------------------------------------------
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
        # Área clicável dos cartões, usada só depois que a gaveta é aberta
        self.gaveta_area_cartoes = pygame.Rect(
            self.zoom_rect.centerx - 100, self.zoom_rect.top + 260, 200, 120
        )

        # ---------------------------------------------------------------
        # WIDGET DO CHATBOT (avançar mensagem)
        # ---------------------------------------------------------------
        self.chatbot_botao_avancar = pygame.Rect(
            self.zoom_rect.right - 170, self.zoom_rect.bottom - 55, 130, 38
        )

        # Imagem dos cartões perfurados exibida dentro da gaveta quando ela
        # está aberta e ainda não foram coletados (substitui a antiga caixa
        # de cartões, que foi removida do jogo).
        self.img_cartoes_mundo = carregar_imagem(ASSETS["cartoes"], (150, 90), CINZA, "cartoes")
        self.cartoes_mundo_pos = (460, 425)

        self.fundo = carregar_imagem(ASSETS["fundo"], (LARGURA, ALTURA), label="sala")

        # ---------------------------------------------------------------
        # DECORAÇÃO (itens fixos, não clicáveis)
        # (sem itens de decoração por enquanto)
        # ---------------------------------------------------------------
        self.decoracao = []

        self.personagem_cenario = carregar_imagem(
            ASSETS["corpo_personagem"], (350, 350), CINZA, "personagem cenario"
        )
        self.personagem_cenario_pos = (540, 240)

        # ---------------------------------------------------------------
        # OBJETOS INTERATIVOS
        # Cada objeto tem um "tipo":
        # - "mundo": objeto físico da sala. O jogador precisa ANDAR até
        #   perto dele e apertar a tecla E para interagir (sem mouse).
        # - "hud": ícone fixo de interface (inventário/chatbot), que
        #   continua sendo clicado normalmente com o mouse, já que não
        #   faz parte do espaço físico percorrido pelo personagem.
        #
        # Layout:
        # - maquina_tabulacao: encostada na parede da esquerda
        # - painel_config: na parede, centralizado acima da mesa
        # - gaveta: na frente da mesa, abaixo do tampo (item de verdade).
        #   É invisível (hitbox transparente) porque o desenho da gaveta
        #   já faz parte da arte de fundo da sala; só existe para marcar
        #   a área onde o jogador pode interagir com a tecla E.
        # - documento_codigo / documento_colunas: presos na parede,
        #   perto da estante
        # - icone_inventario / icone_chatbot: HUD, canto superior esquerdo
        # ---------------------------------------------------------------
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
            {
                "img": carregar_imagem(ASSETS["documento_codigo"], (95, 90), CINZA, "documento codigo"),
                "pos": (850, 455),
                "nome": "documento codigo",
                "tipo": "mundo",
                "desenhar": True,
            },
            {
                "img": carregar_imagem(ASSETS["documento_codigo"], (95, 90), CINZA, "documento colunas"),
                "pos": (850, 340),
                "nome": "documento colunas",
                "tipo": "mundo",
                "desenhar": True,
            },
            {
                "img": carregar_imagem(ASSETS["icone_inventario"], (80, 80), CINZA, "inventario"),
                "pos": (15, 15),
                "nome": "inventario",
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

        try:
            pygame.mixer.music.load(ASSETS["musica_ambiente"])
            pygame.mixer.music.play(-1)
        except pygame.error:
            print("Aviso: não foi possível carregar a música de ambiente.")

        try:
            self.som_click = pygame.mixer.Sound(ASSETS["som_click"])
        except pygame.error:
            self.som_click = None
            print("Aviso: não foi possível carregar o som de clique.")

    # =================================================================
    # ZOOM: abrir / fechar
    # =================================================================
    def abrir_zoom(self, modo):
        self.tela_ampliada_atual = modo
        if modo == "documento_objetivo":
            self.estado["documento_objetivo_lido"] = True
        elif modo == "documento_colunas":
            self.estado["documento_colunas_lido"] = True
        elif modo == "chatbot":
            self.chatbot_indice_mensagem = 0

    def fechar_zoom(self):
        self.tela_ampliada_atual = None

    # =================================================================
    # EVENTOS
    # =================================================================
    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False

            if self.tela_ampliada_atual is not None:
                self._processar_evento_zoom(evento)
                continue

            # Ícones de HUD (inventário, chatbot) continuam sendo
            # acionados normalmente com o mouse.
            if evento.type == pygame.MOUSEBUTTONDOWN:
                for obj in self.interativos:
                    if obj.get("tipo") != "hud":
                        continue
                    rect = obj["img"].get_rect(topleft=obj["pos"])
                    if rect.collidepoint(evento.pos):
                        if self.som_click:
                            self.som_click.play()
                        modo_zoom = TELAS_AMPLIADAS.get(obj["nome"])
                        if modo_zoom:
                            self.abrir_zoom(modo_zoom)
                        break

            # Objetos físicos do cenário: o jogador precisa andar até
            # perto do objeto e apertar "E" para interagir.
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_e:
                objeto_proximo = self._objeto_interativo_proximo()
                if objeto_proximo is not None:
                    if self.som_click:
                        self.som_click.play()
                    modo_zoom = TELAS_AMPLIADAS.get(objeto_proximo["nome"])
                    if modo_zoom:
                        self.abrir_zoom(modo_zoom)

    def _objeto_interativo_proximo(self):
        """Retorna o objeto do tipo 'mundo' mais próximo do jogador,
        desde que esteja dentro do raio de interação — ou None se
        nenhum objeto estiver ao alcance."""
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
        elif self.tela_ampliada_atual == "chatbot":
            self._clicar_chatbot(evento.pos)

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
                self.abrir_zoom("recompensa")

    def _clicar_gaveta(self, pos):
        # Gaveta ainda trancada: interagimos só com o cadeado.
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

        # Gaveta destrancada mas ainda fechada: qualquer clique fora do
        # botão de fechar já abre a gaveta.
        if not self.estado["gaveta_aberta"]:
            self.estado["gaveta_aberta"] = True
            self.gaveta_mensagem = "Gaveta aberta. Pegue os cartões perfurados."
            return

        # Gaveta aberta: clicar nos cartões coleta o item.
        if not self.estado["cartoes_coletados"] and self.gaveta_area_cartoes.collidepoint(pos):
            self.estado["cartoes_coletados"] = True
            self.gaveta_mensagem = "Cartões perfurados coletados! Já podem ser usados na máquina."
            self.maquina_mensagem = "Cartões prontos. Configure o painel e pressione Iniciar."

    def _clicar_chatbot(self, pos):
        if self.chatbot_botao_avancar.collidepoint(pos):
            if self.chatbot_indice_mensagem < len(CONVERSA_CHATBOT) - 1:
                self.chatbot_indice_mensagem += 1
            else:
                self.fechar_zoom()

    # =================================================================
    # ATUALIZAR
    # =================================================================
    def atualizar(self):
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
                    # Força o jogador a reconfigurar o painel
                    self.estado["painel_configurado"] = False
                    self.estado["tabulacao_concluida"] = False

        if self.tela_ampliada_atual is not None:
            return  # jogador não anda com o zoom aberto

        teclas = pygame.key.get_pressed()
        limites = self.tela.get_rect()
        self.jogador.mover(teclas, limites)

    # =================================================================
    # DESENHAR
    # =================================================================
    def desenhar(self):
        self.tela.blit(self.fundo, (0, 0))

        for img, pos in self.decoracao:
            self.tela.blit(img, pos)

        self.tela.blit(self.personagem_cenario, self.personagem_cenario_pos)

        for obj in self.interativos:
            if obj.get("desenhar", True):
                self.tela.blit(obj["img"], obj["pos"])

        # A gaveta em si é invisível (sua hitbox só marca a área de
        # interação); os cartões perfurados aparecem visualmente dentro
        # dela assim que é aberta, até serem coletados pelo jogador.
        if self.estado["gaveta_aberta"] and not self.estado["cartoes_coletados"]:
            self.tela.blit(self.img_cartoes_mundo, self.cartoes_mundo_pos)

        self.jogador.desenhar(self.tela)

        if self.tela_ampliada_atual is None:
            self._desenhar_dica_interacao()

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
            elif self.tela_ampliada_atual == "chatbot":
                self._desenhar_chatbot()
            elif self.tela_ampliada_atual == "recompensa":
                self._desenhar_recompensa()

        pygame.display.update()

    def _desenhar_dica_interacao(self):
        """Mostra um aviso 'Aperte E' acima do objeto do cenário mais
        próximo do jogador, quando ele estiver ao alcance."""
        objeto_proximo = self._objeto_interativo_proximo()
        if objeto_proximo is None:
            return

        rect = objeto_proximo["img"].get_rect(topleft=objeto_proximo["pos"])
        centro_x = rect.centerx
        topo_y = rect.top - 14

        texto = self.font_pequena.render("Aperte E", True, BRANCO)
        largura_balao = texto.get_width() + 20
        balao = pygame.Rect(0, 0, largura_balao, 26)
        balao.center = (centro_x, max(topo_y, 20))

        overlay = pygame.Surface(balao.size, pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 190))
        self.tela.blit(overlay, balao.topleft)
        pygame.draw.rect(self.tela, BRANCO, balao, width=1, border_radius=6)
        self.tela.blit(texto, texto.get_rect(center=balao.center))

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
            # Cadeado com 2 discos
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
            pygame.draw.rect(self.tela, (90, 70, 40), self.gaveta_area_cartoes, border_radius=6)
            pygame.draw.rect(self.tela, BRANCO, self.gaveta_area_cartoes, width=2, border_radius=6)
            texto_cartoes = self.font_texto.render("Cartões (clique para pegar)", True, BRANCO)
            self.tela.blit(texto_cartoes, texto_cartoes.get_rect(center=self.gaveta_area_cartoes.center))

        for i, linha in enumerate(quebrar_texto(self.gaveta_mensagem, self.font_pequena, self.zoom_rect.width - 80)):
            msg = self.font_pequena.render(linha, True, BRANCO)
            self.tela.blit(msg, (self.zoom_rect.left + 40, self.zoom_rect.bottom - 40 + i * 20))

    def _desenhar_chatbot(self):
        self.tela.blit(self.img_chatbot_fundo, self.zoom_rect)

        titulo = self.font_titulo.render("Chatbot", True, BRANCO)
        self.tela.blit(titulo, (self.zoom_rect.left + 40, self.zoom_rect.top + 30))

        autor, texto = CONVERSA_CHATBOT[self.chatbot_indice_mensagem]
        caixa_texto = pygame.Rect(
            self.zoom_rect.left + 30, self.zoom_rect.top + 90, self.zoom_rect.width - 60, 260
        )
        pygame.draw.rect(self.tela, (40, 40, 40), caixa_texto, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, caixa_texto, width=1, border_radius=10)

        y = caixa_texto.top + 16
        for linha in quebrar_texto(texto, self.font_texto, caixa_texto.width - 30):
            render = self.font_texto.render(linha, True, BRANCO)
            self.tela.blit(render, (caixa_texto.left + 15, y))
            y += 28

        contador = self.font_pequena.render(
            f"{self.chatbot_indice_mensagem + 1}/{len(CONVERSA_CHATBOT)}", True, BRANCO
        )
        self.tela.blit(contador, (self.zoom_rect.left + 40, self.chatbot_botao_avancar.top + 10))

        pygame.draw.rect(self.tela, AZUL, self.chatbot_botao_avancar, border_radius=6)
        ultima = self.chatbot_indice_mensagem == len(CONVERSA_CHATBOT) - 1
        texto_botao = self.font_texto.render("Fechar" if ultima else "Avançar", True, BRANCO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.chatbot_botao_avancar.center))

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

    # =================================================================
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