"""
Storage & Database Simulation Engine (SQLite PRAGMAs, tdata Binary Serialization).
"""

import struct
from typing import Dict, Any, Optional


class SQLiteStorageMock:
    """Simulates Telegram Desktop SQLite storage engine and PRAGMA configurations."""

    def __init__(self):
        self.pragmas: Dict[str, Any] = {
            "journal_mode": "DELETE",
            "mmap_size": 0,
            "synchronous": "FULL",
            "cache_size": -2000,
            "temp_store": "DEFAULT",
        }
        self.is_open: bool = False
        self.wal_enabled: bool = False

    def initialize_database(self, enable_optimizations: bool = True) -> None:
        """Initializes database and applies C1 PRAGMA optimizations if enabled."""
        self.is_open = True
        if enable_optimizations:
            self.execute_pragma("journal_mode", "WAL")
            self.execute_pragma("mmap_size", 268435456)  # 256 MB
            self.execute_pragma("synchronous", "NORMAL")
            self.execute_pragma("cache_size", -64000)  # 64 MB
            self.execute_pragma("temp_store", "MEMORY")
            self.wal_enabled = True

    def execute_pragma(self, key: str, value: Any) -> None:
        self.pragmas[key.lower()] = value

    def get_pragma(self, key: str) -> Any:
        return self.pragmas.get(key.lower())


class TdataStreamMock:
    """Simulates sequential binary QDataStream serialization for Core::Settings."""

    def __init__(self):
        self.buffer = bytearray()
        self.read_offset = 0

    def write_int32(self, val: int) -> None:
        self.buffer.extend(struct.pack(">i", int(val)))

    def write_bool(self, val: bool) -> None:
        self.buffer.extend(struct.pack(">i", 1 if val else 0))

    def write_string(self, val: str) -> None:
        b = val.encode("utf-8")
        self.write_int32(len(b))
        self.buffer.extend(b)

    def at_end(self) -> bool:
        return self.read_offset >= len(self.buffer)

    def read_int32(self) -> int:
        if self.read_offset + 4 > len(self.buffer):
            raise EOFError("QDataStream read past end")
        val = struct.unpack(">i", self.buffer[self.read_offset : self.read_offset + 4])[0]
        self.read_offset += 4
        return val

    def read_bool(self) -> bool:
        return bool(self.read_int32() != 0)

    def read_string(self) -> str:
        length = self.read_int32()
        if self.read_offset + length > len(self.buffer):
            raise EOFError("QDataStream string read past end")
        b = self.buffer[self.read_offset : self.read_offset + length]
        self.read_offset += length
        return b.decode("utf-8")


class CoreSettingsMock:
    """Mock for Core::Settings serialization and ghostMode persistence."""

    def __init__(self):
        self._ghost_mode: bool = False
        self._window_width: int = 1024
        self._window_height: int = 768

    @property
    def ghost_mode(self) -> bool:
        return self._ghost_mode

    def set_ghost_mode(self, enabled: bool) -> None:
        self._ghost_mode = enabled

    def serialize(self, stream: TdataStreamMock) -> None:
        """Sequential binary serialization with ghostMode appended at the end."""
        stream.write_int32(self._window_width)
        stream.write_int32(self._window_height)
        # Append-at-end rule
        stream.write_bool(self._ghost_mode)

    def deserialize(self, stream: TdataStreamMock) -> None:
        """Deserialization with stream.atEnd() guard for backwards compatibility."""
        self._window_width = stream.read_int32()
        self._window_height = stream.read_int32()

        # Guarded read for new fields
        if not stream.at_end():
            self._ghost_mode = stream.read_bool()
        else:
            self._ghost_mode = False  # Safe legacy fallback
