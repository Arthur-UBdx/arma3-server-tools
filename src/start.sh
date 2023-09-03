#!/bin/bash

usage() {
    echo "Usage:"
    echo "    pystart.sh <config name>: Start the server with the given config"
    echo "    pystart.sh --list/-l : List all available configs"
    exit 0
}

wrong_arg() {
    echo "Wrong argument"
    usage
    exit 1
}

list_configs() {
    path="."
    configs=("$path"/configs/*.txt)
    echo "Available configs:"
    for config in "${configs[@]}"; do
        echo "    - $(basename "${config%.txt}")"
    done
    exit 0
}

start_server() {
    path="."
    config="$1"
    if [ ! -f "$path/configs/$config.txt" ]; then
        echo "Config $config does not exist, --list to list all available configs"
        exit 1
    fi
    "$path/arma3server" "$path/configs/$config.txt"
}

main() {
    if [ $# -lt 1 ]; then
        usage
    fi

    if [ "$1" = "--list" ] || [ "$1" = "-l" ]; then
        list_configs
    else
        start_server "$1"
    fi
}

main "$@"