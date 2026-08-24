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
def tap_action(device,points:list):
    '''if all((isinstance(p,tuple) or isinstance(p,list)) for p in points):
        if all(len(p)==2 for p in points):
            pass
        elif all(3==len(p) for p in points[1:-1]):
            if (len(points[0]) == 2 and len(points[1]) == 3):
                pass
            elif (len(points[0]) == 3 and len(points[-1]) == 2):
                pass
    if all((isinstance(p,tuple) or isinstance(p,list) or 
            isinstance(p,int) or isinstance(p,float)) for p in points):
        if all(len(p)==2 for p in points):
            pass
        elif all(3==len(p) for p in points[1:-1]):
            if (len(points[0]) == 2 and len(points[1]) == 3):
                pass
            elif (len(points[0]) == 3 and len(points[-1]) == 2):
                pass
    elif all(isinstance(p,dict) for p in points):
            pass'''
    for swipe in points:
        x = swipe["X"]
        y = swipe["Y"]
        c = sub.run(["adb","-s",device,"shell","input","tap",
                     f"{x} {y}"
                     ],capture_output=True, text=True)
        print(c.stdout)
        pass
def swipe_action(device,points:list):
    '''if all((isinstance(p,tuple) or isinstance(p,list)) for p in points):
        if all(len(p)==2 for p in points):
            pass
        elif all(3==len(p) for p in points[1:-1]):
            if (len(points[0]) == 2 and len(points[1]) == 3):
                pass
            elif (len(points[0]) == 3 and len(points[-1]) == 2):
                pass
    if all((isinstance(p,tuple) or isinstance(p,list) or 
            isinstance(p,int) or isinstance(p,float)) for p in points):
        if all(len(p)==2 for p in points):
            pass
        elif all(3==len(p) for p in points[1:-1]):
            if (len(points[0]) == 2 and len(points[1]) == 3):
                pass
            elif (len(points[0]) == 3 and len(points[-1]) == 2):
                pass
    elif all(isinstance(p,dict) for p in points):
            pass'''
    for swipe in points:
        sx = swipe["SX"]
        sy = swipe["SY"]
        ex = swipe["EX"]
        ey = swipe["EY"]
        dur = swipe["duration"]
        c = sub.run(["adb","-s",device,"shell","input ","swipe ",
                     f"{sx} {sy} {ex} {ey} {dur}"
                     ],capture_output=True, text=True)
        print(c.stdout)
        pass
def home(device):
    pass#key_home
def current_activity(device):
    pass#adb shell "dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'"
def home(device):
    pass#[persist.radio.airplane_mode_on]:
    #adb shell settings put global airplane_mode_on 1  
    # adb shell settings put global airplane_mode_on 1
    # adb shell am broadcast -a android.intent.action.AIRPLANE_MODE
    # adb shell settings put global airplane_mode_on 0
    # adb shell am broadcast -a android.intent.action.AIRPLANE_MODE
def get_airplane_Mode(device):
    on =  int(sub.run(["adb","-s",device,"shell","settings","get","global","airplane_mode_on"],capture_output=True, text=True).stdout)
    return on == 1
print(__name__)
if __name__ == "__main__":
    
    #pair_device_wifi("10.158.241.13","34459","168383")
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
    #print(listApps(cell))
    print(dumps(sl,indent=1))
    print(tap_action(tablet,[{"X":500,"Y":840},{"X":1500,"Y":640}]))
    print(swipe_action(tablet,[{"SX":0,"SY":1840/2,"EX":2944,"EY":1840/2,"duration":1000}]))
    print(get_airplane_Mode(tablet),get_airplane_Mode(cell))

