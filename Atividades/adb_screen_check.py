import subprocess


def list_devices():
    try:
        resultado = subprocess.run(
            ["adb", "devices", "-l"],
            capture_output=True,
            text=True,
            check=True,
        )

        texto = resultado.stdout.strip()

        if not texto or "List of devices attached" not in texto:
            print("Nenhum dispositivo encontrado.")
            return

        print(texto)

    except FileNotFoundError:
        print("ADB não encontrado no PATH.")
    except subprocess.CalledProcessError:
        print("Erro ao executar o ADB.")


def screen_is_on(device_ip):
    resultado = subprocess.run(
        ["adb", "-s", device_ip, "shell", "dumpsys", "power"],
        capture_output=True,
        text=True,
    )

    saida = resultado.stdout.lower()

    if "mWakefulness=awake" in saida or "display power: state=on" in saida:
        print("Tela ligada.")
        return True

    print("Tela desligada. Ligando...")
    subprocess.run(
        ["adb", "-s", device_ip, "shell", "input", "keyevent", "26"],
        capture_output=True,
        text=True,
    )

    return False


# Exemplo de uso
if __name__ == "__main__":
    list_devices()
    screen_is_on("SEU_IP_OU_SERIAL")
