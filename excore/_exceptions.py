class FetcherError(BaseException):
    r"""Base class for fetch related error."""


class InvalidRepo(BaseException):
    r"""The repo provided was somehow invalid."""


class InvalidGitHost(BaseException):
    r"""The git host provided was somehow invalid."""


class GitPullError(BaseException):
    r"""A git pull error occurred."""


class GitCheckoutError(BaseException):
    r"""A git checkout error occurred."""


class InvalidProtocol(BaseException):
    r"""The protocol provided was somehow invalid."""


class HTTPDownloadError(BaseException):
    r""""""


class CoreConfigSupportError(BaseException):
    r""""""


class CoreConfigReadError(BaseException):
    r""""""


class CoreConfigBuildError(BaseException):
    r""""""


class ModuleBuildError(BaseException):
    r""""""


class HookManagerBuildError(BaseException):
    r""""""


class HookBuildError(BaseException):
    r""""""
