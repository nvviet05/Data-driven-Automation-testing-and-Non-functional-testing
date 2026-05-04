def text_equals(expected, actual) -> bool:
    if expected is None or actual is None:
        return False
    return str(expected).strip() == str(actual).strip()


def text_contains(expected, actual) -> bool:
    if expected is None or actual is None:
        return False
    return str(expected).strip() in str(actual)
