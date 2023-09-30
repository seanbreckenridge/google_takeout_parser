import importlib.metadata

# Change here if project is renamed and does not equal the package name
__version__ = importlib.metadata.version(__name__)

del importlib
