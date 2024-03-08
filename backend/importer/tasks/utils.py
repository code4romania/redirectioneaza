def batch(iterable, batch_size=1) -> iter:
    batch_length: int = len(iterable)
    for index in range(0, batch_length, batch_size):
        yield iterable[index : min(index + batch_size, batch_length)]
