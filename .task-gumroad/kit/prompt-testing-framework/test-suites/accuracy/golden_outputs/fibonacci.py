def fibonacci(n: int) -> int:
    """Return the nth fibonacci number (0-indexed).

    fibonacci(0) = 0
    fibonacci(1) = 1
    fibonacci(2) = 1
    fibonacci(7) = 13
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    if n == 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
