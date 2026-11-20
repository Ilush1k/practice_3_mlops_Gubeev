"""Сравнение моделей Wine, проверка сохранения и экспорт результата в ClearML."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from time import perf_counter
import uuid
from importlib.metadata import version

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient
from mlflow.models import Model, infer_signature
import numpy as np
import pandas as pd
from clearml import Dataset
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
METRICS = ("accuracy", "precision_weighted", "recall_weighted", "f1_weighted")
EXPERIMENT_NAME = "miit-mlops-practice-4-Gubeev"


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_wine(dataset_id: str, expected_sha256: str) -> tuple[pd.DataFrame, str]:
    dataset = Dataset.get(dataset_id=dataset_id, only_completed=True)
    if not dataset.is_final():
        raise ValueError("ClearML Dataset должен быть финализирован")
    path = Path(dataset.get_local_copy()) / "wine.csv"
    actual = sha256_file(path)
    if actual != expected_sha256.lower():
        raise ValueError(f"SHA-256 Wine не совпадает: ожидался {expected_sha256}, получен {actual}")
    frame = pd.read_csv(path)
    if "target" not in frame or len(frame) != 178 or frame.shape[1] != 14:
        raise ValueError("Ожидался Wine: 178 строк, 13 признаков и target")
    if frame.isna().any().any() or sorted(frame["target"].unique().tolist()) != [0, 1, 2]:
        raise ValueError("Wine содержит пропуски или неожиданные классы")
    return frame, actual


def split_data(frame: pd.DataFrame, seed: int) -> tuple[dict, dict]:
    X, y = frame.drop(columns="target"), frame["target"]
    X_remain, X_test, y_remain, y_test = train_test_split(
        X, y, test_size=0.20, random_state=seed, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_remain, y_remain, test_size=0.25, random_state=seed, stratify=y_remain
    )
    data = dict(X_train=X_train, X_val=X_val, X_test=X_test,
                y_train=y_train, y_val=y_val, y_test=y_test)
    description = {
        "random_state": seed,
        "requested_fractions": {"train": 0.6, "validation": 0.2, "test": 0.2},
        "rows": {"train": len(y_train), "validation": len(y_val), "test": len(y_test)},
        "indices": {"train": X_train.index.tolist(), "validation": X_val.index.tolist(),
                    "test": X_test.index.tolist()},
        "class_counts": {name: {str(k): int(v) for k, v in target.value_counts().sort_index().items()}
                         for name, target in [("train", y_train), ("validation", y_val), ("test", y_test)]},
        "feature_columns": X.columns.tolist(),
    }
    description["sha256"] = hashlib.sha256(
        json.dumps(description, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return data, description


def configurations(seed: int) -> list[dict]:
    result = []
    for c_value in [0.1, 1.0, 10.0]:
        result.append({
            "name": f"logreg-c-{c_value:g}", "family": "logistic_regression",
            "model": Pipeline([("scaler", StandardScaler()), ("classifier", LogisticRegression(
                C=c_value, solver="lbfgs", max_iter=1000, random_state=seed
            ))]),
        })
    for depth, trees in [(3, 100), (6, 100), (None, 200)]:
        result.append({
            "name": f"rf-depth-{depth if depth is not None else 'unlimited'}",
            "family": "random_forest",
            "model": Pipeline([("classifier", RandomForestClassifier(
                n_estimators=trees, max_depth=depth, random_state=seed, n_jobs=1
            ))]),
        })
    return result


def classification_metrics(target, predictions) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(target, predictions)),
        "precision_weighted": float(precision_score(target, predictions, average="weighted", zero_division=0)),
        "recall_weighted": float(recall_score(target, predictions, average="weighted", zero_division=0)),
        "f1_weighted": float(f1_score(target, predictions, average="weighted", zero_division=0)),
    }


def inspect_runs(client: MlflowClient, run_ids: list[str], dataset_id: str,
                 dataset_sha256: str, split_sha256: str) -> list[dict]:
    """Ошибка при отсутствии обязательных полей, signature или сохранённой модели."""
    if len(run_ids) != 6 or len(set(run_ids)) != 6:
        raise RuntimeError("Ожидались шесть разных MLflow runs")
    checks = []
    for run_id in run_ids:
        run = client.get_run(run_id)
        params, metrics, tags = run.data.params, run.data.metrics, run.data.tags
        family = tags.get("model_family")
        required = {"model_type", "random_state"}
        if family == "logistic_regression":
            required |= {"C", "solver", "max_iter"}
        elif family == "random_forest":
            required |= {"n_estimators", "max_depth"}
        else:
            raise RuntimeError(f"Неизвестное семейство модели в {run_id}")
        if run.info.status != "FINISHED" or not required <= params.keys():
            raise RuntimeError(f"Run {run_id}: неверный статус или неполные параметры")
        if not set(METRICS + ("training_seconds",)) <= metrics.keys():
            raise RuntimeError(f"Run {run_id}: неполный набор метрик")
        if not all(np.isfinite(metrics[name]) for name in METRICS + ("training_seconds",)):
            raise RuntimeError(f"Run {run_id}: нечисловые метрики")
        for key, expected in [("dataset_id", dataset_id), ("dataset_sha256", dataset_sha256),
                              ("split_sha256", split_sha256)]:
            if tags.get(key) != expected:
                raise RuntimeError(f"Run {run_id}: неверный тег {key}")
        model_uri = f"runs:/{run_id}/model"
        model_dir = Path(mlflow.artifacts.download_artifacts(artifact_uri=model_uri))
        metadata = Model.load(str(model_dir))
        if metadata.signature is None or not metadata.signature.inputs or not metadata.signature.outputs:
            raise RuntimeError(f"Run {run_id}: отсутствует signature")
        example_info = metadata.saved_input_example_info
        if not example_info:
            raise RuntimeError(f"Run {run_id}: отсутствует input example")
        example = json.loads((model_dir / example_info["artifact_path"]).read_text(encoding="utf-8"))
        if len(example.get("data", [])) != 5:
            raise RuntimeError(f"Run {run_id}: input example должен содержать пять строк")
        if not (model_dir / metadata.flavors["sklearn"]["pickled_model"]).is_file():
            raise RuntimeError(f"Run {run_id}: отсутствует файл модели")
        checks.append({"run_id": run_id, "status": run.info.status, "model_family": family,
                       "required_params": True, "required_metrics": True, "provenance_tags": True,
                       "signature": True, "input_example_rows": 5, "model_file": True})
    if [c["model_family"] for c in checks].count("logistic_regression") != 3:
        raise RuntimeError("Ожидались три Logistic Regression и три Random Forest")
    return checks


def export_clearml(verification: dict, model_path: Path, output: Path, verification_path: Path,
                   project: str, make_public: bool) -> dict:
    from clearml import Model as ClearMLModel, OutputModel, Task

    task = Task.init(
        project_name=project, task_name="wine-best-model", reuse_last_task_id=False,
        output_uri=True, auto_connect_frameworks=False, auto_connect_arg_parser=False,
        auto_resource_monitoring=False,
    )
    try:
        task.add_tags(["practice_4", verification["session_id"]])
        task.connect(verification["best_params"], name="model")
        task.connect({key: verification[key] for key in [
            "experiment_id", "best_run_id", "dataset_id", "dataset_sha256", "session_id", "split_sha256"
        ]}, name="provenance")
        logger = task.get_logger()
        for prefix, values in [("validation", verification["validation_metrics"]),
                               ("test", verification["test_metrics"])]:
            for name, value in values.items():
                logger.report_single_value(f"{prefix}_{name}", value)
        model = OutputModel(task=task, framework="scikit-learn", name="wine-best-model")
        model.update_labels({f"class_{i}": i for i in [0, 1, 2]})
        for key, value in {
            "mlflow_run_id": verification["best_run_id"], "dataset_id": verification["dataset_id"],
            "dataset_sha256": verification["dataset_sha256"], "session_id": verification["session_id"],
            "model_sha256": sha256_file(model_path),
        }.items():
            model.set_metadata(key=key, value=value, v_type="str")
        model.update_weights(weights_filename=str(model_path), auto_delete_file=False, async_enable=False)
        remote_model = ClearMLModel(model_id=model.id)
        downloaded = Path(remote_model.get_weights(raise_on_error=True, force_download=True))
        if sha256_file(downloaded) != sha256_file(model_path):
            raise RuntimeError("Файл модели, скачанный из ClearML, имеет другой SHA-256")
        model.publish()
        remote_model = ClearMLModel(model_id=model.id)
        if not remote_model.published:
            raise RuntimeError("ClearML OutputModel не опубликован")
        shared_ids = []
        if make_public:
            from clearml.backend_api.session.client import APIClient
            api = APIClient()
            source = Dataset.get(dataset_id=verification["dataset_id"], only_completed=True)
            shared_ids = sorted(source.get_dependency_graph())
            api.tasks.make_public(ids=[task.id, *shared_ids])
            api.models.make_public(ids=[model.id])
        result = {
            "task_id": task.id, "model_id": model.id, "published": True,
            "model_download_sha256_matches": True, "public_requested": make_public,
            "shared_dataset_ids": shared_ids,
            "task_url": task.get_output_log_web_page().removesuffix("/output/log"),
            "model_url": task.get_output_log_web_page().split("/experiments/", 1)[0] + f"/models/{model.id}",
        }
        verification["clearml"] = result
        save_json(verification_path, verification)
        for name, path in {
            "verification": verification_path, "comparison": output / "comparison.csv",
            "model_file": model_path, "split": output / "split.json",
            "classification_report": output / "classification_report.json",
            "confusion_matrix": output / "confusion_matrix.png",
            "environment": output / "environment.json",
        }.items():
            if not task.upload_artifact(name, artifact_object=str(path), wait_on_upload=True):
                raise RuntimeError(f"Не удалось загрузить ClearML artifact {name}")
        task.flush(wait_for_uploads=True)
        task.close()
        checked = Task.get_task(task_id=result["task_id"])
        if checked.get_status() != "completed":
            raise RuntimeError("ClearML Task не имеет статус completed")
        expected_artifacts = {"verification", "comparison", "model_file", "split", "classification_report", "confusion_matrix", "environment"}
        if not expected_artifacts <= checked.artifacts.keys():
            raise RuntimeError("ClearML Task содержит не все обязательные artifacts")
        result["task_status"] = "completed"
        result["artifacts_verified"] = True
        return result
    except Exception:
        task.mark_failed(status_reason="Ошибка проверки или экспорта результата", force=True)
        task.close()
        raise


def update_report(verification: dict, comparison: pd.DataFrame) -> None:
    path = ROOT / "REPORT.md"
    text = path.read_text(encoding="utf-8").split("\n## Эксперименты", 1)[0].rstrip()
    v = verification
    lines = ["", "## Эксперименты", "",
             "Wine получен из финализированной версии ClearML Dataset. Перед обучением проверен SHA-256 CSV. Все шесть конфигураций используют один стратифицированный split: 106 строк train, 36 validation и 36 test, random_state=42. Индексы строк и состав классов сохранены в split.json.", "",
             f"- Dataset ID: `{v['dataset_id']}`.", f"- SHA-256 Wine: `{v['dataset_sha256']}`.",
             f"- Tracking URI: `{v['tracking_uri']}`.", f"- Experiment: `{v['experiment_name']}`, ID `{v['experiment_id']}`.",
             f"- Серия запусков: `{v['session_id']}`.", f"- SHA-256 split: `{v['split_sha256']}`.", "",
             "| Компонент | Версия |", "|---|---|"]
    lines += [f"| {name} | {value} |" for name, value in v["environment"].items()]
    lines += ["", "### Сравнение конфигураций", "",
              "| Run | Run ID | Семейство | Параметры | Validation F1 | Время обучения, с |",
              "|---|---|---|---|---:|---:|"]
    for row in comparison.to_dict("records"):
        lines.append(f"| {row['run_name']} | `{row['run_id']}` | {row['model_family']} | `{row['parameters']}` | {row['f1_weighted']:.6f} | {row['training_seconds']:.6f} |")
    lines += ["", f"Выбрана конфигурация **{v['best_run_name']}**: максимальный validation F1 {v['validation_metrics']['f1_weighted']:.6f}. При равенстве F1 применяется алфавитный порядок имён запусков. Test не использовался при выборе конфигурации.", "",
              f"Лучший MLflow run ID: `{v['best_run_id']}`. Модель загружена по `runs:/{v['best_run_id']}/model`; её предсказания совпали с исходным Pipeline. Проверены обязательные поля всех шести runs, signature и пять строк input example. Результаты сохранены в verification.json.", "",
              "### Итоговая оценка", "", "| Метрика test | Значение |", "|---|---:|"]
    lines += [f"| {name} | {value:.6f} |" for name, value in v["test_metrics"].items()]
    lines += ["", "Метрики test вычислены один раз после выбора победителя и записаны только в его run с префиксом test_. Матрица ошибок, предсказания и показатели по классам сохранены как MLflow artifacts.", ""]
    if v.get("clearml"):
        c = v["clearml"]
        lines += ["### Результат в ClearML", "",
                  f"- Task: [{c['task_id']}]({c['task_url']}), статус `{c['task_status']}`.",
                  f"- Model: [{c['model_id']}]({c['model_url']}), опубликована.",
                  "- В Task загружены параметры победителя, validation/test-метрики, таблица сравнения, verification.json, модель, split, окружение и матрица ошибок.",
                  "- Метаданные модели содержат MLflow run ID, Dataset ID и хэши. Файл модели повторно скачан из ClearML, SHA-256 совпал с локальным.",
                  f"- Публичный доступ к Task, модели и исходным версиям данных: {'запрошен через API ClearML' if c['public_requested'] else 'не включался'}.", ""]
    lines += ["### Воспроизведение", "", "```powershell", "poetry install", "clearml-init",
              "poetry run python run_experiments.py `",
              f"  --dataset-id {v['dataset_id']} `", f"  --expected-sha256 {v['dataset_sha256']} `",
              "  --tracking-uri http://127.0.0.1:8081 --clearml --public --update-report", "```", "",
              "Перед запуском HTTP-варианта нужно поднять MLflow Tracking Server по команде из README. Для работы без сервера можно передать --tracking-uri sqlite:///mlflow.db. Повторное выполнение создаёт новую серию из шести runs в том же experiment.", "",
              "### Дополнительные проверки", "",
              "Автоматические тесты проверяют структуру записанных runs и изоляцию test-метрик. Сохранены confusion_matrix.png и classification_report.json. Tracking Server использует SQLite для метаданных и отдельное файловое хранилище артефактов.", "",
              f"В этой серии время обучения составило от {comparison['training_seconds'].min():.6f} до {comparison['training_seconds'].max():.6f} с. Эти измерения относятся к одному запуску на данном компьютере; небольшую разницу времени нельзя считать устойчивым преимуществом. Качество сравнивалось по validation F1, скорость приведена отдельно.", ""]
    path.write_text(text + "\n" + "\n".join(lines), encoding="utf-8", newline="\n")


def run(args: argparse.Namespace) -> dict:
    frame, dataset_sha256 = load_wine(args.dataset_id, args.expected_sha256)
    data, split = split_data(frame, args.random_state)
    session_id = uuid.uuid4().hex[:16]
    output = args.output_dir.resolve() / session_id
    output.mkdir(parents=True, exist_ok=False)
    save_json(output / "split.json", split)
    environment = {"Python": sys.version.split()[0], **{
        name: version(name) for name in ["mlflow", "clearml", "scikit-learn", "pandas", "numpy", "scipy", "joblib", "matplotlib"]
    }}
    save_json(output / "environment.json", environment)
    mlflow.set_tracking_uri(args.tracking_uri)
    experiment = mlflow.set_experiment(args.experiment_name)
    experiment_id = experiment.experiment_id
    client = MlflowClient()
    trained, run_ids = {}, []
    source_sha256 = sha256_file(Path(__file__).resolve())
    for config in configurations(args.random_state):
        model = config["model"]
        params = model.named_steps["classifier"].get_params()
        params["model_type"] = type(model.named_steps["classifier"]).__name__
        with mlflow.start_run(experiment_id=experiment_id, run_name=config["name"], tags={
            "session_id": session_id, "model_family": config["family"], "dataset_id": args.dataset_id,
            "dataset_sha256": dataset_sha256, "split_sha256": split["sha256"], "code_sha256": source_sha256,
        }) as active:
            mlflow.log_params(params)
            started = perf_counter()
            model.fit(data["X_train"], data["y_train"])
            duration = perf_counter() - started
            metrics = classification_metrics(data["y_val"], model.predict(data["X_val"]))
            mlflow.log_metrics({**metrics, "training_seconds": duration})
            mlflow.sklearn.log_model(sk_model=model, name="model", serialization_format="skops",
                skops_trusted_types=["sklearn.tree._tree.Tree"] if config["family"] == "random_forest" else [],
                signature=infer_signature(data["X_train"], model.predict(data["X_train"])),
                input_example=data["X_train"].iloc[:5])
            mlflow.log_artifact(str(output / "split.json"), artifact_path="data")
            mlflow.log_artifact(str(output / "environment.json"), artifact_path="environment")
            run_id = active.info.run_id
        trained[run_id] = model
        run_ids.append(run_id)
        print(f"{config['name']}: validation F1={metrics['f1_weighted']:.6f}; run={run_id}", flush=True)
    run_checks = inspect_runs(client, run_ids, args.dataset_id, dataset_sha256, split["sha256"])
    runs = mlflow.search_runs(experiment_ids=[experiment_id],
        filter_string=f"tags.session_id = '{session_id}'", order_by=["metrics.f1_weighted DESC"])
    if set(runs["run_id"]) != set(run_ids):
        raise RuntimeError("Таблица сравнения не совпадает с текущей серией из шести runs")
    runs = runs.sort_values(["metrics.f1_weighted", "tags.mlflow.runName"], ascending=[False, True], kind="mergesort")
    rows = []
    for row in runs.to_dict("records"):
        family = row["tags.model_family"]
        keys = ["C", "solver", "max_iter", "random_state"] if family == "logistic_regression" else ["n_estimators", "max_depth", "random_state"]
        rows.append({"run_id": row["run_id"], "run_name": row["tags.mlflow.runName"], "model_family": family,
            "parameters": ", ".join(f"{key}={row['params.' + key]}" for key in keys),
            **{name: float(row["metrics." + name]) for name in METRICS},
            "training_seconds": float(row["metrics.training_seconds"])})
    comparison = pd.DataFrame(rows)
    comparison.to_csv(output / "comparison.csv", index=False)
    best_run_id = str(comparison.iloc[0]["run_id"])
    model_uri = f"runs:/{best_run_id}/model"
    loaded = mlflow.sklearn.load_model(model_uri)
    original_predictions = trained[best_run_id].predict(data["X_test"])
    loaded_predictions = loaded.predict(data["X_test"])
    if not np.array_equal(original_predictions, loaded_predictions):
        raise RuntimeError("Предсказания исходной и загруженной модели различаются")
    # Test оценивается только после окончательного выбора конфигурации.
    test_metrics = classification_metrics(data["y_test"], loaded_predictions)
    per_class = classification_report(data["y_test"], loaded_predictions,
        labels=[0, 1, 2], target_names=["class_0", "class_1", "class_2"], output_dict=True, zero_division=0)
    save_json(output / "classification_report.json", per_class)
    matrix = confusion_matrix(data["y_test"], loaded_predictions, labels=[0, 1, 2])
    figure, axis = plt.subplots(figsize=(5, 4))
    ConfusionMatrixDisplay(matrix, display_labels=["class_0", "class_1", "class_2"]).plot(ax=axis, colorbar=False)
    axis.set_title("Wine: test confusion matrix")
    figure.tight_layout()
    figure.savefig(output / "confusion_matrix.png", dpi=160)
    plt.close(figure)
    pd.DataFrame({"row_index": data["X_test"].index, "target": data["y_test"].to_numpy(),
                  "prediction": loaded_predictions}).to_csv(output / "test_predictions.csv", index=False)
    model_path = output / "best_model.joblib"
    joblib.dump(loaded, model_path)
    best = client.get_run(best_run_id)
    verification = {
        "status": "passed", "experiment_name": args.experiment_name, "experiment_id": experiment_id,
        "tracking_uri": args.tracking_uri, "session_id": session_id, "dataset_id": args.dataset_id,
        "dataset_sha256": dataset_sha256, "split_sha256": split["sha256"], "split": split,
        "code_sha256": source_sha256, "environment": environment, "run_ids": run_ids,
        "best_run_id": best_run_id, "best_run_name": str(comparison.iloc[0]["run_name"]),
        "model_uri": model_uri, "best_params": best.data.params,
        "validation_metrics": {name: best.data.metrics[name] for name in METRICS},
        "test_metrics": test_metrics, "test_metric_evaluations": 1,
        "predictions_match": True, "test_original_columns_accepted": True,
        "run_checks": run_checks, "output_dir": str(output),
    }
    with mlflow.start_run(run_id=best_run_id):
        mlflow.log_metrics({"test_" + key: value for key, value in test_metrics.items()})
        for name in ["comparison.csv", "classification_report.json", "confusion_matrix.png", "test_predictions.csv", "best_model.joblib"]:
            mlflow.log_artifact(str(output / name), artifact_path="evaluation")
    for run_id in run_ids:
        names = {name for name in client.get_run(run_id).data.metrics if name.startswith("test_")}
        expected = {"test_" + name for name in METRICS} if run_id == best_run_id else set()
        if names != expected:
            raise RuntimeError("Test-метрики должны находиться только в выбранном run")
    save_json(args.verification_file, verification)
    if args.clearml:
        verification["clearml"] = export_clearml(verification, model_path, output,
            args.verification_file, args.clearml_project, args.public)
    save_json(args.verification_file, verification)
    save_json(output / "verification.json", verification)
    with mlflow.start_run(run_id=best_run_id):
        mlflow.log_artifact(str(args.verification_file.resolve()), artifact_path="verification")
        if verification.get("clearml"):
            mlflow.set_tags({"clearml_task_id": verification["clearml"]["task_id"],
                             "clearml_model_id": verification["clearml"]["model_id"]})
    if args.update_report:
        update_report(verification, comparison)
    print(comparison.to_string(index=False), flush=True)
    print(f"Experiment ID: {experiment_id}\nBest run ID: {best_run_id}\nTest F1: {test_metrics['f1_weighted']:.6f}", flush=True)
    if verification.get("clearml"):
        print(f"ClearML Task ID: {verification['clearml']['task_id']}\nClearML Model ID: {verification['clearml']['model_id']}", flush=True)
    return verification


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-id", required=True, help="ID версии Wine из практики 3")
    parser.add_argument("--expected-sha256", required=True, help="SHA-256 wine.csv из REPORT.md")
    parser.add_argument("--tracking-uri", default=os.getenv("MLFLOW_TRACKING_URI") or f"sqlite:///{(ROOT / 'mlflow.db').as_posix()}")
    parser.add_argument("--experiment-name", default=EXPERIMENT_NAME)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "practice_4")
    parser.add_argument("--verification-file", type=Path, default=ROOT / "verification.json")
    parser.add_argument("--clearml", action="store_true", help="Экспортировать победителя в ClearML")
    parser.add_argument("--clearml-project", default="MIIT/MLOps/practice_4/Gubeev")
    parser.add_argument("--public", action="store_true", help="Открыть чтение ClearML Task, модели и исходных Dataset для проверки")
    parser.add_argument("--update-report", action="store_true", help="Обновить раздел Эксперименты в REPORT.md")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[0-9a-fA-F]{64}", args.expected_sha256):
        parser.error("--expected-sha256 должен содержать 64 шестнадцатеричных символа")
    if args.public and not args.clearml:
        parser.error("--public используется вместе с --clearml")
    return args


def main() -> int:
    args = parse_args()
    try:
        run(args)
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
