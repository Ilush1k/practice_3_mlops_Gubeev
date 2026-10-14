"""Детерминированная подготовка Iris/Wine; изменяется только файл выбранного режима."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.datasets import load_iris, load_wine


def source_frame(name: str) -> pd.DataFrame:
    frame = {"iris": load_iris, "wine": load_wine}[name](as_frame=True).frame
    return frame.sort_values(list(frame.columns), kind="mergesort").reset_index(drop=True)


def prepare(mode: str, output_dir: Path = Path("data")) -> Path:
    name = "wine" if mode == "wine" else "iris"
    frame = source_frame(name)
    if mode == "iris_features":
        frame["sepal_area"] = frame["sepal length (cm)"] * frame["sepal width (cm)"]
        frame["petal_area"] = frame["petal length (cm)"] * frame["petal width (cm)"]
    elif mode not in {"base", "wine"}:
        raise ValueError(f"Неизвестный режим: {mode}")
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{name}.csv"
    frame.to_csv(destination, index=False, encoding="utf-8", lineterminator="\n", float_format="%.17g")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["base", "wine", "iris_features"])
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    print(prepare(args.mode, args.output_dir).as_posix())


if __name__ == "__main__":
    main()
