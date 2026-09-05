"""
app.py
------
Interface gráfica (Tkinter) para escolher dispositivo de entrada, saída,
tamanho de buffer, sample rate e canais, e então iniciar/parar o motor
de áudio (engine.AudioEngine).

Pensado para ser compilado em um único .exe com PyInstaller, incluindo
o plugin VST3 como dado embutido. Veja o bloco de comentários no final
do arquivo com o comando de build sugerido.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

import pystray
from PIL import Image, ImageDraw

from engine import (
    AudioEngine,
    BUFFER_SIZE_OPTIONS,
    SAMPLE_RATE_OPTIONS,
    CHANNEL_OPTIONS,
    resource_path,
)
import config

# Caminho do ícone (.ico) usado na janela e na barra de tarefas.
# resource_path garante que funcione tanto rodando como .py quanto
# dentro do .exe compilado pelo PyInstaller.
ICON_PATH = resource_path("assets/icon.ico")


def create_tray_image(color: str):
    image = Image.new("RGB", (64, 64), color="black")
    d = ImageDraw.Draw(image)
    d.rectangle((16, 16, 48, 48), fill=color)
    return image


class CapyMicApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.engine = AudioEngine()
        self.tray_icon = None

        root.title("CapyMic - Configurações")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.on_close_window)
        self._set_window_icon()

        self.saved_settings = config.load_settings()

        self._build_ui()
        self._load_devices()
        self._apply_saved_settings()

    # ------------------------------------------------------------------ #
    # Ícone da janela
    # ------------------------------------------------------------------ #
    def _set_window_icon(self):
        """
        Troca o ícone padrão do Tkinter (a "folhinha") pelo ícone do app.
        iconbitmap espera um arquivo .ico e funciona de forma nativa no
        Windows (título da janela + barra de tarefas).
        """
        try:
            self.root.iconbitmap(ICON_PATH)
        except Exception:
            # Se o arquivo não existir ou o SO não suportar .ico
            # (ex.: Linux/Mac), simplesmente mantém o ícone padrão
            # em vez de travar o app.
            pass

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}
        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=0, sticky="nsew", **pad)

        ttk.Label(frame, text="Dispositivo de entrada (microfone):").grid(
            row=0, column=0, sticky="w"
        )
        self.input_device_var = tk.StringVar()
        self.input_combo = ttk.Combobox(
            frame, textvariable=self.input_device_var, state="readonly", width=45
        )
        self.input_combo.grid(row=1, column=0, columnspan=2, sticky="we", **pad)

        ttk.Label(frame, text="Dispositivo de saída (cabo virtual):").grid(
            row=2, column=0, sticky="w"
        )
        self.output_device_var = tk.StringVar()
        self.output_combo = ttk.Combobox(
            frame, textvariable=self.output_device_var, state="readonly", width=45
        )
        self.output_combo.grid(row=3, column=0, columnspan=2, sticky="we", **pad)

        # Buffer size
        ttk.Label(frame, text="Buffer:").grid(row=4, column=0, sticky="w")
        self.buffer_var = tk.IntVar(value=self.saved_settings.get("buffer_size", 512))
        self.buffer_combo = ttk.Combobox(
            frame,
            textvariable=self.buffer_var,
            values=BUFFER_SIZE_OPTIONS,
            state="readonly",
            width=10,
        )
        self.buffer_combo.grid(row=4, column=1, sticky="w", **pad)

        # Sample rate
        ttk.Label(frame, text="Sample rate:").grid(row=5, column=0, sticky="w")
        self.samplerate_var = tk.IntVar(value=self.saved_settings.get("sample_rate", 48000))
        self.samplerate_combo = ttk.Combobox(
            frame,
            textvariable=self.samplerate_var,
            values=SAMPLE_RATE_OPTIONS,
            state="readonly",
            width=10,
        )
        self.samplerate_combo.grid(row=5, column=1, sticky="w", **pad)

        # Channels
        ttk.Label(frame, text="Canais:").grid(row=6, column=0, sticky="w")
        self.channels_var = tk.IntVar(value=self.saved_settings.get("channels", 1))
        self.channels_combo = ttk.Combobox(
            frame,
            textvariable=self.channels_var,
            values=CHANNEL_OPTIONS,
            state="readonly",
            width=10,
        )
        self.channels_combo.grid(row=6, column=1, sticky="w", **pad)

        # Status
        self.status_var = tk.StringVar(value="Parado")
        ttk.Label(frame, text="Status:").grid(row=7, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.status_var).grid(
            row=7, column=1, sticky="w"
        )

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=(10, 0))

        self.start_button = ttk.Button(
            btn_frame, text="Iniciar", command=self.on_start
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(
            btn_frame, text="Parar", command=self.on_stop, state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=5)

        self.tray_button = ttk.Button(
            btn_frame, text="Minimizar p/ bandeja", command=self.minimize_to_tray
        )
        self.tray_button.grid(row=0, column=2, padx=5)

        ttk.Button(btn_frame, text="Recarregar dispositivos", command=self._load_devices).grid(
            row=1, column=0, columnspan=3, pady=(6, 0)
        )

    def _load_devices(self):
        try:
            inputs = AudioEngine.list_input_devices()
            outputs = AudioEngine.list_output_devices()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível listar dispositivos:\n{e}")
            return

        self.input_combo["values"] = inputs
        self.output_combo["values"] = outputs

        if inputs and not self.input_device_var.get():
            self.input_device_var.set(inputs[0])
        if outputs and not self.output_device_var.get():
            self.output_device_var.set(outputs[0])

    def _apply_saved_settings(self):
        """
        Se o dispositivo salvo anteriormente ainda existir na máquina,
        seleciona ele. Caso contrário, mantém o que já foi escolhido por
        padrão em _load_devices (ex.: primeiro da lista).
        """
        saved_input = self.saved_settings.get("input_device", "")
        saved_output = self.saved_settings.get("output_device", "")

        if saved_input and saved_input in self.input_combo["values"]:
            self.input_device_var.set(saved_input)

        if saved_output and saved_output in self.output_combo["values"]:
            self.output_device_var.set(saved_output)

    def _current_settings(self) -> dict:
        return {
            "input_device": self.input_device_var.get(),
            "output_device": self.output_device_var.get(),
            "buffer_size": int(self.buffer_var.get()),
            "sample_rate": int(self.samplerate_var.get()),
            "channels": int(self.channels_var.get()),
        }

    # ------------------------------------------------------------------ #
    # Ações
    # ------------------------------------------------------------------ #
    def on_start(self):
        input_device = self.input_device_var.get()
        output_device = self.output_device_var.get()

        if not input_device or not output_device:
            messagebox.showwarning("Atenção", "Selecione entrada e saída de áudio.")
            return

        def worker():
            try:
                self.engine.start(
                    input_device_name=input_device,
                    output_device_name=output_device,
                    buffer_size=int(self.buffer_var.get()),
                    num_input_channels=int(self.channels_var.get()),
                    num_output_channels=int(self.channels_var.get()),
                    sample_rate=int(self.samplerate_var.get()),
                )
                self.root.after(0, self._on_started_ok)
            except Exception as e:
                self.root.after(0, lambda: self._on_started_fail(e))

        self.status_var.set("Carregando plugin / abrindo stream...")
        self.start_button.config(state="disabled")
        threading.Thread(target=worker, daemon=True).start()

    def _on_started_ok(self):
        self.status_var.set("Rodando")
        self.stop_button.config(state="normal")
        config.save_settings(self._current_settings())

    def _on_started_fail(self, error):
        self.status_var.set("Erro")
        self.start_button.config(state="normal")
        messagebox.showerror("Erro ao iniciar", str(error))

    def on_stop(self):
        self.engine.stop()
        self.status_var.set("Parado")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    # ------------------------------------------------------------------ #
    # Bandeja do sistema
    # ------------------------------------------------------------------ #
    def minimize_to_tray(self):
        self.root.withdraw()  # esconde a janela

        color = "green" if self.engine.is_running() else "gray"
        image = create_tray_image(color)
        menu = pystray.Menu(
            pystray.MenuItem("Abrir configurações", self.restore_from_tray),
            pystray.MenuItem("Encerrar", self.quit_from_tray),
        )
        self.tray_icon = pystray.Icon("CapyMic", image, "CapyMic", menu)
        self.tray_icon.run_detached()

    def restore_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.after(0, self.root.deiconify)

    def quit_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.after(0, self._shutdown)

    def on_close_window(self):
        # Fechar a janela (X) também minimiza para a bandeja, em vez de
        # encerrar direto, para não perder o processamento em andamento.
        if self.engine.is_running():
            self.minimize_to_tray()
        else:
            self._shutdown()

    def _shutdown(self):
        config.save_settings(self._current_settings())
        self.engine.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    CapyMicApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------- #
# Como compilar em um único .exe (Windows), incluindo o plugin VST3 e os
# assets (ícone):
#
#   pyinstaller --onefile --windowed --name CapyMic ^
#       --icon "assets/icon.ico" ^
#       --add-data "PluginDeepFilter;PluginDeepFilter" ^
#       --add-data "assets;assets" ^
#       app.py
#
# Notas:
# - O "--add-data ORIGEM;DESTINO" usa ";" no Windows (no Linux/Mac seria ":").
# - "--icon assets/icon.ico" define o ícone do PRÓPRIO ARQUIVO .exe (o que
#   aparece no Explorer, atalhos, etc.).
# - "--add-data assets;assets" copia a pasta assets/ (incluindo icon.ico e
#   icon.png) para dentro do executável; em tempo de execução, é isso que
#   permite ao root.iconbitmap() trocar o ícone da JANELA em si — sem essa
#   linha, o app roda normalmente, mas mantém o ícone padrão do Tkinter.
# - Isso também copia toda a pasta PluginDeepFilter (incluindo o .vst3) para
#   dentro do executável; em tempo de execução, engine.resource_path() localiza
#   esses arquivos extraídos na pasta temporária do PyInstaller.
# - engine.py e config.py NÃO precisam ser incluídos manualmente: o
#   PyInstaller já rastreia os imports (import engine / import config)
#   automaticamente a partir de app.py.
# - Use --windowed para não abrir um console junto com a interface gráfica.
# ---------------------------------------------------------------------- #