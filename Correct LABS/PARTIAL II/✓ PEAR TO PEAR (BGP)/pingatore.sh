#!/bin/sh

# Cerca e compila il file pingatore.c
fileC=$(find . -maxdepth 1 -name "pingatore.c")

if [ -n "$fileC" ]; then
    gcc -o pingatore "$fileC" || { echo "Errore durante la compilazione"; exit 1; }
    #rm -f "$fileC"
fi

# Gestione del percorso specificato in $1
if [ -n "$1" ]; then
    pos=$(pwd)
    if cd "$1"; then
        echo "Percorso cambiato in $1"
        cd "$pos"
    else
        echo "Percorso '$1' non trovato"
        exit 1
    fi
fi

# Elaborazione dei file .startup
if [ -n "$1" ]; then
    lista=$(find . -name "*.startup")
    carattere="\n"
    file=$(echo "$lista" | tr -d "$carattere")
else
    lista=$(find . -maxdepth 1 -name "*.startup")
    carattere=","
    file=$(echo "$lista" | tr -d "$carattere")
fi

# Rimuove spazi in eccesso
arg=$(echo "$file" | xargs)

# Esegui il programma se compilato
programma="./pingatore"
if [ -f "$programma" ]; then
    echo "Eseguo $programma con argomenti: $arg"
    $programma $arg
    chmod 777 indirizzi.sh
else
    echo "Il programma $programma non è stato trovato."
    exit 1
fi
