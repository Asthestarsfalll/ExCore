import functools


class CacheOut:
    def __call__(self, func):
        @functools.wraps
        def _cache():
            if not hasattr(self, "elem"):
                setattr(self, "elem", func())
            return getattr(self, "elem")

        return _cache
