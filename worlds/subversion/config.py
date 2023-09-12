import io
import os
import pathlib
import sys
from typing import IO, Any, Literal, Tuple, Union, overload
import zipfile


base_id = 8750000

# support for AP world (somewhat copied from SM)
_module_file_name = sys.modules[__name__].__file__
_is_apworld = (not (_module_file_name is None)) and (".apworld" in _module_file_name)


def is_apworld() -> bool:
    return _is_apworld


def _get_zip_file() -> Tuple[zipfile.ZipFile, str]:
    apworld_ext = ".apworld"
    assert _module_file_name
    zip_path = pathlib.Path(_module_file_name[:_module_file_name.index(apworld_ext) + len(apworld_ext)])
    return (zipfile.ZipFile(zip_path), zip_path.stem)


@overload
def open_file_apworld_compatible(
    resource: Union[str, pathlib.Path], mode: Literal["rb"], encoding: None = None
) -> IO[bytes]: ...


@overload
def open_file_apworld_compatible(
    resource: Union[str, pathlib.Path], mode: Literal["r"] = "r", encoding: None = None
) -> IO[str]: ...


def open_file_apworld_compatible(
    resource: Union[str, pathlib.Path], mode: str = "r", encoding: None = None
) -> IO[Any]:
    if _is_apworld:
        (zip_file, stem) = _get_zip_file()
        # zip file needs /, not \
        if isinstance(resource, pathlib.Path):
            resource = resource.as_posix()
        else:
            resource = resource.replace("\\", "/")
        with zip_file as zf:
            zip_file_path = resource[resource.index(stem + "/"):]
            if mode == 'rb':
                return zf.open(zip_file_path, 'r')
            else:
                assert mode in ('r', 'w')
                return io.TextIOWrapper(zf.open(zip_file_path, mode), encoding)
    else:
        return open(resource, mode)


# SM had listDir for apworld compatibility, but type-checker said it would crash


def exists_apworld_compatible(resource: str) -> bool:
    if _is_apworld:
        (zip_file, stem) = _get_zip_file()
        with zip_file as zf:
            if (stem in resource):
                zip_file_path = resource[resource.index(stem + "/"):]
                path = zipfile.Path(zf, zip_file_path)
                return path.exists()
            else:
                return False
    else:
        return os.path.exists(resource)