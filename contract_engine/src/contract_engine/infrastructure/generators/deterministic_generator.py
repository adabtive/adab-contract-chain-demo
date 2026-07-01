import itertools
import random
import string
from typing import TYPE_CHECKING, Any, cast

from exrex import generate as generate_regex

from contract_engine.domain.contract import Contract
from contract_engine.domain.generation_result import GenerationResult
from contract_engine.domain.seed import Seed
from contract_engine.domain.types import (
    UNSET,
    AnyOfType,
    AnyType,
    ArrayType,
    FieldDefinition,
    FieldType,
    ObjectType,
    OneOfType,
    PrimitiveKind,
    PrimitiveType,
)
from contract_engine.infrastructure.generators.format_generators import FORMAT_GENERATORS
from contract_engine.infrastructure.generators.generation_mode import GenerationMode
from contract_engine.infrastructure.generators.strategies import (
    AnyOfStrategy,
    AnyStrategy,
    ArrayStrategy,
    ObjectStrategy,
    OneOfStrategy,
    PrimitiveStrategy,
)

if TYPE_CHECKING:
    from contract_engine.infrastructure.generators.strategies.generation_strategy import GenerationStrategy

DEFAULT_INT_MIN = -10_000
DEFAULT_INT_MAX = 10_000

DEFAULT_ARRAY_MAX = 10
DEFAULT_ARRAY_MIN = 0

DEFAULT_STRING_MAX = 50
DEFAULT_STRING_MIN = 0

MAX_DEPTH = 5


class DeterministicGenerator:
    def __init__(self) -> None:
        self._strategies: dict[type, GenerationStrategy[Any]] = {}
        self._strategies[PrimitiveType] = PrimitiveStrategy()
        self._strategies[ObjectType] = ObjectStrategy()
        self._strategies[ArrayType] = ArrayStrategy()
        self._strategies[OneOfType] = OneOfStrategy()
        self._strategies[AnyOfType] = AnyOfStrategy()
        self._strategies[AnyType] = AnyStrategy()

    def generate(
        self,
        contract: Contract,
        mode: GenerationMode,
        seed: Seed,
    ) -> GenerationResult:
        rng = random.Random(seed.value)  # noqa: S311

        if contract.root_type is not None:
            data = self.generate_field(contract.root_type, rng, mode, depth=0)
            if not isinstance(data, dict):
                raise TypeError(f"Root-level oneOf must resolve to an object, got {type(data).__name__}")
        else:
            data = self._generate_object(contract.fields, rng, mode)

        return GenerationResult(seed=seed, data=data)

    def _generate_object(
        self,
        fields: list[FieldDefinition],
        rng: random.Random,
        mode: GenerationMode,
        depth: int = 0,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for field in fields:
            if not field.required:
                presence_probability = 0.9 if mode == GenerationMode.REALISTIC else 0.5
                if rng.random() > presence_probability:
                    continue

            result[field.name] = self.generate_field(field.type, rng, mode, depth)

        return result

    def generate_field(
        self,
        field_type: FieldType,
        rng: random.Random,
        mode: GenerationMode,
        depth: int,
    ) -> Any:
        if depth >= MAX_DEPTH:
            if isinstance(field_type, ArrayType):
                return []
            if isinstance(field_type, ObjectType):
                return {}

        strategy = self._strategies.get(type(field_type))

        if strategy is None:
            raise TypeError(f"No strategy registered for {type(field_type).__name__}")

        return strategy.generate(field_type, self, rng, mode, depth)

    def generate_array(
        self,
        field: ArrayType,
        rng: random.Random,
        mode: GenerationMode,
        depth: int,
    ) -> list[Any]:
        minimum = field.min_items if field.min_items is not None else DEFAULT_ARRAY_MIN
        maximum = field.max_items if field.max_items is not None else DEFAULT_ARRAY_MAX

        if mode == GenerationMode.REALISTIC:
            midpoint = (minimum + maximum) // 2
            size = rng.randint(minimum, midpoint)
        else:
            size = self.edge_biased_int(minimum, maximum, rng)

        return [self.generate_field(field.items, rng, mode, depth) for _ in range(size)]

    def generate_primitive(
        self,
        field: PrimitiveType,
        rng: random.Random,
        mode: GenerationMode,
    ) -> Any:
        if mode == GenerationMode.REALISTIC and field.default is not UNSET:
            return field.default

        if field.enum:
            return rng.choice(field.enum)

        match field.kind:
            case PrimitiveKind.INTEGER:
                return self.generate_integer(field, rng, mode)

            case PrimitiveKind.NUMBER:
                return self.generate_number(field, rng, mode)

            case PrimitiveKind.STRING:
                return self.generate_string(field, rng, mode)

            case PrimitiveKind.BOOLEAN:
                return rng.choice([True, False])

            case _:
                raise TypeError(f"Unsupported primitive kind: {field.kind}")

    def generate_integer(
        self,
        field: PrimitiveType,
        rng: random.Random,
        mode: GenerationMode,
    ) -> int:
        minimum = int(field.minimum) if field.minimum is not None else DEFAULT_INT_MIN
        maximum = int(field.maximum) if field.maximum is not None else DEFAULT_INT_MAX

        if mode == GenerationMode.REALISTIC:
            midpoint = (minimum + maximum) // 2
            spread = max((maximum - minimum) // 4, 1)

            low = max(minimum, midpoint - spread)
            high = min(maximum, midpoint + spread)

            return rng.randint(low, high)

        return self.edge_biased_int(minimum, maximum, rng)

    def _ensure_non_integer(
        self,
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:
        if not float(value).is_integer():
            return value

        # try nudging up
        if value + 0.1 <= maximum:
            return value + 0.1

        # otherwise nudge down
        if value - 0.1 >= minimum:
            return value - 0.1

        # fallback (very tight range, e.g. min=max=int)
        # in this case, we cannot avoid integer → return as-is
        return value

    def generate_number(
        self,
        field: PrimitiveType,
        rng: random.Random,
        mode: GenerationMode,
    ) -> float:
        minimum = float(field.minimum) if field.minimum is not None else -1e6
        maximum = float(field.maximum) if field.maximum is not None else 1e6

        value = rng.uniform(minimum, maximum)
        value = self._ensure_non_integer(value, minimum, maximum)

        # ensure it's not an integer to avoid overlaps in branches for oneOfTypes
        if float(value).is_integer():
            value += 0.1

        if mode == GenerationMode.REALISTIC:
            return round(value, 2)

        edge_value = self.edge_biased_float(minimum, maximum, rng)
        return self._ensure_non_integer(edge_value, minimum, maximum)

    def generate_string(
        self,
        field: PrimitiveType,
        rng: random.Random,
        mode: GenerationMode,
    ) -> str:
        alphabet = string.ascii_letters

        min_len = field.min_length if field.min_length is not None else DEFAULT_STRING_MIN

        if field.max_length is not None:
            max_len = field.max_length
        elif mode == GenerationMode.REALISTIC:
            max_len = 12
        else:
            max_len = DEFAULT_STRING_MAX

        if max_len < min_len:
            raise ValueError("max_length must be >= min_length")

        if field.format:
            fmt_generator = FORMAT_GENERATORS.get(field.format)

            if fmt_generator is not None:
                return fmt_generator(rng, field)

        if field.pattern:
            limits = [50, 200, 1000]

            for limit in limits:
                candidates = list(itertools.islice(cast("str", generate_regex(field.pattern)), limit))

                filtered = [c for c in candidates if min_len <= len(c) <= max_len]

                if filtered:
                    return rng.choice(filtered)

            raise ValueError(
                f"Cannot generate value satisfying pattern '{field.pattern}' with length [{min_len}, {max_len}]"
            )
        if mode == GenerationMode.FUZZ:
            length = self.edge_biased_int(min_len, max_len, rng)
        else:
            length = rng.randint(min_len, max_len)

        return "".join(rng.choice(alphabet) for _ in range(length))

    def edge_biased_int(
        self,
        minimum: int,
        maximum: int,
        rng: random.Random,
    ) -> int:
        candidates = self.edge_biased_int_candidates(minimum, maximum)
        return rng.choice(candidates)

    def edge_biased_int_candidates(
        self,
        minimum: int,
        maximum: int,
    ) -> list[int]:
        midpoint = (minimum + maximum) // 2

        candidates = {
            minimum,
            maximum,
            midpoint,
            minimum + 1,
            maximum - 1,
        }

        return [v for v in candidates if minimum <= v <= maximum]

    def edge_biased_float(
        self,
        minimum: float,
        maximum: float,
        rng: random.Random,
    ) -> float:
        candidates = self.edge_biased_float_candidates(minimum, maximum, rng)
        return rng.choice(candidates)

    def edge_biased_float_candidates(
        self,
        minimum: float,
        maximum: float,
        rng: random.Random,
    ) -> list[float]:

        midpoint = (minimum + maximum) / 2

        candidates = {
            minimum,
            maximum,
            midpoint,
            0.0,
            rng.uniform(minimum, maximum),
        }

        return [v for v in candidates if minimum <= v <= maximum]

    def _generate_from_pattern(
        self,
        pattern: str,
        rng: random.Random,
        limit: int = 20,
    ) -> str:
        candidates = list(cast("str", generate_regex(pattern, limit=limit)))

        if not candidates:
            return ""

        return rng.choice(candidates)
