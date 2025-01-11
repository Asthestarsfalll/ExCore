import subprocess

import toml

predefined_inputs = {
    "name": "example_test",
    "src": "src",
}


def execute(command: str, inputs=None):
    if inputs:
        result = subprocess.run(
            command.split(" "), input="\n".join(inputs), text=True, capture_output=True
        )
    else:
        result = subprocess.run(
            command.split(" "),
            capture_output=True,
        )
    assert result.returncode == 0, result.stderr


def init():
    execute("excore --install-completion")
    execute("excore init --force", predefined_inputs.values())
    cfg = toml.load("./.excore.toml")
    cfg["registries"] = [
        "*Model: Model, Backbone",
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
    execute("excore update")
    execute("excore auto-register")
    execute("excore config-extension")
    execute("excore generate-typehints temp_typing --config ./configs/run.toml")


if __name__ == "__main__":
    init()
