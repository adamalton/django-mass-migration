class MemoizedLazyList(list):
    """ A wrapper around a function which provides a list. Allows an instance of this class to be
        passed as if it is the list but delays evaluation of the function until list items are
        accessed or iterated. Unlike Django's `lazy`, the object appears to be a real list, so it
        can be used as `choices`, and the result is memoized for efficiency. As the result is
        memoized, this object is immutable; it should really be a tuple, but we can't set the
        items in a tuple because it's immutable, so it's a list!
    """

    def __init__(self, load_function):
        self._load_function = load_function
        self._loaded = False

    def _load(self):
        if not self._loaded:
            super().extend(list(self._load_function()))
            self._loaded = True

    def __iter__(self):
        self._load()
        return super().__iter__()

    def __getitem__(self, *args):
        self._load()
        return super().__getitem__(*args)

    def __len__(self):
        self._load()
        return super().__len__()

    def append(self, *args):
        raise TypeError("Cannot append to a MemoizedLazyList.")

    def clear(self):
        raise TypeError("Cannot clear a MemoizedLazyList.")

    def extend(self, *args):
        raise TypeError("Cannot extend a MemoizedLazyList.")

    def insert(self, *args):
        raise TypeError("Cannot insert a MemoizedLazyList.")

    def pop(self):
        raise TypeError("Cannot pop a MemoizedLazyList.")

    def remove(self, *args):
        raise TypeError("Cannot remove a MemoizedLazyList.")

    def reverse(self):
        raise TypeError("Cannot reverse a MemoizedLazyList.")

    def sort(self):
        raise TypeError("Cannot sort a MemoizedLazyList.")
