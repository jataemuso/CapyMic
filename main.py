import time
from pedalboard import Pedalboard, load_plugin
from pedalboard.io import AudioStream

def main():
    MIC_NAME = "Microphone (Realtek(R) Audio)"

    #Virutal Audio Cable
    CABLE_NAME = "CABLE Input (VB-Audio Virtual Cable)"

    #voicemetter
    # CABLE_NAME = "Voicemeeter Input (VB-Audio Voicemeeter VAIO)"

    # 2. Carrega a inteligência artificial (VST)
    try:
        print("Carregando modelo do DeepFilterNet...")
        # Aponta diretamente para a versão VST3 extraída
        plugin = load_plugin("./PluginDeepFilter/DeepFilterNet-v2026.4.2.1-windows/VST3/DeepFilterNet.vst3/Contents/x86_64-win/DeepFilterNet.vst3")
        board = Pedalboard([plugin])
    except Exception as e:
        print(f"Erro ao carregar a DLL: {e}")
        return

   # 3. Inicia o stream de áudio em tempo real
    try:
        # Forçamos 48kHz (exigência do DeepFilterNet) e 1 canal tanto na entrada quanto na saída
        with AudioStream(
            input_device_name=MIC_NAME,
            output_device_name=CABLE_NAME,
            buffer_size=512, #512, 256 ou 128
            num_input_channels=1,
            num_output_channels=1,
            sample_rate=48000 
        ) as stream:
            
            stream.plugins = board
            
            print(f"\n[SUCESSO] Roteamento Ativo (Modo Mono / 48kHz)!")
            print(f"🎤 Entrada física: {MIC_NAME}")
            print(f"🎧 Saída virtual: {CABLE_NAME}")
            print("\nProcessando áudio em tempo real... (Pressione Ctrl+C para encerrar)")
            
            # Mantém o script rodando
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n[ENCERRADO] Processamento finalizado pelo usuário.")
    except Exception as e:
        print(f"\n[ERRO] Falha no stream de áudio: {e}")
        print("Dica: Verifique se os nomes dos dispositivos coincidem com o comando `python -m sounddevice`.")

if __name__ == "__main__":
    main()