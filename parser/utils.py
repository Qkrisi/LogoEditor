import struct
import io

ENCODING = "ISO-8859-1"

def readint32(stream: io.BufferedIOBase) -> int:
	return int.from_bytes(stream.read(4), byteorder="little")

def int32bytes(n: int) -> bytes:
	return n.to_bytes(4, byteorder="little")

def readstr(stream: io.BufferedIOBase) -> str:
	s: str = ""
	while (b := stream.read(1)[0]) != 0x22:
		s += chr(b)
	return s

def readfloat64(stream: io.BufferedIOBase) -> float:
	return struct.unpack("<d", stream.read(8))[0]

def float64bytes(n: float) -> bytes:
	return struct.pack("<d", n)

def readint(length: int, stream: io.BufferedIOBase) -> int:
	n: int = 0
	for _ in range(length):
		n *= 10
		n += stream.read(1)[0] - 48
	return n
