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
    pass


class CoreConfigSupportError(BaseException):
    pass


class CoreConfigParseError(BaseException):
    pass


class StrToClassError(BaseException):
    pass


class EnvVarParseError(BaseException):
    pass


class ModuleBuildError(BaseException):
    pass


class HookManagerBuildError(BaseException):
    pass


class HookBuildError(BaseException):
    pass


class AnnotationsFutureError(Exception):
    pass


class ModuleValidateError(Exception):
    pass
