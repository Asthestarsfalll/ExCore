from excore.registry import auto_register
from excore.json_schema import generate_json_shcema

auto_register("./src")

field_mapper = {
    "Model": ["Model", "BackBone"],
    "Data": ["TrainData", "TestData"],
    "Hook": "ConfigHook",
}

generate_json_shcema(field_mapper)
