"""Verify all identity card PNG assets exist and report dimensions."""
from pathlib import Path

from identities_data import all_identities

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "assets" / "cards"


def main():
    identities = all_identities()
    missing = []
    sizes = {}

    for identity in identities:
        path = CARDS / f"{identity['id']}.png"
        if not path.exists():
            missing.append(identity["id"])
        else:
            try:
                from PIL import Image
                with Image.open(path) as img:
                    sizes[path.name] = img.size
            except Exception as exc:
                print(f"WARN: {path.name}: {exc}")

    print(f"Checked {len(identities)} identities")
    if missing:
        print(f"MISSING ({len(missing)}): {', '.join(missing)}")
        raise SystemExit(1)

    unique_sizes = set(sizes.values())
    print(f"All card assets present ({len(sizes)} files)")
    if len(unique_sizes) == 1:
        print(f"Uniform size: {next(iter(unique_sizes))}")
    else:
        print(f"Multiple sizes detected ({len(unique_sizes)}):")
        for name, size in sorted(sizes.items()):
            print(f"  {name}: {size[0]}x{size[1]}")


if __name__ == "__main__":
    main()