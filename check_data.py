"""Проверка состава, исходных значений, вычисляемых признаков и SHA-256 CSV."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from prepare_data import source_frame

VERSIONS = {
    "base": ({"iris.csv"}, False),
    "wine": ({"iris.csv", "wine.csv"}, False),
    "iris_features": ({"iris.csv"}, True),
    "merged": ({"iris.csv", "wine.csv"}, True),
}


def sha256_file(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def check_data(directory: Path = Path("data"), version: str = "merged") -> list[dict]:
    expected_files, features = VERSIONS[version]
    actual_files = {path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file()}
    if actual_files != expected_files:
        raise ValueError(f"Состав {version}: ожидалось {sorted(expected_files)}, получено {sorted(actual_files)}")
    result = []
    for filename in sorted(expected_files):
        path = directory / filename
        frame = pd.read_csv(path, float_precision="round_trip")
        original = source_frame(path.stem)
        columns = list(original.columns)
        if path.stem == "iris" and features:
            columns += ["sepal_area", "petal_area"]
        if any(str(column).startswith("Unnamed:") for column in frame.columns):
            raise ValueError(f"{filename}: обнаружен безымянный столбец индекса")
        if list(frame.columns) != columns:
            raise ValueError(f"{filename}: неверные столбцы или порядок: {list(frame.columns)}")
        if len(frame) != len(original):
            raise ValueError(f"{filename}: неверное число строк: {len(frame)} вместо {len(original)}")
        missing = int(frame.isna().sum().sum())
        if missing:
            raise ValueError(f"{filename}: пропущенных значений {missing}")
        if not np.allclose(frame[list(original.columns)].to_numpy(), original.to_numpy(), rtol=1e-12, atol=1e-12):
            raise ValueError(f"{filename}: исходные значения, target или сортировка изменены")
        if path.stem == "iris" and features:
            for area, length, width in [("sepal_area", "sepal length (cm)", "sepal width (cm)"),
                                        ("petal_area", "petal length (cm)", "petal width (cm)")]:
                if not np.allclose(frame[area], frame[length] * frame[width], rtol=1e-12, atol=1e-12):
                    raise ValueError(f"{filename}: неверные значения {area}")
        result.append({"path": f"{directory.name}/{filename}", "sha256": sha256_file(path),
                       "rows": len(frame), "column_count": len(frame.columns),
                       "columns": list(frame.columns), "missing_values": missing})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--version", choices=list(VERSIONS), default="merged")
    args = parser.parse_args()
    try:
        rows = check_data(args.data_dir, args.version)
    except (ValueError, OSError, TypeError) as exc:
        parser.exit(1, f"ОШИБКА: {exc}\n")
    print(json.dumps(rows, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
