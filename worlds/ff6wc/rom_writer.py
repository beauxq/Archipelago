import json
import os
from pathlib import Path
import random
import traceback
from typing import Any, Sequence

from settings import get_settings

from .WorldsCollide.wc import WC


def get_base_rom_path(file_name: str = "") -> str:
    from Utils import local_path
    from settings import get_settings

    settings = get_settings()
    if not file_name:
        file_name = settings["ff6wc_options"]["rom_file"]
    if not os.path.exists(file_name):
        file_name = local_path(file_name)
    return file_name


def write_rom_from_gen_data(placements_json: str, wc_args_json: str, output_rom_file_name: str) -> None:
    """ `placements` and `wc_args` are json data from `generate_output` """
    output_directory = os.path.dirname(output_rom_file_name)
    placement_file_name = os.path.join(output_directory, Path(output_rom_file_name).stem + ".applacements")

    placements = json.loads(placements_json)
    rom_name = placements["RomName"]
    placements["output directory"] = output_directory
    placements_json = json.dumps(placements)
    with open(placement_file_name, "w") as file:
        file.write(placements_json)

    wc_args = ["-i", f"{get_base_rom_path()}", "-o", f"{output_rom_file_name}", "-ap", placement_file_name]
    wc_args_flags: Sequence[Any] = json.loads(wc_args_json)
    if not (isinstance(wc_args_flags, list) and all(isinstance(s, str) for s in wc_args_flags)):
        raise ValueError(f"invalid ff6 flag json: {wc_args_json}")
    wc_args.extend(wc_args_flags)
    print(wc_args)
    try:
        import sys
        from copy import deepcopy
        from . import FF6WCSettings
        module_keys = deepcopy(list(sys.modules.keys()))
        for module in module_keys:
            if str(module).startswith("worlds.ff6wc.WorldsCollide"):
                del sys.modules[module]

        # WC uses global `random`
        # `rom_name` has some of the seed in it
        random.seed(rom_name)

        wc = WC()
        wc.main(wc_args)
        os.remove(placement_file_name)

        dialog_id_file_name = os.path.join(output_directory, "dialogs.txt")
        settings: FF6WCSettings = get_settings()["ff6wc_options"]
        dialog_data_dir: FF6WCSettings.DialogDataDirectory = object.__getattribute__(settings, "dialog_data")
        if not os.path.exists(dialog_data_dir):
            os.mkdir(dialog_data_dir)
        dialog_id_storage_file_name = os.path.join(dialog_data_dir, rom_name + ".BIN")
        os.rename(dialog_id_file_name, dialog_id_storage_file_name)
    except Exception as ex:
        print(''.join(traceback.format_tb(ex.__traceback__)))
        print(ex)
        raise ex
