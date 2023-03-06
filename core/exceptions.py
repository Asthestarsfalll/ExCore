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
    r"""The class that represents http request error."""


class CoreConfigSupportError(BaseException):
    r"""The class that represents http request error."""


class CoreConfigReadError(BaseException):
    r"""The class that represents http request error."""


class CoreConfigBuildError(BaseException):
    r"""The class that represents http request error."""


class ModuleBuildError(BaseException):
    r"""The class that represents http request error."""
