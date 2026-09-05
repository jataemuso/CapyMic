import time

import pystray
from PIL import Image, ImageDraw

from engine import AudioEngine

running = True


def create_image():
    # Desenha um pequeno quadrado verde para o ícone
    image = Image.new('RGB', (64, 64), color='black')
    d = ImageDraw.Draw(image)
    d.rectangle((16, 16, 48, 48), fill='green')
    return image


def on_quit(icon, item):
    global running
    running = False  # Avisa o loop do áudio para parar
    icon.stop()      # Remove o ícone da bandeja


def main():
    global running

    MIC_NAME = "Microphone (Realtek(R) Audio)"
    # Descomente a linha do Voicemeeter se for usar ele
    CABLE_NAME = "CABLE Input (VB-Audio Virtual Cable)"
    # CABLE_NAME = "Voicemeeter Input (VB-Audio Voicemeeter VAIO)"

    # 1. Cria o ícone na bandeja em modo "Desanexado" (não trava o áudio)
    image = create_image()
    menu = pystray.Menu(pystray.MenuItem('Encerrar DeepFilter', on_quit))
    icon = pystray.Icon("DeepFilter", image, "Filtro Ativo", menu)
    icon.run_detached()

    # 2. Cria o motor de áudio e carrega o plugin
    engine = AudioEngine()
    try:
        engine.load_plugin()
    except Exception:
        icon.stop()
        return

    # 3. Inicia o stream de áudio na thread principal (desempenho máximo)
    try:
        engine.start(
            input_device_name=MIC_NAME,
            output_device_name=CABLE_NAME,
            buffer_size=512,
            num_input_channels=1,
            num_output_channels=1,
            sample_rate=48000,
        )

        # Mantém o script rodando limpo até você clicar em "Encerrar"
        while running:
            time.sleep(0.5)

    except Exception:
        pass
    finally:
        engine.stop()
        icon.stop()


if __name__ == "__main__":
    main()