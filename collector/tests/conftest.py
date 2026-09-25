import sys
from pathlib import Path

# Add collector dir to sys.path so tests can import modules directly
collector_dir = Path(__file__).parent.parent
if str(collector_dir) not in sys.path:
    sys.path.insert(0, str(collector_dir))
