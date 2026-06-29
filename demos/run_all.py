"""Run every demo scenario end to end.

    python demos/run_all.py

Each scenario is independent and fully offline — no network, GPU, or model
download — so they can be run in any order or on their own, and they double as
smoke tests.
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SCENARIOS = [
    "01_creator_voice_to_post",
    "02_agency_full_pipeline",
    "03_devrel_repo_launch",
    "04_multiplatform_repurpose",
    "05_longform_studio",
]


def main() -> None:
    for name in SCENARIOS:
        mod = importlib.import_module(name)
        mod.main()
    print("\n" + "=" * 70)
    print("  All demo scenarios completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
