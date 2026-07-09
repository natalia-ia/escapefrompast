import pygame
import sys

pygame.init()

LARGURA, ALTURA = 960, 600
CINZA = (150, 150, 150)

ASSETS = {
    # Cenário
    "fundo": "assets/cenario/cenario_fase3.png",

    # Decoração
    "corpo_personagem": "assets/decoracao/corpo do personagem.png",
    "mesa": "assets/decoracao/mesa.png",

    # Objetos interativos
    "caixa_cartoes": "assets/interativos/caixa_cartoes.png",
    "cartoes": "assets/interativos/cartoes.png",
    "chat": "assets/interativos/chat.png",
    "documento_codigo": "assets/interativos/documento_codigo.png",
    "fita": "assets/interativos/fita.png",
    "icone_chatbot": "assets/interativos/icone_chatbot.png",
    "icone_inventario": "assets/interativos/icone_inventario.png",
    "maquina_tabulacao": "assets/interativos/maquina_tabulacao.png",
    "painel_config": "assets/interativos/painel_config.png",

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

        self.fundo = carregar_imagem(ASSETS["fundo"], (LARGURA, ALTURA), label="sala")

        # ---------------------------------------------------------------
        # DECORAÇÃO (itens fixos, não clicáveis)
        # Formato de cada item: (imagem, (x, y))
        # ---------------------------------------------------------------
        #self.decoracao = [
        #    (carregar_imagem(ASSETS["mesa"], (100, 100), CINZA, "mesa"), (100, 120)),
        #]

        # Personagem estático de cenário: não se move, é só decoração.
        # Usa o MESMO tamanho da caixa do personagem jogável (138x288)
        # para ficar com a mesma escala na cena. Posicionado ao lado da
        # estante, sem sobrepor.
        self.personagem_cenario = carregar_imagem(
            ASSETS["corpo_personagem"], (340, 330), CINZA, "personagem cenario"
        )
        self.personagem_cenario_pos = (550, 250)

        # ---------------------------------------------------------------
        # OBJETOS INTERATIVOS (clicáveis)
        # ---------------------------------------------------------------
        self.interativos = [
            {
                "img": carregar_imagem(ASSETS["maquina_tabulacao"], (300, 300), CINZA, "maquina tabulacao"),
                "pos": (0, 280),
                "nome": "maquina tabulacao",
                "desenhar": True,
            },
            {
                "img": carregar_imagem(ASSETS["caixa_cartoes"], (100, 180), CINZA, "caixa de cartoes"),
                "pos": (380, 250),
                "nome": "caixa de cartoes",
                "desenhar": True,
            },
            {
                "img": carregar_imagem(ASSETS["icone_inventario"], (100, 100), CINZA, "inventario"),
                "pos": (LARGURA - 140, ALTURA - 80),
                "nome": "inventario",
                "desenhar": True,
            },
            {
                "img": carregar_imagem(ASSETS["icone_chatbot"], (60, 60), CINZA, "chatbot"),
                "pos": (LARGURA - 70, ALTURA - 80),
                "nome": "chatbot",
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

    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False
            if evento.type == pygame.MOUSEBUTTONDOWN:
                for obj in self.interativos:
                    rect = obj["img"].get_rect(topleft=obj["pos"])
                    if rect.collidepoint(evento.pos):
                        if self.som_click:
                            self.som_click.play()
                        print(f"Clicou em: {obj['nome']}")

    def atualizar(self):
        teclas = pygame.key.get_pressed()
        limites = self.tela.get_rect()
        self.jogador.mover(teclas, limites)

    def desenhar(self):
        self.tela.blit(self.fundo, (0, 0))

        #for img, pos in self.decoracao:
        #    self.tela.blit(img, pos)

        self.tela.blit(self.personagem_cenario, self.personagem_cenario_pos)

        for obj in self.interativos:
            if obj.get("desenhar", True):
                self.tela.blit(obj["img"], obj["pos"])

        self.jogador.desenhar(self.tela)
        pygame.display.update()

    def rodar(self):
        while self.rodando:
            self.processar_eventos()
            self.atualizar()
            self.desenhar()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    jogo = Jogo(personagem_escolhido=1)
    jogo.rodar()