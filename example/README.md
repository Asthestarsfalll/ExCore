## Manually setup

1. Run `excore init`
2. Edit `registries` in `.excore.toml` to `registries = [ "*Model: Model, Backbone", "*Data: TrainData, TestData", "Hook", "*Loss", "*LRSche", "*Optimizer", "Transform", "module"]`
3. Run `excore update`, you can see some config items are updated in `.excore.toml`
4. Run `excore auto-register`
5ft Run `excore config-extension`

## Automatically setup
```bash
python init.py
```

## Run examples

Then you can run `python run.py`. For finegrained config, run `python finegrained.py`
