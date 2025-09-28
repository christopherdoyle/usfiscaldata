"""Type casting for fiscal data pandas dataframes."""

import logging
from typing import Protocol

import pandas as pd

logger = logging.getLogger(__name__)


class TypeCaster(Protocol):
    def __call__(self, values: pd.Series, fmt: str) -> pd.Series: ...


TYPE_REGISTRY: dict[str, TypeCaster] = {}


def register(type_name: str):
    if type_name in TYPE_REGISTRY:
        raise ValueError

    def wrapper(fn):
        TYPE_REGISTRY[type_name] = fn
        return fn

    return wrapper


def date_fmt_to_py_fmt(s: str) -> str:
    if s == "YYYY-MM-DD":
        return "%Y-%m-%d"
    else:
        raise NotImplementedError(f"Unknown date format '{s}'")


@register("DATE")
def cast_date(values: pd.Series, fmt: str) -> pd.Series:
    py_fmt = date_fmt_to_py_fmt(fmt)
    return pd.to_datetime(values.replace({"null": pd.NaT}), format=py_fmt)


@register("STRING")
def cast_string(values: pd.Series, fmt: str) -> pd.Series:
    if fmt != "String":
        logger.warning("Unknown data foramt '%s' for '%s'", fmt, values.name)
    return values.replace({"null": ""})


@register("NUMBER")
def cast_number(values: pd.Series, fmt: str) -> pd.Series:
    return pd.to_numeric(values.replace({"null": pd.NA}))


@register("CURRENCY0")
def cast_currency0(values: pd.Series, fmt: str) -> pd.Series:
    return cast_number(values, fmt=fmt)


def cast_df(
    df: pd.DataFrame,
    data_types: dict[str, str],
    data_formats: dict[str, str],
) -> pd.DataFrame:
    result = df.copy()
    for column in df.columns:
        data_type = data_types[column]
        data_format = data_formats[column]
        caster = TYPE_REGISTRY.get(data_type)
        if caster is None:
            logger.warning("Unknown type '%s', failed to cast", data_type)
            continue
        result[column] = caster(df[column], fmt=data_format)
    return result
