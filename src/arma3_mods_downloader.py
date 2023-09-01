from typing import Tuple, List
import subprocess
import sys
import os
import shutil
import re


APP_ID = "107410"
STEAMCMD_PATH = "steamcmd"
WORKSHOP_PATH=f"{os.environ['HOME']}/Steam/steamapps/workshop/content/{APP_ID}"
ARMA_PATH=f"{os.environ['HOME']}/Steam/steamapps/common/Arma 3 Server"


def try_index(l: list, i: int):
    if type(l) != list or type(i) != int: raise TypeError("l should be a list and i an integer")
    value = None
    try:
        value = l[i]
    except IndexError:
        pass
    return value
    

class Mod:
    def __init__(self, name: str, id: str):
        self.name = name
        self.id = id
        
    def __str__(self):
        return f"{r'{'}\"name\": \"{self.name}\", \"id\": {self.id}{r'}'}"
    
    
class ModList:
    def __init__(self, mods: List[Mod]=[]):
        self.mods = mods
        
    def __str__(self): return [mod.__str__() for mod in self.mods].__str__()
    def __iter__(self): return self.mods.__iter__()
    def __len__(self): return self.mods.__len__()
    def names(self): return [mod.name for mod in self.mods]
    def ids(self): return [mod.id for mod in self.mods]
    
    def find(self, id: str) -> Mod :
        for mod in self.mods:
            if mod.id == id: return mod
        return None
    

class SteamCMDProcess:
    def __init__(self, arguments: list):
        arguments = ["steamcmd"] + arguments + ["+quit"]
        self.steamcmd = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    def __del__(self):
        self.steamcmd.kill()
    
    def wait(self, print_stdout: bool) -> List[int]:
        failed_mod_ids: List[str] = [] 
        line = ''
        while True:
            line = self.steamcmd.stdout.readline()
            if not line:
                break
            if print_stdout: print(line.strip())
            
            match_login_error = re.search(r"Logging in user '.+' to Steam Public\.\.\.FAILED \((.+)\)", line)
            if match_login_error: raise ValueError(f"Error when logging in to steam: {match_login_error.group(1)}")
            
            match_dl_error = re.search(r"ERROR! Download item ([0-9]+)", line)
            if match_dl_error: failed_mod_ids.append(match_dl_error.group(1))
            
        return failed_mod_ids


class SteamCMD:
    def download_mods(mods: ModList) -> ModList:
        username = try_index(sys.argv, 3)
        password = try_index(sys.argv, 4)
        steamguard_code = try_index(sys.argv, 5)
        
        command = ["+login", username, password, steamguard_code]
        print(f"Connecting to {username} using steamguard code {steamguard_code}")
        print("Downloading: ")
        for mod in mods:
            print(f"\t-{mod.name}{' '*(50-mod.name.__len__())}| id={mod.id}")
            command += ["+workshop_download_item", APP_ID, mod.id]
        print("\n")
        failed_downloads = SteamCMDProcess(command).wait(True)
        print(failed_downloads)
        return ModList([mods.find(id) for id in failed_downloads])
            
    def install_mods(mods: ModList):
        for mod in mods:
            print(f"Installing: {mod.name}")
            source = f"{WORKSHOP_PATH}/{mod.id}"
            destination = f"{ARMA_PATH}/mods/@{mod.name}"
            ModFiles.sanitize_subfolders(source)
            if os.path.exists(destination) : shutil.rmtree(destination)
            shutil.move(source, destination)
            
    def maunal_install(mods: ModList) -> ModList:
        mods_not_found = []
        for mod in mods:
            print(f"\nInstalling: {mod.name}")
            source = f"{WORKSHOP_PATH}/{mod.id}/"
            destination = f"{ARMA_PATH}/mods/@{mod.name}/"
            if not os.path.exists(source): 
                print(f"Mod files of {mod.name} not found in '{source}'")
                mods_not_found.append(mod)
                continue
            ModFiles.sanitize_subfolders(source)
            if os.path.exists(destination) : shutil.rmtree(destination)
            shutil.copytree(source, destination)
        return ModList(mods_not_found)


class Arma3ModpackFile:
    def __init__(self, path):
        if not os.path.isfile(path):
            print("Error: Specified path to exported arma3 modpack file (.html) is invalid", file=sys.stderr)
            sys.exit(1)
        
        self.lines = []
        with open(path, "r") as f:
            self.lines = f.readlines()
        
    def parse(self) -> List[Mod]:
        lines = self.lines
        mod_ids = []
        mod_names = []
        for line in lines:
            if "?id=" in line:
                mod_ids.append(line.split("?id=")[1].split("\"")[0])
            if "<td data-type=\"DisplayName\">" in line:
                mod_names.append(ModFiles.sanitize_name(line.split(">")[1].split("<")[0]))
                
        return ModList([Mod(name, id) for id, name in zip(mod_ids, mod_names)])


class ModFiles:
    def sanitize_name(name: str) -> str:
        return name.lower().replace(" ", "_")
    
    def sanitize_subfolders(path: str) -> None:
        for root, dirs, files in os.walk(path):
            for file in files:
                os.rename(os.path.join(root, file), os.path.join(root, file.lower()))
            for dir in dirs:
                os.rename(os.path.join(root, dir), os.path.join(root, dir.lower()))


class ServerConfigFile:
    def generate_params_file(mods: ModList, config_name: str, is_server_mod:bool) -> None:
        if is_server_mod: line = "\n-servermod="
        else: line = "\n-mod="
        for name in mods.names(): line+=f"mods/@{name};"
        with open(f"{ARMA_PATH}/configs/{config_name}.txt", 'a') as file:
            file.write(line)


def check_number_of_args(n: int):
    if len(sys.argv) < n+1:
        print(f"Error: Expected {n} arguments, got {len(sys.argv)-1}, --help to show help")
        sys.exit(1)
        
def log_failed_operations(filename: str, failed_downloads: ModList):
    with open(filename, "w") as f:
        content = "[\n"
        [content := content + f"\t{mod.__str__()},\n" for mod in failed_downloads]
        content = content[:-2]
        content += "\n]"
        f.write(content)

def install_mods():        
    check_number_of_args(4)
    mods: ModList = Arma3ModpackFile(sys.argv[2]).parse()
    failed_downloads = SteamCMD.download_mods(mods)
    succeeded_downloads: ModList = ModList([mod for mod in mods if mod not in failed_downloads])
    SteamCMD.install_mods(succeeded_downloads)
    if failed_downloads:
        print(f"{failed_downloads.__len__()} out of {mods.__len__()} downloads have failed, the list is in ./failed_downloads.json")
        log_failed_operations("./failed_downloads.json", failed_downloads)
    sys.exit(0)
    
def manual_install_mods():
    check_number_of_args(2)
    mods: ModList = Arma3ModpackFile(sys.argv[2]).parse()
    mods_not_found = SteamCMD.maunal_install(mods)
    if mods_not_found:
        print(f"{mods_not_found.__len__()} out of {mods.__len__()} mod folder(s) were not found, the list is in ./failed_manual_install.json")
        log_failed_operations("./failed_manual_install.json", mods_not_found)
    sys.exit(0)
    
def generate_params():
    check_number_of_args(3)
    mods: ModList = Arma3ModpackFile(sys.argv[2]).parse()
    ServerConfigFile.generate_params_file(mods, sys.argv[3], try_index(sys.argv, 4) == "-s")
    sys.exit(0)

def usage():
    print("""
    Usage:
          --help/-h : Show this help message
          
          --install/-i <modpack.html> <username> <password> [steamguard code] : Downloads and install mods from exported arma3 modpack file (.html)
                                          -> Required: <username> & <password>: Steam username & password
                                          -> Optional: [steamguard code]
                                          
          --manual-install/-mi <modpack.html> : Install manually downloaded mods from a exported arma3 modpack file (.html), will look for the files in the default steamcmd installation folder 
          
          --params/-p <modpack.html> <config name> [-s] : Generate params file for arma 3 server,
                                          -> Optional: -s to use as a server-side only modpack
          """)
    sys.exit(0)
    
def no_args():
    usage()
    
def bad_arg():
    print("Error: Incorrect argument specified, --help to show help", file=sys.stderr)
    sys.exit(1)

##

def main():
    argv_map: dict = {"--help": usage, "-h":usage,
                      "--install": install_mods, "-i":install_mods,
                      "--manual-install": manual_install_mods, "-mi": manual_install_mods,
                      "--params": generate_params, "-p":generate_params,
                      }
    if sys.argv.__len__() == 1: fn = usage
    else : fn: callable = argv_map.get(sys.argv[1], bad_arg)
    fn()
    sys.exit(0)

if __name__ == "__main__":
    main()
