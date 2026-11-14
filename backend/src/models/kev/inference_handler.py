"""Framework-neutral Kev inference wrapper with per-request latency measurement."""

import importlib
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns
from typing import Any, Callable, Protocol, Sequence


class Predictor(Protocol):
    def predict(self, user_input: str) -> Any: ...


ModelLoader = Callable[[Path], Predictor | Callable[[str], Any]]


@dataclass(frozen=True)
class InferenceResult:
    prediction: Any
    latency_ms: float


def resolve_callable(reference: str) -> Callable[..., Any]:
    module_name, separator, attribute = reference.partition(":")
    if not separator or not module_name or not attribute:
        raise ValueError("Expected a callable reference in 'module:attribute' form.")
    module = importlib.import_module(module_name)
    value = getattr(module, attribute)
    if not callable(value):
        raise TypeError(f"Configured object is not callable: {reference}")
    return value


class InferenceHandler:
    """Run a loaded local model without binding Kev to a specific ML framework."""

    def __init__(self, model: Predictor | Callable[[str], Any]) -> None:
        if not callable(model) and not callable(getattr(model, "predict", None)):
            raise TypeError("Model must be callable or expose a callable predict(input).")
        self._model = model

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: str | Path,
        loader: ModelLoader,
    ) -> "InferenceHandler":
        path = Path(checkpoint_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Kev checkpoint does not exist: {path}")
        return cls(loader(path))

    def predict(self, user_input: str) -> InferenceResult:
        if not isinstance(user_input, str) or not user_input.strip():
            raise ValueError("Inference input must be a non-empty string.")
        start = perf_counter_ns()
        predict = getattr(self._model, "predict", None)
        prediction = predict(user_input) if callable(predict) else self._model(user_input)
        latency_ms = (perf_counter_ns() - start) / 1_000_000
        return InferenceResult(prediction=prediction, latency_ms=latency_ms)

    def benchmark(
        self,
        user_inputs: Sequence[str],
        *,
        repetitions: int = 1,
    ) -> list[InferenceResult]:
        if isinstance(user_inputs, str) or not user_inputs:
            raise ValueError("At least one input is required for benchmarking.")
        if repetitions <= 0:
            raise ValueError("Benchmark repetitions must be positive.")
        return [
            self.predict(user_input)
            for _ in range(repetitions)
            for user_input in user_inputs
        ]
