# a script for creating the apworld
# If I haven't removed this before merging to Archipelago main, remind me to remove it.

# directory "SubversionRando" (with the correct version) needs to be a sibling to "Archipelago"

import os
from shutil import copytree, make_archive, rmtree

ORIG = "subversion"
COPY_B = "subversion_b"
COPY_C = "subversion_c"


assert os.path.exists(ORIG), f"{ORIG} doesn't exist"
assert not os.path.exists(COPY_B), f"{COPY_B} exists"
assert not os.path.exists(COPY_C), f"{COPY_C} exists"

subversion_rando_dir = os.path.join("..", "..", "SubversionRando", "src", "subversion_rando")
assert os.path.exists(subversion_rando_dir), f"{subversion_rando_dir} doesn't exist"

destination = os.path.join("subversion.apworld")
if os.path.exists(destination):
    os.unlink(destination)
assert not os.path.exists(destination)

copytree(ORIG, COPY_B)

if os.path.exists(os.path.join(COPY_B, "__pycache__")):
    rmtree(os.path.join(COPY_B, "__pycache__"))

# change subversion_rando imports to relative
for file_name in os.listdir(COPY_B):
    # print(file_name)
    if file_name.endswith(".py"):
        full_name = os.path.join(COPY_B, file_name)
        with open(full_name) as file:
            lines = file.readlines()
        change_made = False
        for i in range(len(lines)):
            for import_check, import_replace in (
                ("from subversion_rando", "from .subversion_rando"),
                ("import subversion_rando", "import .subversion_rando"),
            ):
                if lines[i].startswith(import_check):
                    lines[i] = import_replace + lines[i][len(import_check):]
                    change_made = True
        if change_made:
            with open(full_name, "w") as file:
                file.writelines(lines)

copytree(subversion_rando_dir, os.path.join(COPY_B, "subversion_rando"))

if os.path.exists(os.path.join(COPY_B, "subversion_rando", "__pycache__")):
    rmtree(os.path.join(COPY_B, "subversion_rando", "__pycache__"))

os.rename(ORIG, COPY_C)
os.rename(COPY_B, ORIG)

zip_file_name = make_archive("subversion", "zip", ".", ORIG)
print(f"{zip_file_name} -> {destination}")
os.rename(zip_file_name, destination)

rmtree(ORIG)
os.rename(COPY_C, ORIG)

assert os.path.exists(ORIG), f"{ORIG} doesn't exist at end"
assert not os.path.exists(COPY_B), f"{COPY_B} exists at end"
assert not os.path.exists(COPY_C), f"{COPY_C} exists at end"
