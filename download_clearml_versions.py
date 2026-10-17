"""Скачать три завершённые версии по ID в отдельные пустые директории."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from clearml_versions import API_HOST, SPECS, WORK_DIR, get_dataset, setup_sdk


def download_versions(output_dir: Path | None = None, *, fresh_cache: bool = True,
                      expected_api_host: str = API_HOST) -> Path:
    output_dir = (output_dir or WORK_DIR / "downloads" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Директория скачивания должна быть пустой")
    setup_sdk(expected_api_host, fresh_cache=fresh_cache)
    output_dir.mkdir(parents=True, exist_ok=True)
    for mode, spec in SPECS.items():
        dataset = get_dataset(mode)
        target = output_dir / spec["version"]
        dataset.get_mutable_local_copy(target_folder=str(target), overwrite=False)
        print(f"Скачана {spec['version']}: {spec['id']}", flush=True)
    return output_dir


def latest_download() -> Path | None:
    root = WORK_DIR / "downloads"
    if root.is_dir():
        for path in sorted(root.iterdir(), reverse=True):
            if path.is_dir() and all((path / spec["version"]).is_dir() for spec in SPECS.values()):
                return path
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--reuse-cache", action="store_true")
    parser.add_argument("--expected-api-host", default=API_HOST)
    args = parser.parse_args()
    result = download_versions(args.output_dir, fresh_cache=not args.reuse_cache,
                               expected_api_host=args.expected_api_host)
    print(f"Скачанные версии: {result}")


if __name__ == "__main__":
    main()
