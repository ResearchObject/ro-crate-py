from io import BytesIO


class MemoryBuffer(BytesIO):
    """ Memory buffer provides a writable stream that can be read back.
    Automatically resets after reading. """
    def __init__(self):
        super().__init__()
        self._buffer = b""

    def writable(self):
        return True

    def write(self, b):
        if self.closed:
            raise RuntimeError("Stream was closed before writing!")
        self._buffer += b
        return len(b)

    def read(self, **kwargs):
        chunk = self._buffer
        self._buffer = b""
        return chunk
