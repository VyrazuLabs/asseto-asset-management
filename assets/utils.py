
def grouper(iterable, n):
    # Groups iterable into chunks of size n
    args = [iter(iterable)] * n
    return list(zip_longest(*args, fillvalue=None))

from itertools import zip_longest