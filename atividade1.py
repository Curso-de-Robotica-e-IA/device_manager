import subprocess
import time
######
#adb devices
#adb pair ip:port # na tela de pareamento

#depois disso vai pedir o pairing code

#adb connect ip:port #na tela de wireless debugging

print("mostrando dispositivos conectados")
#mostrando a lista de devices
subprocess.run(["adb", "devices"])

#conectando ao dispositivo via wi-fi
codigo_pareamento = input("Digite IP e porta disponíveis na tela de pareamento do dispositivo")
subprocess.run(["adb","pair",codigo_pareamento])


codigo_pareamento = input("Digite IP e porta disponíveis na tela do dispositivo")

subprocess.run(["adb","connect", codigo_pareamento])

nome_device = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout.split('\n')[1].split("\t")[0]

subprocess.run(["adb","devices"])

print("verificando se a tela esta ligada")
result = subprocess.run(['adb', '-s', nome_device, 'shell', 'dumpsys', 'display'],capture_output=True,text=True)
for line in result.stdout.splitlines():
    if 'mScreenState' in line:
        ligada=line.strip().split('=')[1]
if(not ligada=='ON'):
    print("a tela estava desligada, ligando...")
    subprocess.run(['adb', '-s', nome_device,'shell', 'input', 'keyevent', 'KEYCODE_WAKEUP'])

bloqueada = subprocess.run(['adb','-s',nome_device, 'shell','dumpsys','window'],capture_output=True,text=True)
for line in bloqueada.stdout.splitlines():
    if 'mDreamingLockscreen' in line:
        linha = line.strip().split(' ')
        bloqueada = linha[1].split("=")[1]
        if(not bloqueada=='false'):
            print("a tela esta bloqueada, desbloqueando...")
            subprocess.run(['adb', '-s', nome_device, 'shell','input','swipe','300','1400','300','400'])#SIMULANDO O DESLIZE DE DEDO NA TELA NO SENTIDO DE DESBLOQUEIO

serial =subprocess.run(['adb','-s',nome_device,'shell','getprop', 'ro.serialno'],capture_output=True,text=True).stdout
fabricante = subprocess.run(['adb','-s',nome_device,'shell','getprop', 'ro.product.manufacturer'],capture_output=True,text=True).stdout
modelo = subprocess.run(['adb','-s',nome_device,'shell','getprop', 'ro.product.model'],capture_output=True,text=True).stdout
android = subprocess.run(['adb','-s',nome_device,'shell','getprop', 'ro.build.version.release'],capture_output=True,text=True).stdout

print(f'serial number:{serial} \n fabricante: {fabricante} \n Modelo: {modelo} \n Versão do android: {android}')

dimensoes = subprocess.run(['adb','-s',nome_device,'shell','wm','size'], capture_output=True,text=True).stdout.strip().split(":")[1]
print(f'dimensoes da tela{dimensoes}')

apps = subprocess.run(['adb','-s',nome_device,'shell','pm', 'list','packages'],capture_output=True,text=True).stdout
print(f'aplicativos: {apps}')

atividade_atual = subprocess.run(['adb','-s',nome_device,'shell','dumpsys','window'],capture_output=True,text=True)
for line in atividade_atual.stdout.splitlines():
    if 'mCurrentFocus' in line:
        print(line)
        #essa linha é a activity atual

#abrindo o aplicativo da camera
subprocess.run(['adb','-s',nome_device,'shell','am','start','-n','com.android.camera/com.android.camera.Camera'])
#adb shell am start -n com.mi.android.globallauncher/com.miui.home.launcher.Launcher


time.sleep(2)
subprocess.run(['adb','-s',nome_device,'shell','am','start','-n','com.mi.android.globallauncher/com.miui.home.launcher.Launcher'])



stay_on = subprocess.run(['adb','-s',nome_device,'shell','settings','get','global','stay_on_while_plugged_in'], capture_output=True,text=True).stdout
time.sleep(1)
if( not stay_on.strip()=="7"):
    subprocess.run(['adb','-s',nome_device,'shell','settings','put','global','stay_on_while_plugged_in','7'])

#verificando se o modo avião esta ligado
subprocess.run(['adb','-s',nome_device,'shell','settings','put','global','stay_on_while_plugged_in','7'])

#verificando se o modo avião esta ligado
airplane_mode = subprocess.run(['adb','-s',nome_device,'shell','settings','get','global','airplane_mode_on'], capture_output=True,text=True).stdout.strip()
if(airplane_mode=='1'):
    print("o modo avião esta ligado")
else:
    print("o modo avião esta desligado")

subprocess.run(['adb','-s',nome_device, 'shell', 'input', 'tap', '520' ,'1200'])



# PS C:\Users\ysm> adb shell input tap 540 0
# PS C:\Users\ysm> adb shell input tap 540 2300

subprocess.run(['adb','-s',nome_device,'shell','input','swipe','540','0','540','2300'])