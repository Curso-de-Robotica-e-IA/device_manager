import subprocess

resultado = subprocess.run(
    ["adb", "devices", "-l"], #capture_output=True é necessário para capturar stdout e stderr. Sem ele, as mensagens aparecem diretamente no terminal e não ficam disponíveis em resultado.stdout ou resultado.stderr.
    #'ADB': Executável do android | "Devices": Solicita a lista de dispositivos | "-1": mostra informações extras, como fabricante e modelo.
    capture_output=True,
    text=True,
    check=True,
)

    print(resultado.stdout)