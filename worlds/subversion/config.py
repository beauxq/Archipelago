import logging
import os
import pathlib
from shutil import rmtree
import sys
import zipfile


base_id = 8750000


def is_apworld() -> bool:
    module_file_name = sys.modules[__name__].__file__
    return (module_file_name is not None) and (".apworld" in module_file_name)


def _get_zip_file() -> tuple[zipfile.ZipFile, str]:
    apworld_ext = ".apworld"
    module_file_name = sys.modules[__name__].__file__
    assert module_file_name
    zip_path = pathlib.Path(module_file_name[:module_file_name.index(apworld_ext) + len(apworld_ext)])
    return (zipfile.ZipFile(zip_path), zip_path.stem)


def load_library() -> None:
    from Utils import user_path

    (zip_file, _stem) = _get_zip_file()
    logging.info("loading subversion_rando library...")
    for file in zip_file.namelist():
        if file.startswith("subversion/subversion_rando/"):
            new_path = file[11:]
            zip_file.getinfo(file).filename = new_path
            zip_file.extract(file, user_path("lib"))


if is_apworld():
    if "lib" not in sys.path:
        # for running from source
        sys.path.append("lib")

    from Utils import user_path
    user_lib_path = os.path.join(user_path("lib"))
    if user_lib_path not in sys.path:
        # for running from AppImage
        sys.path.append(user_lib_path)

    lib_dir = os.path.join("lib", "subversion_rando")
    lib_crc_file_name = os.path.join(lib_dir, "crc")
    validated = False
    if os.path.exists(lib_crc_file_name):
        from .lib_crc import crc  # type: ignore
        # created by apworld script

        with open(lib_crc_file_name, encoding="utf-8") as lib_crc_file:
            text_crc = lib_crc_file.read()
        if int(text_crc) == crc:
            validated = True
    if not validated:
        if os.path.exists(lib_dir):
            rmtree(lib_dir)
        load_library()
