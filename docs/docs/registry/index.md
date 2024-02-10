---
title: Registry System
sidebar_position: 3
---

## LazyRegistry

The [blog](https://ppwwyyxx.com/blog/2023/Registration-Does-Not-Scale-Well/) of ppwwyyxx inspired `LazyRegistry`. To reduce the unnecessary imports, `ExCore` provides `LazyRegistry`, which store the mappings of class/function name to its `qualname` and dump the mappings to local. When config parsing, the necessary modules will be imported.

Rather than calling it a registry, it's more like providing a tagging feature. With the feature, `ExCore` can find all class/function and statically analysis them, then dump the results in local to support some editing features to config files, see [config extention](./config/config_extention).
