## Manually setup

1. Run `excore init`
2. Edit `registries` in `.excore.toml` to `registries = [ "*Model: Model, Backbone", "*Data: TrainData, TestData", "Hook", "*Loss", "*LRSche", "*Optimizer", "Transform", "module"]`
3. Run `excore update`, you can see some config items are updated in `.excore.toml`
4. Run `excore auto-register`
5. Run `excore config-extension`
6. Run `python run.py`

## Automatically setup
```bash
python init.py
```

Then you can run `python run.py`
