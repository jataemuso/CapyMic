"""
config.py
---------
Salva e carrega as preferências do usuário (dispositivo de entrada/saída,
buffer, sample rate, canais) em um arquivo JSON dentro da pasta AppData
do Windows (ou HOME, em outros sistemas), para persistir entre execuções
do .exe.
"""

import json
import os

APP_FOLDER_NAME = "DeepFilterApp"
SETTINGS_FILE_NAME = "settings.json"

DEFAULT_SETTINGS = {
    "input_device": "",
    "output_device": "",
    "buffer_size": 512,
    "sample_rate": 48000,
    "channels": 1,
}


def get_config_dir() -> str:
    """
    Retorna a pasta de configuração do app:
    - Windows: %APPDATA%\\DeepFilterApp
    - Outros SOs: ~/.config/DeepFilterApp (fallback razoável)
    """
    appdata = os.environ.get("APPDATA")
    if appdata:
        base_dir = appdata
    else:
        base_dir = os.path.join(os.path.expanduser("~"), ".config")

    config_dir = os.path.join(base_dir, APP_FOLDER_NAME)
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_settings_path() -> str:
    return os.path.join(get_config_dir(), SETTINGS_FILE_NAME)


def load_settings() -> dict:
    """
    Carrega as preferências salvas. Se o arquivo não existir ou estiver
    corrompido, retorna os valores padrão (nunca lança exceção).
    """
    path = get_settings_path()
    settings = DEFAULT_SETTINGS.copy()

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                settings.update(saved)
        except (json.JSONDecodeError, OSError):
            pass  # arquivo corrompido ou ilegível: segue com os padrões

    return settings


def save_settings(settings: dict) -> None:
    """Salva as preferências no arquivo JSON. Falha silenciosamente."""
    path = get_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except OSError:
        pass
