from typing import Optional
from PIL import Image, ImageOps
import numpy as np

import parser.utils as utils
import zlib
import io

class LogoImage:
	def __init__(self, startnum: int, activex: int, activey: int, delay: int, bitmap: np.ndarray):
		self.startnum: int = startnum
		self.activex: int = activex
		self.activey: int = activey
		self.delay: int = delay
		self.bitmap: np.ndarray = bitmap
	
	def getachannel(self) -> Image:
		return self.getimage().getchannel("A")
	
	def getimage(self) -> Image:
		return Image.fromarray(self.bitmap, "RGBA")
	
	def get_alpha_bmp(self) -> bytes:
		bitmap = np.copy(self.bitmap)
		bitmap[..., 3] = 255-bitmap[..., 3]
		alpha_mask = bitmap[:, :, 3] == 0
		bitmap[alpha_mask, 0:3] = 255
		img = Image.fromarray(bitmap, "RGBA")
		with io.BytesIO() as stream:
			img.convert("RGB").save(stream, format="BMP")
			return stream.getvalue()
	
	@property
	def bmp32(self) -> bytes:
		img: Image = self.getimage()
		with io.BytesIO() as stream:
			img.save(stream, format="BMP")
			return stream.getvalue()
	
	@property
	def bmp24(self) -> bytes:
		img: Image = self.getimage().convert("RGB")
		with io.BytesIO() as stream:
			img.save(stream, format="BMP")
			return stream.getvalue()
	
	@property
	def hasalpha(self) -> bool:
		return self.getachannel().getextrema()[1] == 255
	
	@property
	def alpha(self) -> Optional[bytes]:
		if not self.hasalpha:
			return None
		achannel: Image = self.getachannel()
		mask: Image = achannel.point(lambda x: 255 if x == 255 else 0).convert("1")
		with io.BytesIO() as stream:
			mask.save(stream, format="BMP")
			return stream.getvalue()
	
	@property
	def height(self) -> int:
		return self.bitmap.shape[0]

	@property
	def width(self) -> int:
		return self.bitmap.shape[1]
	
	def __bytes__(self) -> bytes:
		res: bytearray = bytearray()
		res += utils.int32bytes(self.startnum)
		res += b"\x46\x20\x20\x31\x0C\x00\x00\x00"
		res += utils.int32bytes(self.activex)
		res += utils.int32bytes(self.activey)
		res += utils.int32bytes(self.delay)
		res += b"\x46\x44\x20\x31"	#FD 1
		res += utils.int32bytes(len(self.bmp32))
		res += self.bmp32
		res += b"\x46\x49\x20\x31"	#FI 1
		res += utils.int32bytes(len(self.bmp24))
		res += self.bmp24
		if self.hasalpha:
			alpha: bytes = self.alpha
			res += b"\x46\x4D\x20\x31"	#FM 1
			res += utils.int32bytes(len(alpha))
			res += alpha
		if self.startnum > 3:
			res += b"\x46\x45\x20\x32"	#FE 2
			res += b"\x05\x00\x00\x00\x02\xFF\xFF\xFF\x00"
		return bytes(res)

	def read(stream: io.BufferedIOBase) -> "LogoImage":
		startnum: int = utils.readint32(stream)
		stream.read(8)	#constant data??	46 20 20 31 0C 00 00 00
		activex: int = utils.readint32(stream)
		activey: int = utils.readint32(stream)
		delay: int = utils.readint32(stream)
		length: int = 0
		bmp32: Optional[bytes] = None
		bmp24: Optional[bytes] = None
		alpha: Optional[bytes] = None
		while True:
			if not stream.read(1):	#F
				break
			t: int = stream.read(1)[0]
			if t == 0x44:	#D - 32b
				stream.read(2)	#_1
				length = utils.readint32(stream)
				bmp32 = stream.read(length)
			elif t == 0x49:	#I - 24b
				stream.read(2)	#_1
				length = utils.readint32(stream)
				bmp24 = stream.read(length)
				if startnum <= 2:
					break
			elif t == 0x4D:	#M - alpha
				stream.read(2)	#_1
				length = utils.readint32(stream)
				alpha = stream.read(length)
				if startnum <= 3:	#TODO figure this out
					break
			elif t == 0x45:	#E
				break
			else:
				raise ValueError(f"Unknown image indicator: {hex(t)} ({stream.tell()-1})")
		if startnum > 3:
			stream.read(2)	#_2
			stream.read(9)	#constant data???	05 00 00 00 02 FF FF FF 00
		if bmp32 is None:
			with io.BytesIO(bmp24) as rstream:
				_img = Image.open(rstream).convert("RGBA")
				if alpha is None:
					_img.putalpha(0)
				else:
					with io.BytesIO(alpha) as astream:
						alpha_img = Image.open(astream).convert("1").point(lambda x: 255 * (x > 0)).convert("L")
						_img.putalpha(alpha_img)
				with io.BytesIO() as wstream:
					_img.save(wstream, format="BMP")
					bmp32 = wstream.getvalue()
		img = LogoImage.from_bytes(bmp32, activex, activey, delay,False)
		img.startnum = startnum
		return img
	
	def from_image(image: Image, activex: Optional[int] = None, activey: Optional[int] = None, delay: int = 100, invert_alpha: bool = True) -> "LogoImage":
		startnum: int = 5	#TODO Figure this out
		image = image.convert("RGBA")
		if invert_alpha:
			arr: np.ndarray = np.array(image)
			arr[..., 3] = 255 - arr[..., 3]
			image = Image.fromarray(arr, "RGBA")
		if activex is None:
			activex = image.width // 2
		if activey is None:
			activey = image.height // 2
		return LogoImage(startnum, activex, activey, delay, np.array(image))
	
	def from_stream(stream: io.BufferedIOBase, activex: Optional[int] = None, activey: Optional[int] = None, delay: int = 100, invert_alpha: bool = True) -> "LogoImage":
		def finish() -> LogoImage:
			stream.seek(0)
			return LogoImage.from_image(Image.open(stream), invert_alpha)
		#32bit BMP fix
		if stream.read(2) != b"\x42\x4D":	#BM
			return finish()
		stream.seek(10)
		bitmap_start: int = utils.readint32(stream)
		header_size: int = utils.readint32(stream)
		if header_size != 40:	#BITMAPINFOHEADER
			return finish()
		width: int = utils.readint32(stream)
		height: int = utils.readint32(stream)
		stream.seek(28)
		depth: int = int.from_bytes(stream.read(2), byteorder="little")
		if depth != 32:
			return finish()
		compression: int = utils.readint32(stream)
		if compression != 0:	#3, 6?
			return finish()
		stream.seek(bitmap_start)
		bitmap: bytes = stream.read()
		arr: np.ndarray = np.array(bytearray(bitmap))
		arr = arr.reshape((height, width, 4))
		arr = arr[..., [2, 1, 0, 3]]
		return LogoImage.from_image(ImageOps.flip(Image.fromarray(arr, "RGBA")), activex, activey, delay, invert_alpha)
	
	def from_bytes(image: bytes, activex: Optional[int] = None, activey: Optional[int] = None, delay: int = 100, invert_alpha: bool = True) -> "LogoImage":
		assert len(image) >= 2
		with io.BytesIO(image) as stream:
			return LogoImage.from_stream(stream, activex, activey, delay, invert_alpha)
		

class LogoFrame:
	def __init__(self, startnum: int):
		self.startnum: int = startnum
		self.images: list[LogoImage] = []
	
	def __bytes__(self) ->  bytes:
		res: bytearray = bytearray()
		res += utils.int32bytes(self.startnum)
		res += b"\x46\x53\x20\x31"	#FS 1
		imgdata: bytearray = bytearray()
		imgdata += utils.int32bytes(len(self.images))
		for img in self.images:
			imgdata += bytes(img)
		res += utils.int32bytes(len(imgdata))
		res += imgdata
		return bytes(res)
	
	def read(stream: io.BufferedIOBase) -> "LogoFrame":
		startnum: int = utils.readint32(stream)
		stream.read(4)	#FS 1
		utils.readint32(stream)	#length
		img_count: int = utils.readint32(stream)
		frame: LogoFrame = LogoFrame(startnum)
		for i in range(img_count):
			frame.images.append(LogoImage.read(stream))
		return frame
	
	def add_bytes(self, image: bytes, activex: Optional[int] = None, activey: Optional[int] = None, delay: int = 100, invert_alpha: bool = True):
		self.images.append(LogoImage.from_bytes(image, activex, activey, delay, invert_alpha))
	
	def add_image(self, image: Image, activex: Optional[int] = None, activey: Optional[int] = None, delay: int = 100, invert_alpha: bool = True):
		self.images.append(LogoImage.from_image(image, activex, activey, delay, invert_alpha))

class LogoGraphics:
	def __init__(self, angle0: float, repeat: bool, compass: bool):
		self.angle0: float = angle0
		self.repeat: bool = repeat
		self.compass: bool = compass
		self.frames: list[LogoFrame] = []
	
	def read(stream: io.BufferedIOBase) -> "LogoGraphics":
		stream.read(4)
		length: int = utils.readint32(stream)
		stream.read(4)
		with io.BytesIO(zlib.decompress(stream.read(length-4))) as graphics_stream:
			angle0: float = utils.readfloat64(graphics_stream)
			repeat: bool = bool(graphics_stream.read(1)[0])
			compass: bool = bool(graphics_stream.read(1)[0])
			graphics: LogoGraphics = LogoGraphics(angle0, repeat, compass)
			num_frames: int = utils.readint32(graphics_stream)
			for i in range(num_frames):
				graphics.frames.append(LogoFrame.read(graphics_stream))
			return graphics
	
	def __bytes__(self) -> bytes:
		res: bytearray = bytearray()
		res += b"\x49\x4D\x5A\x31"	#IMZ1
		origdata: bytearray = bytearray()
		origdata += utils.float64bytes(self.angle0)
		origdata.append(int(self.repeat))
		origdata.append(int(self.compass))
		origdata += utils.int32bytes(len(self.frames))
		for frame in self.frames:
			origdata += bytes(frame)
		compressed: bytes = zlib.compress(bytes(origdata), level=6)
		res += utils.int32bytes(len(compressed)+4)
		res += utils.int32bytes(len(origdata))
		res += compressed
		return bytes(res)

class LogoThumbnail:
	def __init__(self, bmp: bytes):
		self.bmp: bytes = bmp

	def __bytes__(self) -> bytes:
		res: bytearray = bytearray()
		res += b"\x49\x43\x5A\x31"	#ICZ1
		compressed: bytes = zlib.compress(bytes(self.bmp), level=6)
		res += utils.int32bytes(len(compressed)+4)
		res += utils.int32bytes(len(self.bmp))
		res += compressed
		return bytes(res)

	def read(stream: io.BufferedIOBase) -> "LogoThumbnail":
		stream.read(4)	#ICZ1
		length: int = utils.readint32(stream)
		stream.read(4)	#Original length
		return LogoThumbnail(zlib.decompress(stream.read(length-4)))

class LGFFile:
	def __init__(self, version: int):
		self.version: int = version
		self.graphics: list[LogoGraphics] = []
	
	def read(stream: io.BufferedIOBase) -> "LGFFile":
		stream.read(3)	#LGF
		version = utils.readint(2, stream)
		lgf = LGFFile(version)
		graphics_count = utils.readint32(stream)
		for i in range(graphics_count):
			lgf.graphics.append(LogoGraphics.read(stream))
		return lgf
	
	def read_bytes(data: bytes) -> "LGFFile":
		with io.BytesIO(data) as stream:
			return LGFFile.read(stream)
	
	def read_file(path: str) -> "LGFFile":
		with open(path, "rb") as f:
			return LGFFile.read(f)
	
	def __bytes__(self) -> bytes:
		res: bytearray = bytearray()
		res += b"\x4C\x47\x46"	#LGF
		if self.version < 10:
			res += b"\x30"
		res += str(self.version).encode(utils.ENCODING)
		res += utils.int32bytes(len(self.graphics))
		for graphic in self.graphics:
			res += bytes(graphic)
		return bytes(res)
	
	def write(self, stream: io.BufferedIOBase):
		stream.write(bytes(self))
	
	def write_file(self, path: str):
		with open(path, "wb") as f:
			self.write(f)