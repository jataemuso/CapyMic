"""
engine.py
---------
Motor de processamento de áudio: carrega o plugin VST3 (DeepFilterNet)
e gerencia o AudioStream de entrada/saída. Não conhece interface gráfica
nem ícone de bandeja — apenas processa áudio.
"""

import os
import sys

from pedalboard import Pedalboard, load_plugin
from pedalboard.io import AudioStream


def resource_path(relative_path: str) -> str:
    """
    Resolve um caminho relativo tanto rodando como script (.py) quanto
    rodando como executável empacotado pelo PyInstaller (onefile).

    Quando compilado com PyInstaller, os arquivos incluídos via --add-data
    são extraídos para uma pasta temporária apontada por sys._MEIPASS.
    """
    try:
        base_path = sys._MEIPASS  # criado pelo PyInstaller em tempo de execução
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Caminho padrão do plugin, relativo à raiz do projeto (ou do .exe compilado)
DEFAULT_PLUGIN_PATH = resource_path(
    "PluginDeepFilter/DeepFilterNet-v2026.4.2.1-windows/VST3/"
    "DeepFilterNet.vst3/Contents/x86_64-win/DeepFilterNet.vst3"
)

# Opções comuns, úteis para popular combobox na interface
BUFFER_SIZE_OPTIONS = [64, 128, 256, 512, 1024, 2048]
SAMPLE_RATE_OPTIONS = [44100, 48000]
CHANNEL_OPTIONS = [1, 2]


class AudioEngine:
    """Encapsula o carregamento do plugin e o AudioStream do pedalboard."""

    def __init__(self, plugin_path: str = DEFAULT_PLUGIN_PATH):
        self.plugin_path = plugin_path
        self.board = None
        self.stream = None
        self._running = False

    # ------------------------------------------------------------------ #
    # Plugin
    # ------------------------------------------------------------------ #
    def load_plugin(self):
        """Carrega o VST3 e monta o Pedalboard. Lança exceção se falhar."""
        plugin = load_plugin(self.plugin_path)
        self.board = Pedalboard([plugin])
        return self.board

    # ------------------------------------------------------------------ #
    # Dispositivos
    # ------------------------------------------------------------------ #
    @staticmethod
    def list_input_devices():
        return list(AudioStream.input_device_names)

    @staticmethod
    def list_output_devices():
        return list(AudioStream.output_device_names)

    # ------------------------------------------------------------------ #
    # Stream
    # ------------------------------------------------------------------ #
    def start(
        self,
        input_device_name: str,
        output_device_name: str,
        buffer_size: int = 512,
        num_input_channels: int = 1,
        num_output_channels: int = 1,
        sample_rate: int = 48000,
    ):
        """Carrega o plugin (se necessário) e abre o AudioStream."""
        if self.board is None:
            self.load_plugin()

        self.stream = AudioStream(
            input_device_name=input_device_name,
            output_device_name=output_device_name,
            buffer_size=buffer_size,
            num_input_channels=num_input_channels,
            num_output_channels=num_output_channels,
            sample_rate=sample_rate,
        )
        # Abre o stream manualmente (equivalente ao "with AudioStream(...) as stream")
        self.stream.__enter__()
        self.stream.plugins = self.board
        self._running = True

    def stop(self):
        """Fecha o stream de áudio, se estiver aberto."""
        self._running = False
        if self.stream is not None:
            try:
                self.stream.__exit__(None, None, None)
            except Exception:
                pass
            finally:
                self.stream = None

    def is_running(self) -> bool:
        return self._running
