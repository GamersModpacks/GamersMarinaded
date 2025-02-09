#!/usr/bin/env python3
"""
PackFrameworker Script (v4) in Python

This script replicates the functionality of the original PowerShell script.
It does the following:
  - Loads (or creates) a configuration file with the desired Minecraft version and modloader.
  - Checks (quietly) if 'git' and 'packwiz' are installed (in PATH).
  - Provides a main menu with options to:
      1) Build modpacks (for giga, nano, and server types).
      2) Copy the Beta folder to the Release folder.
      3) Change configuration settings.
      0) Exit.
  - For each build, it prompts the user for a new modpack version (defaulting to the last used one),
    updates (or clones) the PackFramework repository, cleans the build folder, copies required files,
    performs text replacement to update version numbers, and refreshes the pack via packwiz.
    
The script uses cross‐platform functions (os.path, shutil, subprocess) so that it runs on any OS
where Python is available.
"""

import os
import sys
import subprocess
import json
import shutil

# Global constants and paths
SCRIPT_VERSION = "v4"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
LAST_VERSION_FILE = os.path.join(SCRIPT_DIR, "beta", "lastVersion.txt")


def check_dependencies():
    """
    Check if required tools (git and packwiz) are available in PATH.
    If either is not found, a warning is printed to stderr.
    """
    if shutil.which("git") is None:
        print("WARNING: git is not installed or not found in PATH.", file=sys.stderr)
    if shutil.which("packwiz") is None:
        print("WARNING: packwiz is not installed or not found in PATH.", file=sys.stderr)


def load_config():
    """
    Load configuration from the JSON configuration file.
    If the file does not exist, prompt the user to enter the desired settings
    (Minecraft version and modloader) and save them.
    
    Returns:
        A dictionary with keys "mcversion" and "modloader".
    """
    if not os.path.exists(CONFIG_FILE):
        print("Configuration file not found. Please enter the following settings:")
        mcversion = input("Enter Minecraft version (e.g., 1.20.1): ").strip()
        modloader = input("Enter modloader (e.g., forge): ").strip()
        config = {"mcversion": mcversion, "modloader": modloader}
        save_config(config)
    else:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    return config


def save_config(config):
    """
    Save configuration to the JSON configuration file in a human-readable format.
    
    Args:
        config (dict): Configuration dictionary to save.
    """
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def clear_screen():
    """
    Clear the terminal screen (works on Windows and Unix-like systems).
    """
    os.system("cls" if os.name == "nt" else "clear")


def select_new_mp_version():
    """
    Prompt the user to select a new modpack version.
    Reads the last version from beta/lastVersion.txt if it exists,
    and if the user just presses Enter the last version is kept.
    The selected version is saved back to the file.
    
    Returns:
        The selected modpack version as a string.
    """
    # Ensure that the beta directory exists.
    beta_dir = os.path.join(SCRIPT_DIR, "beta")
    os.makedirs(beta_dir, exist_ok=True)

    last_version = ""
    if os.path.exists(LAST_VERSION_FILE):
        try:
            with open(LAST_VERSION_FILE, "r", encoding="utf-8") as f:
                last_version = f.read().strip()
        except Exception:
            last_version = ""
    prompt = f"Select the new modpack version (Press Enter to keep '{last_version}'): "
    new_version = input(prompt).strip()
    if new_version == "":
        new_version = last_version
    # Save the selected version for future use.
    with open(LAST_VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(new_version)
    print(f"Selected modpack version: {new_version}")
    return new_version


def update_pack_framework():
    """
    Update or clone the PackFramework repository.
    If the 'framework' folder exists, attempt to update it using 'git pull origin';
    otherwise, clone the repository from GitHub.
    """
    framework_path = os.path.join(SCRIPT_DIR, "framework")
    if os.path.exists(framework_path):
        print("Found a PackFramework folder, trying to update...")
        try:
            subprocess.run(["git", "pull", "origin"], cwd=framework_path, check=True)
        except subprocess.CalledProcessError:
            print("Error updating PackFramework.")
    else:
        print("PackFramework folder not found, cloning repository...")
        try:
            subprocess.run(
                ["git", "clone", "https://github.com/Den4enko/PackFramework", "framework"],
                cwd=SCRIPT_DIR,
                check=True,
            )
        except subprocess.CalledProcessError:
            print("Error cloning PackFramework repository.")


def copy_directory_contents(src, dest):
    """
    Recursively copy all contents from the source directory to the destination directory.
    Files and directories will be overwritten if they already exist.
    
    Args:
        src (str): Source directory path.
        dest (str): Destination directory path.
    """
    if not os.path.exists(src):
        # Nothing to copy if the source does not exist.
        return
    os.makedirs(dest, exist_ok=True)
    for item in os.listdir(src):
        s_item = os.path.join(src, item)
        d_item = os.path.join(dest, item)
        if os.path.isdir(s_item):
            shutil.copytree(s_item, d_item, dirs_exist_ok=True)
        else:
            shutil.copy2(s_item, d_item)


def replace_in_file(file_path, old_text, new_text):
    """
    Replace all occurrences of old_text with new_text in the given file.
    
    Args:
        file_path (str): Path to the file.
        old_text (str): The text to be replaced.
        new_text (str): The text to replace with.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace(old_text, new_text)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")


def build_modpack(modpacktype, config, selected_version):
    """
    Build the modpack for a given modpack type.
    This includes clearing the output directory, copying necessary files,
    removing files specified in a list, updating version strings in certain files,
    and finally refreshing the pack with packwiz.
    
    Args:
        modpacktype (str): The modpack type (e.g., "giga", "nano", or "server").
        config (dict): Configuration containing "mcversion" and "modloader".
        selected_version (str): The new modpack version string.
    """
    modloader = config["modloader"]
    mcversion = config["mcversion"]
    output_path = os.path.join(SCRIPT_DIR, "beta", modloader, mcversion, modpacktype)
    print(f"Building {mcversion}-{modpacktype}...")

    # Clean up any old files by removing the entire output directory.
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path, exist_ok=True)

    # Merge the necessary files into the output directory.
    # 1. Copy PackFramework's packwiz files.
    src_path = os.path.join(SCRIPT_DIR, "framework", "packwiz", modloader, mcversion, modpacktype)
    copy_directory_contents(src_path, output_path)

    # 2. Copy 'server' files from the mod folder.
    src_path_server = os.path.join(SCRIPT_DIR, "mod", modloader, "all", "server")
    copy_directory_contents(src_path_server, output_path)

    # 3. For nano and giga, copy additional files.
    if modpacktype in ["nano", "giga"]:
        src_path_nano = os.path.join(SCRIPT_DIR, "mod", modloader, "all", "nano")
        copy_directory_contents(src_path_nano, output_path)
        if modpacktype == "giga":
            src_path_giga = os.path.join(SCRIPT_DIR, "mod", modloader, "all", "giga")
            copy_directory_contents(src_path_giga, output_path)

    # Remove files specified in filesToRemove.txt, if it exists.
    files_to_remove_path = os.path.join(output_path, "filesToRemove.txt")
    if os.path.isfile(files_to_remove_path):
        print("Removing files from the list...")
        try:
            with open(files_to_remove_path, "r", encoding="utf-8") as f:
                files_to_remove = f.readlines()
            for file_relative in files_to_remove:
                file_relative = file_relative.strip()
                if file_relative:
                    target_path = os.path.join(output_path, file_relative)
                    if os.path.isfile(target_path):
                        os.remove(target_path)
                    elif os.path.isdir(target_path):
                        shutil.rmtree(target_path)
            os.remove(files_to_remove_path)
        except Exception as e:
            print(f"Error removing files: {e}")

    # Update version strings in specific files.
    replace_in_file(os.path.join(output_path, "pack.toml"), "noVersion", selected_version)
    replace_in_file(os.path.join(output_path, "config", "bcc-common.toml"), "noVersion", selected_version)
    if modpacktype in ["nano", "giga"]:
        replace_in_file(
            os.path.join(output_path, "config", "fancymenu", "custom_locals", "mod", "en_us.local"),
            "noVersion",
            selected_version,
        )

    # Refresh the modpack using packwiz.
    print("Refreshing modpack using packwiz...")
    try:
        subprocess.run(["packwiz", "refresh", "--build"], cwd=output_path, check=True)
    except subprocess.CalledProcessError:
        print("Error refreshing modpack with packwiz.")

    print("Done!")


def copy_beta_to_release():
    """
    Copy the contents of the 'beta' directory into a new 'release' directory.
    After copying, the lastVersion.txt file (if present) is removed from the release folder.
    """
    beta_dir = os.path.join(SCRIPT_DIR, "beta")
    release_dir = os.path.join(SCRIPT_DIR, "release")

    # Remove the existing release folder, if it exists.
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir, exist_ok=True)

    # Copy every item from beta to release.
    for item in os.listdir(beta_dir):
        s_item = os.path.join(beta_dir, item)
        d_item = os.path.join(release_dir, item)
        if os.path.isdir(s_item):
            shutil.copytree(s_item, d_item, dirs_exist_ok=True)
        else:
            shutil.copy2(s_item, d_item)

    # Remove lastVersion.txt from release if it exists.
    last_version_release = os.path.join(release_dir, "lastVersion.txt")
    if os.path.exists(last_version_release):
        try:
            os.remove(last_version_release)
        except Exception as e:
            print(f"Error removing lastVersion.txt from release: {e}")


def change_settings():
    """
    Allow the user to change configuration settings (Minecraft version and modloader).
    The new settings are saved into the configuration file.
    """
    print("Current settings:")
    config = load_config()  # Load current settings.
    print(f"1) Minecraft version: {config.get('mcversion', '')}")
    print(f"2) Modloader: {config.get('modloader', '')}")
    new_mcversion = input("Enter new Minecraft version (Press Enter to keep current): ").strip()
    new_modloader = input("Enter new modloader (Press Enter to keep current): ").strip()

    if new_mcversion:
        config["mcversion"] = new_mcversion
    if new_modloader:
        config["modloader"] = new_modloader

    save_config(config)
    print("Settings updated.")


def main_menu():
    """
    Display the main menu and handle user input.
    The user may choose to build the modpack, copy beta to release,
    change settings, or exit the application.
    """
    config = load_config()
    while True:
        print(f"[PackFrameworker Script {SCRIPT_VERSION}]")
        print("Select an action:")
        print("1) Build")
        print("2) Copy Beta to Release folders")
        print("3) Change settings")
        print("0) Exit")
        choice = input("Enter number: ").strip()
        clear_screen()

        if choice == "0":
            sys.exit(0)
        elif choice == "1":
            # Build modpack.
            selected_version = select_new_mp_version()
            update_pack_framework()
            # Build for each modpack type in the specified order.
            for modpacktype in ["giga", "nano", "server"]:
                build_modpack(modpacktype, config, selected_version)
        elif choice == "2":
            # Copy Beta to Release folders.
            copy_beta_to_release()
        elif choice == "3":
            # Change configuration settings.
            change_settings()
            config = load_config()  # Reload settings.
        else:
            print("I'm sorry, but it seems you've selected the wrong option.")


def main():
    """
    Main entry point: check for required dependencies and then start the main menu.
    """
    check_dependencies()
    main_menu()


if __name__ == "__main__":
    main()
