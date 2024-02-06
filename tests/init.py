import subprocess

import toml

predefined_inputs = {
    "name": "tests",
    "src": "source_code",
}


def excute(command: str, inputs=None):
    if inputs:
        subprocess.run(
            command.split(" "), stdout=subprocess.PIPE, input="\n".join(inputs), text=True
        )
    else:
        subprocess.run(command.split(" "), stdout=subprocess.PIPE)


def init():
    excute("excore init --force", predefined_inputs.values())
    cfg = toml.load("./.excore.toml")
    cfg["registries"] = [
        "*Model",
        "*Data: TrainData, TestData",
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


if __name__ == "__main__":
    init()
