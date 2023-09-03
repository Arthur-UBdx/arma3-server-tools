# ARMA 3 SERVER TOOLS

## `downloader.py` - Mods downloader

Quick python CLI I made to download, install and generate params files for Arma 3 Server mods.
Only works on linux for the moment.

If the download fails, try deleting the `Steam` folder in `$HOME`

There are parameters at the start of the script file, default values are:

```python
    STEAMCMD_PATH = "steamcmd"
    WORKSHOP_PATH=f"{os.environ['HOME']}/Steam/steamapps/workshop/content/107410"
    ARMA_PATH=f"{os.environ['HOME']}/arma3server"
```

## `start.sh` - Server start script

Bash script to start an Arma 3 server with mods and params files.
