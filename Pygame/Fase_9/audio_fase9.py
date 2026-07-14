"""
=====================================================================
audio_fase9.py -- música de fundo + efeitos sonoros da Fase 9,
compartilhados entre fase9.py e puzzle_terminal.py, pra manter os
nomes de arquivo e os volumes organizados num lugar só (mesmo espírito
de estilo_crt.py, que já centraliza a paleta de cores visual desta
fase, em vez de espalhar valores soltos pelos dois arquivos).

Se algum arquivo de som não existir ou o mixer não estiver disponível
(ex: máquina sem placa de som, ou os testes automatizados que rodam
esta fase sem dispositivo de áudio), as funções aqui simplesmente NÃO
tocam nada -- nunca levantam exceção pro resto do jogo, pra áudio
nunca travar a fase (ver o try/except em cada função).
=====================================================================
"""

import os

import pygame

PASTA_ASSETS_SONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sons")


def _caminho_som(nome_arquivo):
    return os.path.join(PASTA_ASSETS_SONS, nome_arquivo)


# ---------------------------------------------------------------------------
# ARQUIVOS E VOLUMES -- ajuste aqui (nomes de arquivo e volumes num lugar só)
# ---------------------------------------------------------------------------
SOM_MUSICA_FUNDO = _caminho_som("musica.mp3")
SOM_CLIQUE = _caminho_som("clique.mp3")
SOM_SUCESSO = _caminho_som("sucesso.mp3")
SOM_ERRO = _caminho_som("erro.mp3")
SOM_COMPUTADOR_LIGANDO = _caminho_som("comp_ligando.mp3")

VOLUME_MUSICA_FUNDO = 0.06  # ~6% -- bem mais baixa que os efeitos, música de fundo não deve competir/cansar
VOLUME_EFEITOS = 0.7        # um pouco mais alto que a música, pra os efeitos serem bem ouvidos

# Volume GERAL (0.0 a 1.0) -- multiplicador aplicado por CIMA de
# VOLUME_MUSICA_FUNDO/VOLUME_EFEITOS, ajustado pelo painel de
# configurações (ver config_fase9.abrir_painel_config()). 1.0 = volumes
# originais de cima, sem nenhuma redução extra.
fator_volume_geral = 1.0

# Todo som carregado por carregar_som() entra aqui como (Sound,
# volume_base) -- é o que permite reaplicar o volume de CADA som já
# carregado quando o fator_volume_geral mudar (ver definir_volume_geral()),
# em vez de só valer pros próximos sons a carregar.
_sons_registrados = []


def carregar_som(caminho, volume=VOLUME_EFEITOS):
    """Carrega um efeito sonoro (pygame.mixer.Sound) já no volume
    informado (multiplicado pelo fator_volume_geral atual) -- devolve
    None se o arquivo não existir ou não puder ser carregado (sem placa
    de som, mixer não inicializado etc.), pra quem chama simplesmente
    não tocar nada em vez de travar o jogo (mesmo espírito de
    fase9.carregar_imagem/carregar_fonte, que também devolvem None
    quando o asset ainda não existe)."""
    if not (caminho and os.path.isfile(caminho)):
        return None
    try:
        som = pygame.mixer.Sound(caminho)
        som.set_volume(volume * fator_volume_geral)
        _sons_registrados.append((som, volume))
        return som
    except pygame.error:
        return None


def definir_volume_geral(novo_fator):
    """Define o volume GERAL (0.0 a 1.0, sempre travado nesse
    intervalo), aplicado de uma vez sobre a música de fundo E todos os
    efeitos já carregados -- chamado pelo painel de configurações
    (config_fase9.py) quando o jogador ajusta o volume. Reaplica NA HORA
    em cada som já carregado (não só nos próximos), pra a mudança valer
    em tempo real."""
    global fator_volume_geral
    fator_volume_geral = max(0.0, min(1.0, novo_fator))
    try:
        pygame.mixer.music.set_volume(VOLUME_MUSICA_FUNDO * fator_volume_geral)
    except pygame.error:
        pass
    for som, volume_base in _sons_registrados:
        try:
            som.set_volume(volume_base * fator_volume_geral)
        except pygame.error:
            pass


def tocar_som(som):
    """Toca um efeito já carregado (ver carregar_som) -- não faz nada se
    `som` for None (não carregou) ou se o mixer falhar na hora de tocar."""
    if som is None:
        return
    try:
        som.play()
    except pygame.error:
        pass


def parar_tudo():
    """Para a música de fundo E todos os efeitos sonoros (todos os
    canais) de uma vez -- chamado ao escolher SAIR no painel de
    configurações, pra nada da Fase 9 continuar tocando depois que a
    fase termina (mesmo espírito de audio_fase2.parar_tudo, em
    Pygame/Fase_2/fase2/audio_fase2.py -- efeitos sonoros usam canais
    separados de pygame.mixer.music, então só parar a música não basta)."""
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
