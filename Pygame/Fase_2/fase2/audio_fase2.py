"""
=====================================================================
audio_fase2.py -- música de fundo + efeitos sonoros da Fase 2,
compartilhados entre fase2.py e puzzles/babbage_lovelace.py, pra
manter os nomes de arquivo e os volumes organizados num lugar só (em
vez de espalhar caminhos/volumes soltos pelos dois arquivos).

Se algum arquivo de som não existir ou o mixer não estiver disponível
(ex: máquina sem placa de som), as funções aqui simplesmente NÃO tocam
nada -- nunca levantam exceção pro resto do jogo, pra áudio nunca
travar a fase (ver o try/except em cada função).
=====================================================================
"""

import os

import pygame

# Mesma pasta assets/ que fase2.ASSETS_DIR e puzzles/common.ASSETS_DIR já
# usam (Pygame/Fase_2/fase2/assets/) -- recalculada aqui (em vez de
# importada de um dos dois) pra este módulo não criar uma dependência
# nova entre fase2.py e puzzles/common.py.
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _caminho_som(nome_arquivo):
    return os.path.join(ASSETS_DIR, nome_arquivo)


# ---------------------------------------------------------------------------
# ARQUIVOS E VOLUMES -- ajuste aqui (nomes de arquivo e volumes num lugar só)
# ---------------------------------------------------------------------------
SOM_MUSICA_FUNDO = _caminho_som("msc_fase2.mp3")
SOM_CAIXA = _caminho_som("caixa.mp3")
SOM_COLETAR_ENGRENAGEM = _caminho_som("coletar_engrenagem.mp3")
SOM_CONSERTANDO_MAQUINA = _caminho_som("consetando_maq.mp3")
SOM_ERRO = _caminho_som("error.mp3")
SOM_MAQUINA_LIGANDO = _caminho_som("maq_lig.mp3")

VOLUME_MUSICA_FUNDO = 0.45  # ~45% -- mais baixo que os efeitos, música de fundo não deve competir/cansar
VOLUME_EFEITOS = 0.7        # um pouco mais alto que a música, pra os efeitos serem bem ouvidos

# Canais dedicados (pygame.mixer.Channel) -- número do canal só, ajuste
# aqui se precisar. CANAL_CLIQUE é reservado só pros efeitos de reação a
# um clique do jogador (caixa, engrenagem, acerto/erro de carta): tocar
# nele SEMPRE para o que já estava tocando ali antes (ver
# tocar_efeito_clique), então cliques rápidos nunca empilham o som um
# por cima do outro. CANAL_VITORIA é reservado só pro som de vitória
# (máquina ligando), separado dos outros, pra dar pra parar ele
# especificamente quando a cena muda (ver parar_vitoria) sem mexer nos
# outros efeitos.
CANAL_CLIQUE_ID = 1
CANAL_VITORIA_ID = 2


def carregar_som(caminho, volume=VOLUME_EFEITOS):
    """Carrega um efeito sonoro (pygame.mixer.Sound) já no volume
    informado -- devolve None se o arquivo não existir ou não puder ser
    carregado (sem placa de som, mixer não inicializado etc.), pra quem
    chama simplesmente não tocar nada em vez de travar o jogo (mesmo
    espírito das funções de carregamento de imagem/fonte já usadas nesta
    fase, que também devolvem algo "vazio" quando o asset falta)."""
    if not (caminho and os.path.isfile(caminho)):
        return None
    try:
        som = pygame.mixer.Sound(caminho)
        som.set_volume(volume)
        return som
    except pygame.error:
        return None


def _tocar_em_canal(canal_id, som):
    """Toca `som` no canal `canal_id`, parando primeiro qualquer coisa
    que já estivesse tocando nesse MESMO canal -- é isso que garante que
    um clique novo nunca soe por cima do efeito do clique anterior."""
    if som is None:
        return
    try:
        canal = pygame.mixer.Channel(canal_id)
        canal.stop()
        canal.play(som)
    except pygame.error:
        pass


def tocar_efeito_clique(som):
    """Toca um efeito de REAÇÃO A CLIQUE (abrir caixa/baú/pote, coletar
    engrenagem, acertar/errar uma carta) no canal dedicado
    CANAL_CLIQUE_ID -- um clique novo sempre para o efeito do clique
    anterior antes de tocar o novo, pra nunca soar um por cima do
    outro."""
    _tocar_em_canal(CANAL_CLIQUE_ID, som)


def tocar_vitoria(som):
    """Toca o som de vitória (máquina ligando) no canal dedicado
    CANAL_VITORIA_ID, separado dos efeitos de clique -- ver
    parar_vitoria() pra como ele é interrompido quando a cena muda."""
    _tocar_em_canal(CANAL_VITORIA_ID, som)


def parar_vitoria():
    """Para o som de vitória (maq_lig.mp3), se ainda estiver tocando --
    chamado assim que a etapa de vitória do puzzle termina, pra ele
    nunca vazar pra próxima cena (fade/sala da máquina do tempo)."""
    try:
        pygame.mixer.Channel(CANAL_VITORIA_ID).stop()
    except pygame.error:
        pass


def parar_tudo():
    """Para a música de fundo E todos os efeitos (todos os canais) de
    uma vez -- chamado ao sair da Fase 2 por qualquer caminho (vitória,
    ESC, fechar, voltar pro menu), pra nada dela continuar tocando
    depois que a fase termina."""
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass
    try:
        pygame.mixer.stop()
    except pygame.error:
        pass


def iniciar_musica_fundo():
    """Toca SOM_MUSICA_FUNDO em loop contínuo (loops=-1), como música de
    fundo da fase inteira (oficina + puzzle) -- não faz nada se o
    arquivo não existir ou o mixer não estiver disponível."""
    if not (SOM_MUSICA_FUNDO and os.path.isfile(SOM_MUSICA_FUNDO)):
        return
    try:
        pygame.mixer.music.load(SOM_MUSICA_FUNDO)
        pygame.mixer.music.set_volume(VOLUME_MUSICA_FUNDO)
        pygame.mixer.music.play(loops=-1)
    except pygame.error:
        pass
