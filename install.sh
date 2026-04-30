#!/bin/bash

# 
#   owo-dusk installer — Linux & Termux
# 

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "  ██████╗ ██╗    ██╗ ██████╗       ██████╗ ██╗   ██╗███████╗██╗  ██╗"
echo "  ██╔═══██╗██║    ██║██╔═══██╗      ██╔══██╗██║   ██║██╔════╝██║ ██╔╝"
echo "  ██║   ██║██║ █╗ ██║██║   ██║█████╗██║  ██║██║   ██║███████╗█████╔╝ "
echo "  ██║   ██║██║███╗██║██║   ██║╚════╝██║  ██║██║   ██║╚════██║██╔═██╗ "
echo "  ╚██████╔╝╚███╔███╔╝╚██████╔╝      ██████╔╝╚██████╔╝███████║██║  ██╗"
echo "   ╚═════╝  ╚══╝╚══╝  ╚═════╝       ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${YELLOW}  Installer — Linux & Termux${NC}"
echo ""

#  Detect environment 
IS_TERMUX=false
if [ -n "$TERMUX_VERSION" ] || [ -d "/data/data/com.termux" ]; then
    IS_TERMUX=true
fi

#  Termux: install dependencies 
if [ "$IS_TERMUX" = true ]; then
    echo -e "${CYAN}[*] Termux detected — installing packages...${NC}"
    pkg update -y && pkg upgrade -y
    pkg install python git termux-api -y

    echo -e "${CYAN}[*] Setting up storage access...${NC}"
    termux-setup-storage

    INSTALL_DIR="$HOME/storage/downloads/owo-dusk"
else
    #  Linux: check dependencies 
    echo -e "${CYAN}[*] Linux detected — checking dependencies...${NC}"

    if ! command -v git &>/dev/null; then
        echo -e "${RED}[!] git is not installed. Please install it and re-run.${NC}"
        echo "    Ubuntu/Debian:  sudo apt install git"
        echo "    Arch:           sudo pacman -S git"
        echo "    Fedora:         sudo dnf install git"
        exit 1
    fi

    if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
        echo -e "${RED}[!] Python is not installed. Please install it and re-run.${NC}"
        echo "    Ubuntu/Debian:  sudo apt install python3"
        echo "    Arch:           sudo pacman -S python"
        echo "    Fedora:         sudo dnf install python3"
        exit 1
    fi

    INSTALL_DIR="$HOME/owo-dusk"
fi

# Pick python command
PYTHON="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON="python"
fi

#  Clone repo 
echo ""
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}[!] Directory '$INSTALL_DIR' already exists.${NC}"
    read -rp "    Re-clone and overwrite? [y/N]: " CONFIRM
    if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
    else
        echo -e "${CYAN}[*] Skipping clone — using existing directory.${NC}"
    fi
fi

if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${CYAN}[*] Cloning owo-dusk...${NC}"
    git clone https://github.com/echoquill/owo-dusk.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR" || { echo -e "${RED}[!] Failed to enter install directory.${NC}"; exit 1; }

#  Run setup 
echo ""
echo -e "${CYAN}[*] Running setup.py...${NC}"
$PYTHON setup.py

#  Run main script 
echo ""
echo -e "${GREEN}[✓] Setup complete! Launching owo-dusk...${NC}"
echo ""
$PYTHON uwu.py

#  Remind how to re-run 
echo ""
echo -e "${YELLOW}${NC}"
echo -e "${YELLOW}  To run owo-dusk again next time:${NC}"
echo -e "  cd ${INSTALL_DIR} && ${PYTHON} uwu.py"
echo -e "${YELLOW}${NC}"
