import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from enterprise_os.bootstrap.ceo_bootstrap import boot_ceo


if __name__ == "__main__":
    boot_ceo()
