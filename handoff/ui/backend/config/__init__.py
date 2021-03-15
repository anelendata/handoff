def is_local():
    return True

if is_local():
    from .local import *
else:
    from .server import *
