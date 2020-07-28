from importlib import import_module


platform = None

def get_platform(provider):
    global platform
    if platform:
        return platform
    platform = import_module("handoff.provider." + provider)
    return platform
