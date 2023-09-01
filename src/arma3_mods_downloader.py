from typing import Tuple, List
import subprocess
import sys
import os
import shutil

## PARAMETERS
STEAMCMD_PATH = "steamcmd"
WORKSHOP_PATH=f"{os.environ['HOME']}/Steam/steamapps/workshop/content/107410"
ARMA_PATH=f"{os.environ['HOME']}/Steam/steamapps/common/Arma 3 Server"
## ----------

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
        
    def __str__(self):
        return [mod.__str__() for mod in self.mods].__str__()
    
    def __iter__(self):
        return self.mods.__iter__()
    
    def __len__(self):
        return self.mods.__len__()
        
    def names(self):
        return [mod.name for mod in self.mods]
    
    def ids(self):
        return [mod.id for mod in self.mods]
    

class SteamCMDProcess:
    def __init__(self, arguments: str):
        self.steamcmd = subprocess.Popen(["steamcmd", arguments, "+quit"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    def __del__(self):
        self.steamcmd.kill()
    
    def run_and_wait(arguments: str) -> int:
        steamcmd = subprocess.Popen(["steamcmd", arguments, "+quit"]).wait()
        return steamcmd
        
    def wait(self, print_stdout: bool) -> int:
        print("\n")
        last_line = ""
        line = ""
        while True:
            last_line = line
            line = self.steamcmd.stdout.readline()
            if not line:
                break
            if print_stdout: print(line.strip())
        print("\n")
        return int("ERROR!" in last_line) # return 0 if ok, 1 if error since steamcmd process always returns 0 even if there is an error

class SteamCMD:
    def whoami():
        print(f"$STEAMCMD_USR: {os.environ.get('STEAMCMD_USR')}\n$STEAMCMD_PWD: {os.environ.get('STEAMCMD_PWD')}")
        sys.exit(0)
        
    def download_mods(mods: ModList) -> List[Tuple[str, str]]:
        failed_downloads = []
        for mod in mods:
            print(f"\nDownloading {mod.name}, id={mod.id}")
            command = f"+login {os.environ['STEAMCMD_USR']} {os.environ['STEAMCMD_PWD']} +workshop_download_item 107410 {mod.id}"
            exit_code = SteamCMDProcess(command).wait(print_stdout=True)
            if bool(exit_code): failed_downloads.append(mod)
        return ModList(failed_downloads)
            
    def install_mods(mods: ModList):
        for mod in mods:
            print(f"Installing: {mod.name}")
            source = f"{WORKSHOP_PATH}/{mod.id}"
            destination = f"{ARMA_PATH}/mods/@{mod.name}"
            ModFiles.sanitize_subfolders(f"{WORKSHOP_PATH}/{mod.id}")
            if os.path.exists(destination) : shutil.rmtree(destination)
            shutil.copytree(source, destination)


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

def install_mods():        
    check_number_of_args(2)
    mods: ModList = Arma3ModpackFile(sys.argv[2]).parse()
    failed_downloads = SteamCMD.download_mods(mods)
    succeeded_downloads: ModList = ModList([mod for mod in mods if mod not in failed_downloads])
    SteamCMD.install_mods(succeeded_downloads)
    if failed_downloads:
        print(f"{failed_downloads.__len__()} out of {mods.__len__()} downloads have failed, the list is in ./failed_downloads.json")
        with open("./failed_downloads.json", "w") as f:
            content = "[\n"
            [content := content + f"\t{mod.__str__()},\n" for mod in failed_downloads]
            content = content[:-2]
            content += "\n]"
            f.write(content)
        
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
          
          --install/-i <modpack.html> : Install mods from exported arma3 modpack file (.html)
          --params/-p <modpack.html> <config name> [-s] : Generate params file for arma 3 server,
                                          -> Optional: -s to use as a server-side only modpack 
          
          --whoami/-w : See the current username and password (stored in env vars STEAMCMD_USR and STEAMCMD_PWD)
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
                      "--params": generate_params, "-p":generate_params,
                      "--whoami": SteamCMD.whoami, "-w": SteamCMD.whoami,
                      }
    # check_number_of_args(1)
    if sys.argv.__len__() == 1: fn = usage
    else : fn: callable = argv_map.get(sys.argv[1], bad_arg)
    fn()
    sys.exit(0)

if __name__ == "__main__":
    main()