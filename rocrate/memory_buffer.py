from io import RawIOBase


class MemoryBuffer(RawIOBase):
    """
    A buffer class that supports reading and writing binary data.
    The buffer automatically resets upon reading to make sure all data is read only once.
    """

    def __init__(self):
        self._buffer = b''

    def write(self, data):
        if self.closed:
            raise ValueError('write to closed file')
        self._buffer += data
        return len(data)

    def read(self, size=-1):
        if self.closed:
            raise ValueError('read from closed file')
        if size < 0:
            data = self._buffer
            self._buffer = b''
        else:
            data = self._buffer[:size]
            self._buffer = self._buffer[size:]
        return data
