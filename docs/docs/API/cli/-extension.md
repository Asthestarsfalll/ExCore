---
title: _extension
sidebar_position: 3
---

## TOC

- **Functions:**
  - 🅵 [config\_extension](#🅵-config_extension) - Generate json_schema for onfig completion and class_mapping for class navigation.
  - 🅵 [\_generate\_typehints](#🅵-_generate_typehints)
  - 🅵 [generate\_typehints](#🅵-generate_typehints) - Generate type hints for modules and isolated objects.
  - 🅵 [\_quote](#🅵-_quote)
  - 🅵 [quote](#🅵-quote) - Quote all special keys in target config files.

## Functions

## 🅵 config\_extension

<details>

<summary>config\_extension</summary>
```python
@app.command()
def config_extension() -> None:
    _generate_taplo_config()
    if not workspace.json_schema_fields:
        logger.warning("You should set json_schema_fields first")
        sys.exit(0)
    _generate_json_schema_and_class_mapping(workspace.json_schema_fields)
```

</details>


Generate json\_schema for onfig completion and class\_mapping for class navigation.
## 🅵 \_generate\_typehints

<details>

<summary>\_generate\_typehints</summary>
```python
def _generate_typehints(
    entry: str, class_name: str, info_class_name: str, config: str = ""
) -> None:
    if not workspace.primary_fields:
        logger.critical("Please initialize the workspace first.")
        return
    target_file = os.path.join(workspace.src_dir, entry + ".py")
    logger.info(f"Generating module type hints in {target_file}.")
    with open(target_file, "w", encoding="UTF-8") as f:
        f.write(f"from typing import Union{', Any' if config else ''}\n")
        f.write(
            "from excore.config.models import ModuleNode, ModuleWrapper\n\n"
        )
        f.write(f"class {class_name}:\n")
        for i in workspace.primary_fields:
            f.write(f"    {i}: Union[ModuleNode, ModuleWrapper]\n")
    logger.info(f"Generating isolated objects type hints in {target_file}.")
    if config:
        from .. import config as cfg

        c = cfg.load(config)
        cfg.silent()
        run_info = c.build_all()[1]
        with open(target_file, "a", encoding="UTF-8") as f:
            f.write(f"\nclass {info_class_name}:\n")
            for key in run_info:
                f.write(f"    {key}: Any\n")
```

</details>

## 🅵 generate\_typehints

<details>

<summary>generate\_typehints</summary>
```python
@app.command()
def generate_typehints(
    entry: str = CArg(default="module_types", help="The file to generate."),
    class_name: Annotated[
        str, COp(help="The class name of type hints.")
    ] = "TypedModules",
    info_class_name: Annotated[
        str, COp(help="The class name of run_info.")
    ] = "RunInfo",
    config: Annotated[
        str, COp(help="Used generate type hints for isolated objects.")
    ] = "",
) -> None:
    _generate_typehints(entry, class_name, info_class_name, config)
```

</details>


Generate type hints for modules and isolated objects.
## 🅵 \_quote

<details>

<summary>\_quote</summary>
```python
def _quote(config: str, override: bool) -> None:
    config_paths: list[str] = []

    def _get_path(path, paths):
        if not os.path.isdir(path):
            paths.append(path)
            return
        pa = os.listdir(path)
        for p in pa:
            _get_path(os.path.join(path, p), paths)

    _get_path(config, config_paths)
    config_paths = [i for i in config_paths if i.endswith(".toml")]
    import toml

    for c in config_paths:
        config_dict = toml.load(c)
        if not override:
            c = os.path.splitext(c)[0] + "_overrode.toml"
        with open(c, "w") as f:
            toml.dump(config_dict, f)
```

</details>

## 🅵 quote

<details>

<summary>quote</summary>
```python
@app.command()
def quote(
    config: Annotated[str, CArg(help="Target config file or folder.")],
    override: Annotated[bool, COp(help="Whether to override configs.")] = False,
) -> None:
    _quote(config, override)
```

</details>


Quote all special keys in target config files.
