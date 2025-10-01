# Ensure project root is on sys.path for test imports
import sys
import pathlib
root = pathlib.Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
