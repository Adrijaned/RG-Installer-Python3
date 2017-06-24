#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import subprocess
from urllib import request as url
import configparser
import shutil
import tarfile
import json

# Version of installer
version = "1.0"
# Root URL to download files from
root_url = "https://www.mirc.cz/"
# List of things to download
toDownload = []
# Currently downloaded file
currentFile = ""
# Create instance of config parser
config = configparser.ConfigParser()
# New launcher profiles to create
new_profiles = []


def accept(acceptTo):
    """A little method to get whether user accepts something. Returns boolean value."""
    temp = input(acceptTo + " Y/N...")
    if temp == 'y' or temp == 'Y':
        return True
    elif temp == 'n' or temp == 'N':
        return False
    else:
        print("Prosím používejte pouze Y pro ano, nebo N pro ne.")
        return accept(acceptTo)


def print_makedirs_error(extended=""):
    """Prints default error message on os.makedirs()  fault. 'extended' is meant for extra info"""
    print("Zdá se, že nelze vytvořit potřebnou složku. Může to být způsobeno například " +
          "nedostatečnými privilegii.\nZkontrolujte, že spouštíte tento instalátor s " +
          "právy dostačujícími pro zápis do zadané instalační lokace, a zkuste spustit tento " +
          "instalátor znovu.\nV případě přetrvávajících problémů neváhejte někoho kontaktovat " +
          "na 'https://forum.rebelgames.net/'. Hodně štěstí!" + extended)
    input()
    exit(1)


def urlretrievehook(in1, in2, in3):
    """Outputs progress of downloads"""
    if in1 * in2 >= in3:
        print("Staženo 100 % z " + currentFile + ", celková velikost: " + in3 + " B")
    else:
        temp_toPrint = "Staženo " + str(int(in1 * in2 / (in3 / 100))) + " % (" + (in1 * in2) + \
                       " B) z " + currentFile + ", " + "celková velikost: " + in3 + " B"
        print(temp_toPrint, end="")
        for x in range(len(temp_toPrint)):
            print("\b", end="")


def addProfiles(data):
    """Add profiles to launcher_profiles.json"""
    for profile in new_profiles:
        data["profiles"][profile["name"]] = {u'gameDir': u'' + profile["dir"],
                                             u'name': u'' + profile["name"] + '',
                                             u'lastVersionId': u'' + profile["forge"]}
        outfile = open(file=mainDir + "launcher_profiles.json", mode="wb")
        json.dump(obj=data, fp=outfile, sort_keys=True, indent=4)
        print("Hotovo")


def main():
    global currentFile  # For use in urlretrievehook()
    global mainDir  # For use in addProfiles()
    # Greeting
    print("Vítejte v Linux Instalátoru RebelGames.net! (Adrijaned, v" + version + ")")

    # Get installation root.
    temp_bool = accept("Přejete si použít výchozí instalační lokaci '~/.minecraft/'?")
    if temp_bool:
        mainDir = "~/.minecraft/"
    else:
        mainDir = input("Jakou instalační lokaci si přejete použít? ")
        if not mainDir[-1] == '/':
            mainDir += '/'
    mainDir = os.path.expanduser(mainDir)

    # Check for root to exist. If not, attemp to create
    if not os.path.isdir(mainDir):
        temp_bool = accept("Složka " + mainDir + " neexistuje, přejete si ji vytvořit? ")
        if temp_bool:
            try:
                os.makedirs(mainDir)
            except OSError:
                print_makedirs_error()
        else:
            print("Vytvořte prosím cílovou složku manuálně nebo zadejte instalaci do jiné lokace")
            input()
            exit(0)

    # Create temp dir
    tempDir = "/tmp/rginstall/"
    if not os.path.isdir(tempDir):
        try:
            os.makedirs(tempDir)
        except OSError:
            print_makedirs_error(extended="error in " + tempDir)

    # Check for 'versions' dir
    if not os.path.isdir(mainDir + "versions"):
        try:
            os.makedirs(mainDir + "versions")
        except OSError:
            print_makedirs_error()

    # Check java version
    # Get output from executing "java -version" (from stderr - because yellow fluffy rabbit)
    # Decode the output (b"java version...") to string using utf-8
    # Get version number or "not found"
    java = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT).decode("utf-8")
    java_version = "not found" if java.find('"1.') == -1 else java[java.find('"1.') + 3]
    # Žaves - accepted java versions - if this installer lasts long enough to be more java
    # versions released, just add those here
    accepted_java_versions = ["7", "8", "9", "10"]
    if java_version not in accepted_java_versions:
        print("Vaše verze javy(" + java + ") je zastaralá a proto modpacky RebelGames.net " +
              "nemusí být plně funkční.")
        print("Prosím aktualizujte svou javu na novější verzi na 'https://java.com/'.")

    # Download config
    currentFile = "config.ini"
    try:
        url.urlretrieve(url=root_url + "rginstaller.ini",
                        filename=tempDir + "config.ini",
                        reporthook=urlretrievehook)
    # Except nearly anything - there so many things that may go wrong and no way to handle them
    except:
        print("Nepodařilo se stáhnout konfiguraci, zkontrolujte své internetové připojení a "
              "v případě přetrvávajících obtíží prosím nahlašte bug na "
              "'https://forum.rebelgames.net/")
        input()
        exit(1)
    # Allow developer versions of modpacks?
    devVersions = accept("Chcete povolit testovací verze modpacků? ")

    # Do install forge + forgelibs?
    if accept("Chcete nainstalovat Forge? "):
        toDownload.append({"path": "versions/", "item": "forge"})
    if accept("Chcete nainstalovat knihovny Forge? "):
        toDownload.append({"path": "", "item": "libs"})

    # Read config, ask to install everything from it
    config.read(tempDir + "config.ini")
    for section in config.sections():
        if ("rg" not in section) and (("dev" not in section) or devVersions):
            if accept("Chcete nainstalovat modpack " + config.get(section, "description") + "?"):
                toDownload.append({"path": "", "item": section, "modpack": True,
                                   "desc": config.get(section, "description"),
                                   "forge": config.get(section, "forge")})

    # Download anything requested
    os.makedirs(tempDir + ".minecraft/")  # Download in here
    for option in toDownload:
        currentFile = option["item"]
        url.urlretrieve(url=root_url + option["item"] + ".tar.gz",
                        filename=tempDir + ".minecraft/" + option["item"] +
                                 ".tar.gz",
                        reporthook=urlretrievehook)

    # Install anything downloaded
    for option in toDownload:
        if option["modpack"]:
            if os.path.isdir(mainDir + option["item"] + "/mods/"):
                shutil.rmtree(mainDir + option["item"] + "/mods/")
            new_profiles.append({"name": "[RG] " + option["desc"],
                                 "forge": option["forge"],
                                 "dir": mainDir + option["item"] + "/"})
        tempFile = tarfile.open(name=tempDir + option["item"] + ".tar.gz")
        tempFile.extractall(path=mainDir + option["path"] + option["item"])
        tempFile.close()

    # Create profiles
    if os.path.exists(mainDir + "launcher_profiles.json"):
        print("Přidávání profilů...", end="")
        try:
            json_file = open(file=mainDir + "launcher_profiles.json")
            data = json.load(json_file)
            addProfiles(data=data)
        except ValueError:
            print("Neplatný JSON. Zkuste odstranit soubor '§INSTALLDIR§/launcher%profiles.json'.")
            exit(1)
    elif accept("Nebyl nalezen soubor 'launcher_profiles.json'. Přejete si jej vytvořit? "):
        print("Vytváření profilů...", end="")
        data = {}
        data["authenticationDatabase"] = {}
        addProfiles(data=data)

    # Remove temporal directories
    shutil.rmtree(tempDir)
    print("Instalace hotova")
    input()


if __name__ == '__main__':
    main()
