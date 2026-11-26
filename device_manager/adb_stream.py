from collections.abc import Iterator
from typing import Any


class AdbStreamProcess:
    """Popen-like streaming wrapper around an `adbutils.AdbConnection` socket."""

    def __init__(
        self,
        connection: Any,
        *,
        command: str,
        encoding: str | None = 'utf-8',
    ) -> None:
        self._connection = connection
        self._command = command
        self._encoding = encoding
        self._closed = False

    @property
    def command(self) -> str:
        """The ADB shell command associated with this stream."""
        return self._command

    @property
    def is_open(self) -> bool:
        """Whether the underlying stream connection is still open."""
        return not self._closed

    def iter_lines(self) -> Iterator[str]:
        """Yield decoded text lines from the stream until EOF or close."""
        encoding = self._encoding or 'utf-8'
        with self._connection.conn.makefile(
            'r',
            encoding=encoding,
            errors='replace',
        ) as reader:
            for line in reader:
                if self._closed:
                    break
                yield line.rstrip('\r\n')

    def read_chunks(self, chunk_size: int = 4096) -> Iterator[bytes]:
        """Yield raw byte chunks from the stream (e.g. for binary streams)."""
        while not self._closed:
            chunk = self._connection.conn.recv(chunk_size)
            if not chunk:
                break
            yield chunk

    def close(self) -> None:
        """Close the underlying `adbutils` stream connection (idempotent)."""
        if not self._closed:
            self._closed = True
            self._connection.close()

    def terminate(self) -> None:
        """Alias for `close()`, mirroring `subprocess.Popen.terminate()`."""
        self.close()

    def __enter__(self) -> 'AdbStreamProcess':
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
