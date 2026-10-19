ICONS = {}


def icon(ctx, *names):
    def deco(fn):
        for n in names:
            ICONS[(ctx, n)] = fn
        return fn
    return deco
