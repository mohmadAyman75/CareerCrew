"""
validate.py  —  SHARED: input checks every agent uses.

A missing key or a wrong type in the state is a bug in OUR code,
so these helpers RAISE a clear error instead of returning a message.
"""


def require_dict(state, function_name: str) -> dict:
    """Raise if the state is not a dict. Return it unchanged."""
    if not isinstance(state, dict):
        raise TypeError(f"{function_name}() needs the state as a dict, got {type(state).__name__}")
    return state


def require(state: dict, key: str, expected_type: type | tuple[type, ...]):
    """Return state[key]. Raise a clear error if it is missing, None, or the wrong type."""
    require_dict(state, "require")

    if state.get(key) is None:
        raise KeyError(f"The state has no '{key}'. Did the step that writes it run first?")

    value = state[key]
    if not isinstance(value, expected_type):
        raise TypeError(
            f"state['{key}'] must be {_type_name(expected_type)}, got {type(value).__name__}"
        )
    return value


def _type_name(expected_type: type | tuple[type, ...]) -> str:
    if isinstance(expected_type, tuple):
        return " or ".join(t.__name__ for t in expected_type)
    return expected_type.__name__
