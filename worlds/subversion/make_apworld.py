# a script for creating the apworld
# (This is not a module for Archipelago. This is a stand-alone script.)

# run from working directory subversion - working directory will be changed to ..

# directory "SubversionRando" (with the correct version) needs to be a sibling to "Archipelago"
# This does not verify the version.
# TODO: This script could download the correct version from github based on information in requirements.txt

import os
from pathlib import Path
from shutil import copytree, make_archive, rmtree
import subprocess
import tempfile
import zlib

ORIG = "subversion"
TEMP = "subversion_temp"
MOVE = "subversion_move"
LIBRARY_NAME = "subversion_rando"
REQUIREMENTS_FILE_PATH = Path(__file__).parent / "requirements.txt"

if os.getcwd().endswith("Archipelago"):
    os.chdir("worlds")
else:
    os.chdir("..")
assert os.getcwd().endswith("worlds"), f"incorrect directory: {os.getcwd()=}"


def copy_directory_from_commit(github_url: str, dir_name: str, destination_path: str | Path) -> None:
    """
    copies a subdirectory from a specific commit in a GitHub repository to a local path

    Parameters:
        github_url: the GitHub commit URL in the format:
                    https://github.com/github_user/repo_name@commit_hash
        dir_name: the subdirectory under `src` to copy.
        destination_path: the local directory where the contents will be copied to

    Raises:
        ValueError: if the URL is invalid or the directory does not exist.
        FileNotFoundError: if the `dir_name` directory is not found in the commit.
    """
    try:
        repo_url, commit_hash = github_url.rsplit("@", maxsplit=1)
    except ValueError:
        raise ValueError(f"invalid GitHub URL format {github_url} - use the format: <repo_url>@<commit_hash>") from None

    temp_dir_for_lib = tempfile.mkdtemp(dir=os.getcwd(), prefix="lib_temp_clone_")
    clone_cmd = ["git", "clone", repo_url, temp_dir_for_lib]
    checkout_cmd = ["git", "checkout", commit_hash]
    start_cwd = os.getcwd()
    try:
        print(f"{' '.join(clone_cmd)}")
        subprocess.run(clone_cmd, check=True)

        os.chdir(temp_dir_for_lib)

        print(f"{' '.join(checkout_cmd)}")
        subprocess.run(checkout_cmd, check=True)

        src_dir = os.path.join(temp_dir_for_lib, "src", dir_name)
        if not os.path.exists(src_dir):
            raise FileNotFoundError(f"{dir_name=} does not exist under 'src' at this commit")

        print(f"copying {src_dir} to {destination_path}...")
        copytree(src_dir, destination_path, dirs_exist_ok=False)
    finally:
        print(f"cleaning up {temp_dir_for_lib=}")
        if os.path.exists(temp_dir_for_lib):
            rmtree(temp_dir_for_lib)
        os.chdir(start_cwd)


def get_url_from_requirements_file(req_file: str | Path) -> str:
    with open(REQUIREMENTS_FILE_PATH) as file:
        for line in file:
            if line.startswith(LIBRARY_NAME):
                _lib_name, url = line.split("+", maxsplit=1)
                url, _version = url.rsplit("#", maxsplit=1)
                return url
    raise ValueError(f"url not found in requirements file {req_file}")


def lib_crc() -> int:
    crc = 0
    for p, _dir_names, file_names in os.walk(os.path.join(TEMP, LIBRARY_NAME)):
        for file_name in file_names:
            full_path = os.path.join(p, file_name)
            with open(full_path, "rb") as file:
                crc = zlib.crc32(file.read(), crc)
    return crc


def main() -> None:
    assert os.path.exists(ORIG), f"{ORIG} doesn't exist"
    assert os.path.exists(REQUIREMENTS_FILE_PATH), f"{REQUIREMENTS_FILE_PATH=} doesn't exist"
    assert not os.path.exists(TEMP), f"{TEMP} exists"
    assert not os.path.exists(MOVE), f"{MOVE} exists"

    url = get_url_from_requirements_file(REQUIREMENTS_FILE_PATH)

    destination = os.path.join("subversion.apworld")
    if os.path.exists(destination):
        os.unlink(destination)
    assert not os.path.exists(destination)

    copytree(ORIG, TEMP)

    if os.path.exists(os.path.join(TEMP, "__pycache__")):
        rmtree(os.path.join(TEMP, "__pycache__"))

    copy_directory_from_commit(url, LIBRARY_NAME, Path(os.path.join(TEMP, LIBRARY_NAME)).absolute())

    if os.path.exists(os.path.join(TEMP, LIBRARY_NAME, "__pycache__")):
        rmtree(os.path.join(TEMP, LIBRARY_NAME, "__pycache__"))

    if os.path.exists(os.path.join(TEMP, LIBRARY_NAME, "subversion.1.2.ips")):
        rmtree(os.path.join(TEMP, LIBRARY_NAME, "subversion.1.2.ips"))

    crc = lib_crc()
    print(f"writing crc {crc}")
    with open(os.path.join(TEMP, LIBRARY_NAME, "crc"), "w") as crc_file:
        crc_file.write(f"{crc}")
    with open(os.path.join(TEMP, "lib_crc.py"), "w") as crc_module:
        crc_module.write(f"crc = {crc}\n")

    os.rename(ORIG, MOVE)
    os.rename(TEMP, ORIG)

    zip_file_name = make_archive("subversion", "zip", ".", ORIG)
    print(f"{zip_file_name} -> {destination}")
    os.rename(zip_file_name, destination)

    rmtree(ORIG)
    os.rename(MOVE, ORIG)

    assert os.path.exists(ORIG), f"{ORIG} doesn't exist at end"
    assert not os.path.exists(TEMP), f"{TEMP} exists at end"
    assert not os.path.exists(MOVE), f"{MOVE} exists at end"


if __name__ == "__main__":
    main()
