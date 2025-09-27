from typing import Literal, Any

FilterKey = Literal["lt", "lte", "gt", "gte", "eq", "in"]


class _FilterKey:
    def __init__(self, name: str):
        self.name = name
        self.callback = None
        self.filter: FilterKey = None
        self.value: Any = None

    def bind(self, callback):
        self.callback = callback
        self.update()
        return self

    def __eq__(self, other):
        self.filter = "eq"
        self.value = other
        self.update()
        return True

    def __lt__(self, other):
        self.filter = "lt"
        self.value = other
        self.update()
        return True

    def __le__(self, other):
        self.filter = "lte"
        self.value = other
        self.update()
        return True

    def __gt__(self, other):
        self.filter = "gt"
        self.value = other
        self.update()
        return True

    def __ge__(self, other):
        self.filter = "gte"
        self.value = other
        self.update()
        return True

    def __xor__(self, other):
        return self.isin(other)

    def isin(self, other):
        self.filter = "in"
        self.value = other
        self.update()
        return True

    def update(self):
        if (
            self.callback is not None
            and self.filter is not None
            and self.value is not None
        ):
            self.callback(self)


class Filter:
    def __init__(self):
        self._data = {}

    def __getitem__(self, name):
        key = _FilterKey(name).bind(self._on_value_set)
        return key

    def __setitem__(self, name, value):
        key = _FilterKey(name).bind(self._on_value_set)
        key == value

    def _on_value_set(self, filter_key: _FilterKey):
        self._data[filter_key.name] = (filter_key.filter, filter_key.value)

    def format_for_param(self) -> str:
        return ",".join(
            f"{key}:{op}:{self._format_value(value)}"
            for key, (op, value) in self._data.items()
        )

    @staticmethod
    def _format_value(value) -> str:
        if isinstance(value, (list, tuple)):
            return "(" + ",".join(map(str, value)) + ")"
        return str(value)
