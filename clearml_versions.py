"""Базовая версия ClearML Dataset и общие настройки трёх версий практики."""
from __future__ import annotations

import argparse
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from prepare_data import prepare

ROOT = Path(__file__).resolve().parent
PROJECT = "MIIT/MLOps/practice_3/Gubeev"
NAME = "sklearn-tabular-Gubeev"
BASE_ID = "77ab3b41f30a48a7b4da01a60e705aba"
WINE_ID = "fd4384d1b03242269ec15a584a543499"
IRIS_FEATURES_ID = "23306db43cc441fd8eb27f66502bf1a1"
API_HOST = "https://api.clear.ml"
WORK_DIR = ROOT / ".dvc" / "tmp" / "clearml"

SPECS = {
    "base": {"key": "BASE_ID", "id": BASE_ID, "version": "1.0.0",
             "files": ["iris.csv"], "added": ["iris.csv"], "modified": [],
             "description": "Исходный Iris scikit-learn, без Wine и вычисляемых признаков"},
    "wine": {"key": "WINE_ID", "id": WINE_ID, "version": "1.1.0",
             "files": ["iris.csv", "wine.csv"], "added": ["wine.csv"], "modified": [],
             "description": "К исходному Iris от базы добавлен только Wine"},
    "iris_features": {"key": "IRIS_FEATURES_ID", "id": IRIS_FEATURES_ID, "version": "2.0.0",
                      "files": ["iris.csv"], "added": [], "modified": ["iris.csv"],
                      "description": "Отдельная ветвь от базы: Iris с sepal_area и petal_area, без Wine"},
}
EXPECTED_SHA256 = {
    "base": {"iris.csv": "acb1d0e09be856a27d25798722572591b3ec55df2382354c5f83919f4b61e96b"},
    "wine": {"iris.csv": "acb1d0e09be856a27d25798722572591b3ec55df2382354c5f83919f4b61e96b",
             "wine.csv": "b72adfd45219c12d4af882f76b4c67df0a44922d0bac0f2fd30e4b8d0c97a301"},
    "iris_features": {"iris.csv": "8228a6345ef84c613f21e4dca934ad87fc9d8629db248f215bdaf40bdb83c669"},
}


def setup_sdk(expected_api_host: str = API_HOST, *, fresh_cache: bool = False) -> None:
    """Credentials читаются из пользовательского clearml.conf вне репозитория."""
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    cache = WORK_DIR / "cache" / (run_id if fresh_cache else "default")
    if fresh_cache:
        if cache.exists():
            raise RuntimeError("Новый cache уже существует")
        os.environ["CLEARML_CACHE_DIR"] = str(cache)
    else:
        os.environ.setdefault("CLEARML_CACHE_DIR", str(cache))
    from clearml.backend_api.session import Session
    from clearml.config import get_cache_dir

    # ClearML 1.18 использует pathlib2: сравниваем нормализованные строки путей.
    if fresh_cache and os.path.normcase(os.path.abspath(str(get_cache_dir()))) != os.path.normcase(str(cache.resolve())):
        raise RuntimeError("SDK не использует новый пустой cache")
    if Session.get_api_server_host().rstrip("/") != expected_api_host.rstrip("/"):
        raise RuntimeError("Адрес API в настройке SDK не совпадает с ожидаемым")


def get_dataset(mode: str):
    from clearml import Dataset
    return Dataset.get(dataset_id=SPECS[mode]["id"], only_completed=True)


def inspect_dataset(dataset, mode: str) -> dict:
    """Проверить серверный состав, финализацию и ветвление по точным IDs."""
    from clearml import Task

    spec = SPECS[mode]
    parents = [] if mode == "base" else [BASE_ID]
    graph = dataset.get_dependency_graph()
    if dataset.version != spec["version"] or dataset.name != NAME:
        raise ValueError(f"{mode}: неверное имя или номер версии")
    if graph.get(dataset.id) != parents:
        raise ValueError(f"{mode}: неверные родители: {graph}")
    if mode == "iris_features" and WINE_ID in graph:
        raise ValueError("WINE_ID обнаружен среди предков Iris features")
    files = sorted(dataset.list_files())
    changes = {"added": sorted(dataset.list_added_files()),
               "modified": sorted(dataset.list_modified_files()),
               "removed": sorted(dataset.list_removed_files())}
    if files != spec["files"] or changes != {"added": spec["added"], "modified": spec["modified"], "removed": []}:
        raise ValueError(f"{mode}: неверный состав или изменения: {files}, {changes}")
    task = Task.get_task(task_id=dataset.id)
    status = task.get_status()
    if not dataset.is_final() or status != "completed":
        raise ValueError(f"{mode}: ожидался финализированный Dataset со статусом completed")
    url = task.get_output_log_web_page().replace("/projects/", "/datasets/simple/", 1).removesuffix("/output/log")
    return {"key": spec["key"], "id": dataset.id, "version": dataset.version,
            "parents": parents, "graph": graph, "files": files,
            "changes": changes, "status": status, "dataset_url": url}


def create_version(mode: str, *, existing_id: str | None = None):
    """Создать версию либо продолжить уже начатую, не меняя исходный workspace."""
    from clearml import Dataset

    spec = SPECS[mode]
    parents = [] if mode == "base" else [BASE_ID]
    if existing_id:
        dataset = Dataset.get(dataset_id=existing_id)
    else:
        dataset = Dataset.create(
            dataset_project=PROJECT, dataset_name=NAME, dataset_version=spec["version"],
            parent_datasets=parents or None, description=spec["description"],
            dataset_tags=["practice_3", "Gubeev", mode],
        )
        print(f"{spec['key']}: {dataset.id}", flush=True)
    if dataset.name != NAME or dataset.version != spec["version"] or dataset.get_dependency_graph().get(dataset.id) != parents:
        raise ValueError("Неверная версия или родители Dataset")
    if not dataset.is_final():
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=WORK_DIR) as temporary:
            source = prepare(mode, Path(temporary))
            dataset.add_files(path=str(source))
            dataset.upload()
            if not dataset.finalize():
                raise RuntimeError("Не удалось финализировать Dataset")
    return dataset


def run_creator(mode: str) -> None:
    spec = SPECS[mode]
    parser = argparse.ArgumentParser(description=f"ClearML {spec['version']}: {spec['description']}")
    parser.add_argument("--execute", action="store_true", help="Получить и проверить уже созданную версию")
    parser.add_argument("--expected-api-host", default=API_HOST)
    args = parser.parse_args()
    if not args.execute:
        print(f"{PROJECT} / {NAME}\nVersion {spec['version']}; {spec['key']}={spec['id']}")
        print("Версия уже создана. Для проверки укажите --execute; дубликаты не создаются.")
        return
    setup_sdk(args.expected_api_host)
    dataset = create_version(mode, existing_id=spec["id"])
    result = inspect_dataset(dataset, mode)
    print(f"Version {result['version']}: {result['id']}; status={result['status']}; files={result['files']}")


if __name__ == "__main__":
    run_creator("base")
