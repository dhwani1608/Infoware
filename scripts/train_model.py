from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.trainer import train_models


if __name__ == "__main__":
    metrics = train_models()
    print(metrics)
