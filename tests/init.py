import os
import subprocess

import toml

predefined_inputs = {
    "name": "tests",
    "src": "source_code",
}


def excute(command: str, inputs=None):
    if inputs:
        result = subprocess.run(
            command.split(" "), input="\n".join(inputs), text=True, capture_output=True
        )
    else:
        result = subprocess.run(
            command.split(" "),
            capture_output=True,
        )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0, result.stderr


def init():
    excute("excore init --force", predefined_inputs.values())
    cfg = toml.load("./.excore.toml")
    cfg["registries"] = [
        "*Model",
        "*Data: TrainData, TestData, DataModule",
        "*Backbone",
        "Head",
        "Hook",
        "*Loss",
        "*LRSche",
        "*Optimizer",
        "Transform",
        "module",
    ]
    with open("./.excore.toml", "w", encoding="UTF-8") as f:
        toml.dump(cfg, f)
    excute("excore update")
    excute("excore auto-register")
    import excore

    assert os.path.exists(os.path.join(excore.workspace.cache_base_dir, "tests"))


if __name__ == "__main__":
    init()
