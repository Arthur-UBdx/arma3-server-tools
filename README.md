# ARMA 3 MODS DOWNLOADER

Quick python CLI I made to download, install and generate params files for Arma 3 Server mods.
Only works on linux for the moment.

```bash
    Usage:
          --help/-h : Show this help message
          
          --install/-i <modpack.html> : Install mods from exported arma3 modpack file (.html)
          --params/-p <modpack.html> <config name> [-s] : Generate params file for arma 3 server,
                                          -> Optional: -s to use as a server-side only modpack 
          
          --whoami/-w : See the current username and password (stored in env vars STEAMCMD_USR and STEAMCMD_PWD)
```

There are parameters at the start of the script file:

Default values are:

```python
    STEAMCMD_PATH = "steamcmd"
    WORKSHOP_PATH=f"{os.environ['HOME']}/Steam/steamapps/workshop/content/107410"
    ARMA_PATH=f"{os.environ['HOME']}/Steam/steamapps/common/Arma 3 Server"
```

Steamcmd is required, the steam username and password are stored in environment variables `STEAMCMD_USR` and `STEAMCMD_PWD`.
