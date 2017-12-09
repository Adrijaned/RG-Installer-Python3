#!/usr/bin/python3
# -*- coding: utf-8 -*-
import configparser
import json
import os
import shutil
import subprocess
import tarfile
import time
from urllib import request as url

# Version of installer
version = "1.1"
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
# Debug flag
debug = False
# Open logfile
lof_file = open(file="log.txt", mode="at")
# Changelist
changelist = """
V 1.1:
    * added changelist
    * logging now writes newlines
    * I'm not exactly sure why it worked before, but now it is, as far as i 
        know, working, AKA forge extracts into the right directory
        * minor update: now even the second part of forge extracts into the
            right directory
    * Changed license from GNU GPL to MIT
"""


def log(message):
    print(message)
    lof_file.write(message + "\n")
    lof_file.flush()


def print_debug(message="debug"):
    if debug:
        log(message)


def accept(acceptTo):
    """
    Get whether user accepted to something.

    :param acceptTo: Question to ask user
    :return: Boolean - True if user accepted, False otherwise
    """
    temp = input(acceptTo + " Y/N...")
    if temp == 'y' or temp == 'Y':
        return True
    elif temp == 'n' or temp == 'N':
        return False
    else:
        log("Prosím používejte pouze Y pro ano, nebo N pro ne.")
        return accept(acceptTo)


def print_makedirs_error(extended=""):
    """Prints default error message on os.makedirs()  fault. 'extended' is meant for extra info"""
    log(
        "Zdá se, že nelze vytvořit potřebnou složku. Může to být způsobeno například " +
        "nedostatečnými privilegii.\nZkontrolujte, že spouštíte tento instalátor s " +
        "právy dostačujícími pro zápis do zadané instalační lokace, a zkuste spustit tento " +
        "instalátor znovu.\nV případě přetrvávajících problémů neváhejte někoho kontaktovat " +
        "na 'https://forum.rebelgames.net/'. Hodně štěstí!" + extended)
    time.sleep(3)
    exit(1)


def urlretrievehook(in1, in2, in3):
    """Outputs progress of downloads"""
    if in1 * in2 >= in3:
        # Hack - add so many whitespace characters
        log("Staženo 100 % z '" + currentFile + "', celková velikost: " + str(
            in3) + " B"
                   "                  ")
    else:
        temp_toPrint = "Staženo " + str(int(in1 * in2 / (in3 / 100))) + " % (" + \
                       str(
                           in1 * in2) + " B) z '" + currentFile + "', " + \
                       "celková velikost: " + str(in3) + " B"
        print(temp_toPrint, end="")
        for x in range(len(temp_toPrint)):
            print("\b", end="")


def addProfiles(data):
    """Add profiles to launcher_profiles.json"""
    for profile in new_profiles:
        if "profiles" not in data:
            data["profiles"] = {}
        data["profiles"][profile["name"]] = {u'gameDir': u'' + profile["dir"],
                                             u'name': u'' + profile[
                                                 "name"] + '',
                                             u'lastVersionId': u'' + profile[
                                                 "forge"]}
        outfile = open(file=mainDir + "launcher_profiles.json", mode="w")
        json.dump(obj=data, fp=outfile, sort_keys=True, indent=4)
    log("Hotovo")
    print_debug("addProfiles Done")


def main():
    print_debug("Start")
    global currentFile  # For use in urlretrievehook()
    global mainDir  # For use in addProfiles()

    # Greeting
    log(
        "Vítejte v Linux Instalátoru RebelGames.net! (Adrijaned, v" + version +
        ")")

    # Get installation root.
    temp_bool = accept(
        "Přejete si použít výchozí instalační lokaci '~/.minecraft/'?")
    if temp_bool:
        mainDir = "~/.minecraft/"
    else:
        mainDir = input("Jakou instalační lokaci si přejete použít? ")
        if not mainDir[-1] == '/':
            mainDir += '/'
    mainDir = os.path.expanduser(mainDir)
    print_debug("1")

    # Check for root to exist. If not, attemp to create
    if not os.path.isdir(mainDir):
        temp_bool = accept(
            "Složka " + mainDir + " neexistuje, přejete si ji vytvořit? ")
        if temp_bool:
            try:
                os.makedirs(mainDir)
            except OSError:
                print_makedirs_error()
        else:
            log(
                "Vytvořte prosím cílovou složku manuálně nebo zadejte instalaci"
                " do jiné lokace")
            time.sleep(3)
            exit(0)
    print_debug("2")

    # Create temp dir
    tempDir = "/tmp/rginstall/"
    if os.path.isdir(tempDir):
        shutil.rmtree(tempDir)
    try:
        os.makedirs(tempDir)
    except OSError:
        print_makedirs_error(extended="error in " + tempDir)
    print_debug("3")

    # Check for 'versions' dir
    if not os.path.isdir(mainDir + "versions"):
        try:
            os.makedirs(mainDir + "versions")
        except OSError:
            print_makedirs_error()
    print_debug("4")

    # Check java version
    # Get output from executing "java -version" (from stderr - because yellow fluffy rabbit)
    # Decode the output (b"java version...") to string using utf-8
    # Get version number or "not found"
    java = subprocess.check_output(["java", "-version"],
                                   stderr=subprocess.STDOUT).decode("utf-8")
    java_version = "not found" if java.find('"1.') == -1 else java[
        java.find('"1.') + 3]
    # Žaves - accepted java versions - if this installer lasts long enough to be more java
    # versions released, just add those here
    accepted_java_versions = ["7", "8", "9", "10", "11"]
    if java_version not in accepted_java_versions:
        log(
            "Vaše verze javy(" + java + ") je zastaralá a proto modpacky RebelGames.net " +
            "nemusí být plně funkční.")
        log(
            "Prosím aktualizujte svou javu na novější verzi na 'https://java.com/'.")
    print_debug("5")

    # Download config
    currentFile = "config.ini"
    try:
        url.urlretrieve(url=root_url + "rginstaller.ini",
                        filename=tempDir + "config.ini",
                        reporthook=urlretrievehook)
    # Except nearly anything - there so many things that may go wrong and no way to handle them
    except:
        log(
            "Nepodařilo se stáhnout konfiguraci instalátoru, zkontrolujte své internetové "
            "připojení a v případě přetrvávajících obtíží prosím nahlašte bug na "
            "'https://forum.rebelgames.net/")
        time.sleep(3)
        exit(1)
    # Allow developer versions of modpacks?
    devVersions = accept("Chcete povolit testovací verze modpacků? ")
    print_debug("6")

    # Do install forge + forgelibs?
    if accept("Chcete nainstalovat Forge? "):
        toDownload.append(
            {"path": "versions/", "item": "forge", "modpack": False})
    if accept("Chcete nainstalovat knihovny Forge? "):
        toDownload.append({"path": "", "item": "libs", "modpack": False})
    print_debug("7")

    # Read config, ask to install everything from it
    config.read(tempDir + "config.ini")
    for section in config.sections():
        if ("rg" not in section) and (("dev" not in section) or devVersions):
            if accept("Chcete nainstalovat modpack " + config.get(section,
                                                                  "description") + "?"):
                toDownload.append({"path": "", "item": section, "modpack": True,
                                   "desc": config.get(section, "description"),
                                   "forge": config.get(section, "forge")})
    print_debug("8")

    # Download anything requested
    os.makedirs(tempDir + ".minecraft/")  # Download in here
    for option in toDownload:
        currentFile = option["item"] + ".tar.gz"
        try:
            url.urlretrieve(url=root_url + currentFile,
                            filename=tempDir + ".minecraft/" + currentFile,
                            reporthook=urlretrievehook)
        except:
            log("Nepodařilo se stáhnout " + option[
                "desc"] + " zkontrolujte své internetové "
                          "připojení a v případě přetrvávajících obtíží prosím nahlašte bug na "
                          "'https://forum.rebelgames.net/")
            time.sleep(3)
            exit(1)
    print_debug("9")

    # Install anything downloaded
    for option in toDownload:
        if option["modpack"]:
            if os.path.isdir(mainDir + option["item"] + "/mods/"):
                shutil.rmtree(mainDir + option["item"] + "/mods/")
            new_profiles.append({"name": "[RG] " + option["desc"],
                                 "forge": option["forge"],
                                 "dir": mainDir + option["item"] + "/"})
        tempFile = tarfile.open(
            name=tempDir + ".minecraft/" + option["item"] + ".tar.gz")
        tempFile.extractall(path=mainDir + option["path"] + (option["item"] if
        not (option["item"] in ("forge", "libs")) else ""))
        tempFile.close()
    print_debug("toDownload = " + str(toDownload))
    print_debug("10")

    # Create profiles
    if os.path.exists(mainDir + "launcher_profiles.json"):
        log("Přidávání profilů...")
        try:
            json_file = open(file=mainDir + "launcher_profiles.json")
            data = json.load(json_file)
            addProfiles(data=data)
        except ValueError:
            log(
                "Neplatný JSON. Zkuste odstranit soubor '§INSTALLDIR§/launcher_profiles.json'.")
            exit(1)
    elif accept(
            "Nebyl nalezen soubor 'launcher_profiles.json'. Přejete si jej vytvořit? "):
        log("Vytváření profilů...")
        data = {}
        data["authenticationDatabase"] = {}
        addProfiles(data=data)
    print_debug("11")

    # Remove temporal directories
    #shutil.rmtree(tempDir)
    log("Instalace hotova")
    time.sleep(3)
    print_debug("END")


if __name__ == '__main__':
    main()
