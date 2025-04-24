---
title: _exceptions
---

## TOC

- **Classes:**
  - 🅲 [FetcherError](#🅲-fetchererror) - Base class for fetch related error.
  - 🅲 [InvalidRepo](#🅲-invalidrepo) - The repo provided was somehow invalid.
  - 🅲 [InvalidGitHost](#🅲-invalidgithost) - The git host provided was somehow invalid.
  - 🅲 [GitPullError](#🅲-gitpullerror) - A git pull error occurred.
  - 🅲 [GitCheckoutError](#🅲-gitcheckouterror) - A git checkout error occurred.
  - 🅲 [InvalidProtocol](#🅲-invalidprotocol) - The protocol provided was somehow invalid.
  - 🅲 [HTTPDownloadError](#🅲-httpdownloaderror)
  - 🅲 [CoreConfigSupportError](#🅲-coreconfigsupporterror)
  - 🅲 [CoreConfigParseError](#🅲-coreconfigparseerror)
  - 🅲 [StrToClassError](#🅲-strtoclasserror)
  - 🅲 [EnvVarParseError](#🅲-envvarparseerror)
  - 🅲 [ModuleBuildError](#🅲-modulebuilderror)
  - 🅲 [HookManagerBuildError](#🅲-hookmanagerbuilderror)
  - 🅲 [HookBuildError](#🅲-hookbuilderror)
  - 🅲 [AnnotationsFutureError](#🅲-annotationsfutureerror)
  - 🅲 [ModuleValidateError](#🅲-modulevalidateerror)

## Classes

## 🅲 FetcherError

```python
class FetcherError(BaseException):
```

Base class for fetch related error.
## 🅲 InvalidRepo

```python
class InvalidRepo(BaseException):
```

The repo provided was somehow invalid.
## 🅲 InvalidGitHost

```python
class InvalidGitHost(BaseException):
```

The git host provided was somehow invalid.
## 🅲 GitPullError

```python
class GitPullError(BaseException):
```

A git pull error occurred.
## 🅲 GitCheckoutError

```python
class GitCheckoutError(BaseException):
```

A git checkout error occurred.
## 🅲 InvalidProtocol

```python
class InvalidProtocol(BaseException):
```

The protocol provided was somehow invalid.
## 🅲 HTTPDownloadError

```python
class HTTPDownloadError(BaseException):
```
## 🅲 CoreConfigSupportError

```python
class CoreConfigSupportError(BaseException):
```
## 🅲 CoreConfigParseError

```python
class CoreConfigParseError(BaseException):
```
## 🅲 StrToClassError

```python
class StrToClassError(BaseException):
```
## 🅲 EnvVarParseError

```python
class EnvVarParseError(BaseException):
```
## 🅲 ModuleBuildError

```python
class ModuleBuildError(BaseException):
```
## 🅲 HookManagerBuildError

```python
class HookManagerBuildError(BaseException):
```
## 🅲 HookBuildError

```python
class HookBuildError(BaseException):
```
## 🅲 AnnotationsFutureError

```python
class AnnotationsFutureError(Exception):
```
## 🅲 ModuleValidateError

```python
class ModuleValidateError(Exception):
```
