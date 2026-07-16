"""
=====================================================================
audio_fase5.py -- música de fundo da Fase 5, no mesmo espírito de
audio_fase2.py (Pygame/Fase_2/fase2/audio_fase2.py): nomes de arquivo e
volumes organizados num lugar só, em vez de espalhados pelo resto do
código de fase_5.py.

Se o arquivo de música não existir ou o mixer não estiver disponível
(ex: máquina sem placa de som), iniciar_musica_fundo() simplesmente NÃO
toca nada -- nunca levanta exceção pro resto do jogo (mesmo espírito
defensivo de audio_fase2.py e de fase_5.py._parar_audio_seguro()).

Diferença em relação a audio_fase2.py: esta fase (por enquanto) não tem
efeitos sonoros próprios, só música de fundo -- por isso não há canais
dedicados (CANAL_CLIQUE_ID/CANAL_VITORIA_ID) nem carregar_som() aqui.
Se algum dia esta fase ganhar efeitos sonoros, é só copiar esse
pedaço de audio_fase2.py pra cá.
=====================================================================
"""

import os

import pygame

# Mesma pasta assets/ que fase_5.ASSETS/caminho_asset() já usa (a pasta
# "assets" ao lado deste arquivo) -- recalculada aqui, não importada de
# fase_5.py, pra este módulo não criar uma dependência nova (mesmo
# espírito autocontido de audio_fase2.py).
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _caminho_som(nome_arquivo):
    return os.path.join(ASSETS_DIR, nome_arquivo)


# ---------------------------------------------------------------------------
# ARQUIVO E VOLUME -- troque o nome do arquivo aqui por qualquer música que
# preferir (basta colocar o .mp3/.ogg escolhido em Fase_5/assets/).
# ---------------------------------------------------------------------------
SOM_MUSICA_FUNDO = _caminho_som("musica_fase5.mp3")

VOLUME_MUSICA_FUNDO = 0.06  # ~6% -- mesmo valor usado nas Fases 2 e 9, pra música de fundo não competir/cansar

# Volume GERAL (0.0 a 1.0) -- multiplicador aplicado por CIMA de
# VOLUME_MUSICA_FUNDO, ajustado pelo painel de configurações (ver
# config_fase5.abrir_painel_config()). 1.0 = volume original de cima,
# sem nenhuma redução extra. Mesmo espírito de
# audio_fase2.fator_volume_geral.
fator_volume_geral = 1.0


def definir_volume_geral(novo_fator):
    """Define o volume GERAL (0.0 a 1.0, sempre travado nesse
    intervalo) e reaplica NA HORA sobre a música que já estiver
    tocando -- chamado pelo painel de configurações (config_fase5.py)
    quando o jogador ajusta o volume, pra a mudança valer em tempo
    real."""
    global fator_volume_geral
    fator_volume_geral = max(0.0, min(1.0, novo_fator))
    try:
        pygame.mixer.music.set_volume(VOLUME_MUSICA_FUNDO * fator_volume_geral)
    except pygame.error:
        pass


def iniciar_musica_fundo():
    """Toca SOM_MUSICA_FUNDO em loop contínuo (loops=-1), como música de
    fundo da fase inteira -- não faz nada se o arquivo não existir ou o
    mixer não estiver disponível."""
    if not (SOM_MUSICA_FUNDO and os.path.isfile(SOM_MUSICA_FUNDO)):
        return
    try:
        pygame.mixer.music.load(SOM_MUSICA_FUNDO)
        pygame.mixer.music.set_volume(VOLUME_MUSICA_FUNDO * fator_volume_geral)
        pygame.mixer.music.play(loops=-1)
    except pygame.error:
        pass


def parar_tudo():
    """Para a música de fundo -- chamado ao sair da Fase 5 por qualquer
    caminho (vitória, derrota, ESC, fechar, voltar pro menu pelo painel
    de configurações), pra nada dela continuar tocando depois que a
    fase termina. Mesmo nome/papel de audio_fase2.parar_tudo(), pra
    quem já conhece o padrão da Fase 2 reconhecer de cara."""
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass
