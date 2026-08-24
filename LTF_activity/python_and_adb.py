from json import dumps
#import device_manager
import subprocess as sub
from time import sleep
dict_keyevent = {f"{k}":f"KEYCODE_{k}" for k in range(10)}
dict_keyevent["power"] = "KEYCODE_POWER";dict_keyevent["enter"] = "KEYCODE_ENTER" 
def update_conected_devices(d):
    res =sub.run(["adb","devices","-l"], capture_output=True, text=True)
    #print(res.stdout)
    #adb -s RQCRA00NL6D shell "getprop | grep manufacturer"
    #adb -s RQCRA00NL6D shell getprop ro.serialno
    devices = {line[:line.index("device")].strip(): 
               dict({"Status":line[line.index("device"):line.index(" product")],
                     "ID":line[:line.index("device")].strip()},
                    **{duos[:duos.index(":")]:duos[duos.index(":")+1:] 
                        for duos in line[line.index("product"):].split(" ") if ":" in duos}) 
                            for line in res.stdout.split("\n") if 
                                all(x in line for x in ["product","model","device"])}
    values_dict = {"[ro.product.manufacturer]":"manufacturer",
         "[ro.build.version.release]":"android ver",
         "[ro.serialno]":"serialno_",
         "[ro.product.name]":"Name"}
    vd_names = {"[ro.config.lgsi.market_name]":"market_name"}
    ["adb","shell","wm","size"]
    for device in devices.keys():
        output = sub.run(["adb","-s",device,"shell","wm","size"], capture_output=True, text=True).stdout
        x,y = (int(output[output.index(":")+1:output.index("x")]),int(output[output.index("x")+1:]))
        devices[device]["display"] = (x,y)
        output = sub.run(["adb","-s",device,"shell","wm","density"], capture_output=True, text=True).stdout
        den = int(output[output.index(":")+1:])
        devices[device]["density"] = den
        for k,v in values_dict.items():
            output = sub.run(["adb","-s",device,"shell",f"getprop {k[1:-1]}"], capture_output=True, text=True)
            devices[device][v] = output.stdout.strip()
        for k in vd_names.keys():
            output = sub.run(["adb","-s",device,"shell",f"getprop {k[1:-1]}"], capture_output=True, text=True)
            out = output.stdout.strip()
            if len(out)>0: devices[device]["Name"] = out
    return devices
def build_Comand(d):
    if isinstance(list):
        return d
    else:
        if "setings" in d:
            pass
def pair_device_wifi(ip,port,key):
    c = sub.run(["adb","pair",f"{ip}:{port}",key], capture_output=True, text=True)
    print(c.stdout)
    c = sub.run(["adb","connect",f"{ip}:{port}"], capture_output=True, text=True)
    print(c.stdout)
    #c = sub.Popen(["adb","pair",f"{ip}:{port}"],stdin=sub.PIPE,stdout=sub.PIPE, stderr=sub.PIPE,text=True)# stdin=PIPE, stderr=PIPE, text=True)
    #c.stdout.write(key)
    #c.stdout.flush()
    #print(c.stdout)
    #out,err = c.communicate(key)#c.communicate(input=key)
    #l=[out,err]
def enter_key(key,device,model = None):

    c = sub.run(["adb","-s",device,"shell","input","keyevent",dict_keyevent["enter"]], 
                capture_output=True, text=True)
    for k in list(str(key)):
        c = sub.run(["adb","-s",device,"shell","input","keyevent",dict_keyevent[k]], capture_output=True, text=True)
        sleep(0.5)
def listApps(device):
    c = sub.run(["adb","-s",device,"shell","cmd","package","list","packages"],capture_output=True, text=True)
    print(c.stdout)
print(__name__)
if __name__ == "__main__":
    
    pair_device_wifi("10.158.241.13","34459","168383")
    devices = update_conected_devices({})
    print(dumps(devices,indent=2))
    tablet = [d["ID"] for d in devices.values() if d["manufacturer"]=="LENOVO"][0]
    cell  = [d["ID"] for d in devices.values() if d["manufacturer"]=="samsung"][0]
    i_display = sub.run(["adb","-s",tablet,"shell","dumpsys","display"], capture_output=True, text=True)
    i_power = sub.run(["adb","-s",tablet,"shell","dumpsys","power "], capture_output=True, text=True)
    sl = [line for line in i_power.stdout.split("\n")+i_display.stdout.split("\n") 
          if any(x in line.lower() for x in  ["mscreenstate","mholding"])]
    if "mScreenState=ON".lower() not in i_display.stdout.lower():
        c = sub.run(["adb","-s",tablet,"shell","input","keyevent",dict_keyevent["power"]], capture_output=True, text=True)
        print(c.stdout)
    #enter_key(secret,device)
    print(listApps(cell))
    print(dumps(sl,indent=1))

