import subprocess

import toml

predefined_inputs = {
    "name": "tests",
    "src": "source_code",
}


def init():
    input_data = "\n".join(predefined_inputs.values())
    subprocess.run(["excore", "init"], stdout=subprocess.PIPE, input=input_data, text=True)
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
    subprocess.run(["excore", "update"])
    subprocess.run(["excore", "auto-register"])

if __name__ == "__main__":
    init()
