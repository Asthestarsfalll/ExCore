import functools


class CacheOut:
    def __call__(self, func):
        @functools.wraps(func)
        def _cache(self):
            if not hasattr(self, "elem"):
                setattr(self, "elem", func(self))
            return getattr(self, "elem")

        return _cache
