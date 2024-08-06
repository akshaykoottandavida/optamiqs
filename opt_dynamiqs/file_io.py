import numpy as np
from jaxtyping import ArrayLike
import time

import os
import glob
import re
import h5py

__all__ = [
    "save_and_print",
    "append_to_h5",
    "write_to_h5",
    "generate_file_path",
    "extract_info_from_h5",
]


def save_and_print(
    filepath: str,
    data_dict: dict,
    params_to_optimize: ArrayLike | dict,
    init_param_dict: dict,
    epoch: int = 0,
    prev_time: float = 0.0,
):
    """saves the infidelities and optimal parameters obtained at each timestep"""
    infidelities = data_dict["infidelities"]
    if type(params_to_optimize) is dict:
        data_dict = data_dict | params_to_optimize
    else:
        data_dict["opt_params"] = params_to_optimize
    print(
        f"epoch: {epoch}, fids: {1 - infidelities},"
        f" elapsed_time: {np.around(time.time() - prev_time, decimals=3)} s"
    )
    if epoch != 0:
        append_to_h5(filepath, data_dict)
    else:
        write_to_h5(filepath, data_dict, init_param_dict)


def generate_file_path(extension, file_name, path):
    # Ensure the path exists.
    os.makedirs(path, exist_ok=True)

    # Create a save file name based on the one given; ensure it will
    # not conflict with others in the directory.
    max_numeric_prefix = -1
    for file_name_ in glob.glob(os.path.join(path, "*")):
        if f"_{file_name}.{extension}" in file_name_:
            numeric_prefix = int(
                re.match(r"(\d+)_", os.path.basename(file_name_)).group(1)
            )
            max_numeric_prefix = max(numeric_prefix, max_numeric_prefix)

    # Generate the file path.
    file_path = os.path.join(
        path, f"{str(max_numeric_prefix + 1).zfill(5)}_{file_name}.{extension}"
    )
    return file_path


def extract_info_from_h5(filepath):
    data_dict = {}
    with h5py.File(filepath, "r") as f:
        for key in f.keys():
            data_dict[key] = f[key][()]
        param_dict = dict(f.attrs.items())
    return data_dict, param_dict


def append_to_h5(filepath, data_dict):
    with h5py.File(filepath, "a") as f:
        for key, val in data_dict.items():
            f[key].resize(f[key].shape[0] + 1, axis=0)
            f[key][-1] = val


def write_to_h5(filepath, data_dict, param_dict):
    with h5py.File(filepath, "a") as f:
        for key, val in data_dict.items():
            f.create_dataset(key, data=[val], chunks=True, maxshape=(None, *val.shape))
        for kwarg in param_dict.keys():
            try:
                f.attrs[kwarg] = param_dict[kwarg]
            except TypeError:
                f.attrs[kwarg] = str(param_dict[kwarg])
