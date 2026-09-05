import time
import pystray
from PIL import Image, ImageDraw
from pedalboard import Pedalboard, load_plugin
from pedalboard.io import AudioStream

# Variável para controlar quando fechar o programa
running = True

def create_image():
    # Desenha um pequeno quadrado verde para o ícone
    image = Image.new('RGB', (64, 64), color='black')
    d = ImageDraw.Draw(image)
    d.rectangle((16, 16, 48, 48), fill='green')
    return image

def on_quit(icon, item):
    global running
    running = False # Avisa o loop do áudio para parar
    icon.stop()     # Remove o ícone da bandeja

def main():
    global running
    
    MIC_NAME = "Microphone (Realtek(R) Audio)"
    # Descomente a linha do Voicemeeter se for usar ele
    CABLE_NAME = "CABLE Input (VB-Audio Virtual Cable)"
    # CABLE_NAME = "Voicemeeter Input (VB-Audio Voicemeeter VAIO)"

    # 1. Cria o ícone na bandeja em modo "Desanexado" (Não trava o áudio)
    image = create_image()
    menu = pystray.Menu(pystray.MenuItem('Encerrar DeepFilter', on_quit))
    icon = pystray.Icon("DeepFilter", image, "Filtro Ativo", menu)
    icon.run_detached() 

    # 2. Carrega a inteligência artificial (VST)
    try:
        plugin = load_plugin("./PluginDeepFilter/DeepFilterNet-v2026.4.2.1-windows/VST3/DeepFilterNet.vst3/Contents/x86_64-win/DeepFilterNet.vst3")
        board = Pedalboard([plugin])
    except Exception as e:
        icon.stop()
        return

    # 3. Inicia o stream de áudio na Thread Principal (Desempenho máximo)
    try:
        with AudioStream(
            input_device_name=MIC_NAME,
            output_device_name=CABLE_NAME,
            buffer_size=512,
            num_input_channels=1,
            num_output_channels=1,
            sample_rate=48000 
        ) as stream:
            
            stream.plugins = board
            
            # Mantém o script rodando limpo até você clicar em "Encerrar"
            while running:
                time.sleep(0.5)
                
    except Exception:
        pass

if __name__ == "__main__":
    main()