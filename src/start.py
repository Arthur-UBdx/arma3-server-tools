import sys
import subprocess
import os

def usage():
    print("""
Usage:
    pystart.py <config name>: Start the server with the given config
    pystart.py --list/-l : List all available configs
          """)
    sys.exit(0)
    
def wrong_arg():
    print("Wrong argument")
    usage()
    sys.exit(1)
    
def list_configs():
    path = os.path.dirname(os.path.realpath(__file__))
    configs = [f for f in os.listdir(f"{path}/configs/") if f.endswith(".txt")]
    print("Available configs:")
    for config in configs:
        print("    - {}".format(config))
    sys.exit(0)
    
def start_server(config):
    path = os.path.dirname(os.path.realpath(__file__))
    if not os.path.isfile(f"{path}/configs/{config}.txt"):
        print(f"Config {config} does not exist, --list to list all available configs")
        sys.exit(1)
    subprocess.call([f"{path}/arma3server", f"{path}/configs/{config}.txt"])

def main():
    if sys.argv.__len__() < 2:
        usage()
    arg = sys.argv[1]
    if arg in ['-l', '--list']:
        list_configs()
    else:
        start_server(arg)
        
if __name__ == "__main__":
    main()