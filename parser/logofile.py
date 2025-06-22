from typing import Optional, List
from datetime import datetime
from copy import deepcopy
from parser.lang import hungarian
from parser.logographics import *
import parser.logo_objects as obj
import parser.utils as utils
import io
import os

_LOCALES = {
	"hungarian": hungarian
}

_ESCAPE = ['\\', ' ', '[', ']', '(', ')', '"', '+', '-', '/', '*', '|']

def _get_command_bytes(stream: io.BytesIO) -> Optional[bytes]:
	res: bytearray = bytearray()
	cont = True
	end: bool = False
	while True:
		b: bytes = stream.read(1)
		if b == b"":
			end = True
			break
		value: int = b[0]
		if value == 0x0A:	#\n
			cont = False
			continue
		elif value == 0x0D:	#\r
			if not cont:
				stream.read(1)
				break
			continue
		elif value == 0x09:	#\t
			value = 0x01
		elif not cont:
			stream.seek(-1, os.SEEK_CUR)
			break
		cont = True
		res += value.to_bytes(1)
	if end and len(res) == 0:
		return None
	return bytes(res)

def _parsevalue(value: bytearray, strlevel: int, inlist: bool) -> object:
	s: str = value.decode(utils.ENCODING)
	if strlevel > 0:
		return s
	if s == "igaz":
		return True
	if s == "hamis":
		return False
	try:
		return int(s)
	except ValueError:
		try:
			return float(s)
		except ValueError:
			return s if inlist else LogoCommandEval(s)

def _tostr(value: object, inlist: bool = False) -> str:
	if isinstance(value, bool):
		return "igaz" if value else "hamis"
	if isinstance(value, str):
		if "|" in value:
			for c in _ESCAPE:
				value = value.replace(c, "\\" + c)
			return value if inlist else '"' + value
		return f'|{value}|' if inlist else f'"|{value}|'
	if isinstance(value, int) or isinstance(value ,float):
		return str(value)
	if isinstance(value, list):
		s = "["
		tail = False
		for inner in value:
			if tail:
				s += " "
			tail = True
			s += _tostr(inner, True)
		s += "]"
		return s
	if isinstance(value, LogoCommandEval):
		return value.cmd
	raise TypeError(f"Unknown Imagine type: {type(value)}")

def _process_setting(key: str, value: object, locales, definitions: dict[str, str], events: dict[str, str], ownvars: dict[str, object], commonvars: dict[str, object]) -> bool:
	if key.startswith(locales.SETTING_SELFDEFINE):
		key = key.replace(locales.SETTING_SELFDEFINE, "", 1)
		if isinstance(value, list):
			newvalue: str = "eljárás " + key
			print(value)
			for p in value[0]:
				newvalue += " :" + p
			newvalue += chr(0xB6) + " " + _tostr(value[1]).replace("|", "") + chr(0xB6) + "vége"
			value = newvalue
		definitions[key] = value.replace(chr(0xB6), "\n")
		return True
	if key.startswith(locales.SETTING_EVENT):
		key = key.replace(locales.SETTING_EVENT, "", 1)
		events[key] = _tostr(value) if isinstance(value, list) else value
		return True
	if key.startswith(locales.SETTING_OWNVAR):
		key = key.replace(locales.SETTING_OWNVAR, "", 1)
		ownvars[key] = value
		return True
	if key.startswith(locales.SETTING_COMMONVAR):
		key = key.replace(locales.SETTING_COMMONVAR, "", 1)
		commonvars[key] = value
		return True
	return False

def _tolocation(o: obj.Main | type) -> str:
	current: obj.Main | type = o
	s: str = ""
	while current != None:
		if s != "":
			s = "'" + s
		s = current.__name__ + s
		current = current.__location__ if isinstance(o, obj.Main) else current.classlocation
	return s

class LogoCommandEval:
	def __init__(self, cmd: str):
		self.cmd: str = cmd

class LogoProjectSettings:
	def __init__(self, language: str, path: str, version: str, date: datetime):
		self.language: str = language
		self.path: str = path
		self.version: str = version
		self.date: datetime = date
	
	def read(stream: io.BufferedIOBase) -> "LogoProjectSettings":
		stream.read(11)	#language: "
		language: str = utils.readstr(stream)
		stream.read(8)	#_name: "
		path: str = utils.readstr(stream)
		stream.read(12)	#__version: "
		version: str = utils.readstr(stream)
		stream.read(8)	#__date:_
		datestr: str = stream.read(19).decode(utils.ENCODING)	#DD.MM.YYYY HH:MM:SS
		stream.read(4)	#\r\n\r\n
		return LogoProjectSettings(language, path, version, datetime.strptime(datestr, "%d.%m.%Y %H:%M:%S"))
	
	def __bytes__(self) -> bytes:
		res: bytearray = bytearray(b"\x6C\x61\x6E\x67\x75\x61\x67\x65\x3A\x20\x22")	#language: "
		res += self.language.encode(utils.ENCODING)
		res += b"\x22\x20\x6E\x61\x6D\x65\x3A\x20\x22"	#" name: "
		res += self.path.encode(utils.ENCODING)
		res += b"\x22\x20\x20\x76\x65\x72\x73\x69\x6F\x6E\x3A\x20\x22"	#"  version: "
		res += self.version.encode(utils.ENCODING)
		res += b"\x22\x20\x20\x64\x61\x74\x65\x3A\x20"	#"  date:_
		res += self.date.strftime("%d.%m.%Y %H:%M:%S").encode(utils.ENCODING)
		#res += b"\x0D\x0A\x0D\x0A"	#\r\n\r\n
		return bytes(res)
		

class LogoHeader:
	def __init__(self, version: int, graphicsnum: int, langoverride: bool, language: str = ""):
		self.version: int = version
		self.graphicsnum: int = graphicsnum
		self.size: int = 0
		self.langoverride: bool = langoverride
		if self.langoverride:
			self.language: str = language
			self.langsize: int = len(self.language)
			if self.language not in _LOCALES:
				raise ValueError("Unknown language: " + self.language)
			self._locales = _LOCALES[self.language]
		else:
			self.language: str = ""
			self.langsize: int = 0
			raise NotImplementedError("English is not yet implemented")
	
	@property
	def graphics(self) -> bool:
		return self.graphicsnum > 2	#TODO figure this out
	
	def read(stream: io.BufferedIOBase) -> "LogoHeader":
		stream.read(3)	#LFG
		version: int = utils.readint(2, stream)
		graphicsnum: int = utils.readint32(stream)
		l = stream.read(1)[0]
		langoverride: bool = False
		langsize: int = 0
		language: str = ""
		if l == 0x4C:	#L
			langoverride = True
			stream.read(3)	#A 1
			langsize = utils.readint32(stream)
			language = stream.read(langsize).decode(utils.ENCODING)
			stream.read(1)	#T
		stream.read(3)	#X 1
		size: int = utils.readint32(stream)
		stream.read(2)	#;_
		header = LogoHeader(version, graphicsnum, langoverride, language)
		header.size = size
		return header
		
	def __bytes__(self) -> bytes:
		res: bytearray = bytearray(b"\x4C\x47\x46")	#LGF
		if self.version < 10:
			res.append(0x30)	#0
		res += str(self.version).encode(utils.ENCODING)
		res += utils.int32bytes(self.graphicsnum)
		if self.langoverride:
			res += b"\x4C\x41\x20\x31"	#LA 1
			res += utils.int32bytes(self.langsize)
			res += self.language.encode(utils.ENCODING)
		res += b"\x54\x58\x20\x31"	#TX 1
		res += utils.int32bytes(self.size)
		res += b"\x3B\x20"	#;_
		return bytes(res)

class LogoCommand:
	def __init__(self, _file: "LogoFile", raw: bytes):
		self._file: LogoFile = _file
		self._locales = self._file.header._locales
		with io.BytesIO(raw) as stream:
			callees: List[str] = []
			currentcallee: bytearray = bytearray()
			while (current := stream.read(1)) != b"\x20":
				if current[0] == 0x27:
					callees.append(currentcallee.decode(utils.ENCODING))
					currentcallee = bytearray()
				else:
					currentcallee += current
			name = currentcallee.decode(utils.ENCODING)
			parameters = []
			currentvalue: bytearray = bytearray()
			escape: bool = False
			last2: int = -1
			last: int = -1
			lists = []
			strlevel: int = 0
			while (current := stream.read(1)) != b"":
				byte = current[0]
				if byte == 0x01:
					if len(lists) > 0 and len(lists[-1]) == 0:
						continue
					byte = 0x20
				if byte == 0x7C and not escape:	#|
					#escape = False
					if strlevel < 2:
						strlevel = 2
					else:
						if len(lists) > 0:
							lists[-1].append(_parsevalue(currentvalue, strlevel, True))
							if stream.read(2) != b"\x5C\x30":	#\0
								stream.seek(-1, os.SEEK_CUR)
						else:
							parameters.append(_parsevalue(currentvalue, strlevel, False))
						currentvalue = bytearray()
						strlevel = 0
				elif escape or strlevel == 2:
					currentvalue.append(byte)
					escape = False
				elif byte == 0x5C:	#\
					escape = True
				elif byte == 0x22:	#"
					if len(lists) > 0:
						currentvalue.append(byte)
					elif strlevel == 2:
						currentvalue.append(byte)
					elif strlevel == 0:
						strlevel = 1
					else:
						raise ValueError("Quotation mark error")
				elif byte == 0x5B:	#[
					lists.append([])
					if len(lists) > 1:
						lists[-2].append(lists[-1])
				elif byte == 0x5D:	#]
					if len(currentvalue) > 0:
						lists[-1].append(_parsevalue(currentvalue, strlevel, True))
					if len(lists) == 1:
						parameters.append(lists[0])
					del lists[-1]
					currentvalue = bytearray()
					strlevel = 0
				elif byte == 0x20:	#_
					if len(currentvalue) > 0:
						if len(lists) > 0:
							lists[-1].append(_parsevalue(currentvalue, strlevel, True))
						else:
							parameters.append(_parsevalue(currentvalue, strlevel, False))
						currentvalue = bytearray()
						strlevel = 0
				else:
					currentvalue.append(byte)
			if len(lists) > 0:
				if len(currentvalue) > 0:
					lists[-1].append(_parsevalue(currentvalue, strlevel, True))
				parameters.append(lists[0])
			elif len(currentvalue) > 0:
				parameters.append(_parsevalue(currentvalue, strlevel, False))
			self.callees = callees
			self.name = name.lower()
			self.parameters = parameters
			self._process()
	
	def __str__(self) -> str:
		s: str = ""
		s += "'".join(self.callees)
		if len(self.callees) > 0:
			s += "'"
		s += self.name
		for v in self.parameters:
			s += " " + _tostr(v)
		return s
	
	def __bytes__(self) -> bytes:
		return str(self).encode(utils.ENCODING)

	def _process(self):
		if self.name == self._locales.COMMAND_NEW:
			self._process_new()
		if self.name == self._locales.COMMAND_NEWCLASS:
			self._process_newclass()
		if self.name == self._locales.COMMAND_GLOBALVAR:
			self._process_globalvar()
		if self.name == self._locales.COMMAND_FIELDS:
			self._process_fields()
		if self.name == self._locales.COMMAND_WINDOWSTATE:
			self._process_window_state()
		if self.name == self._locales.COMMAND_ACTIVETURTLE:
			self._process_activeturtle()
	
	def _process_new(self, window: bool = False):
		o: obj.Main = None
		classname: str = self.parameters[0].lower() if not window else self._locales.CLASS_MAINWINDOW
		location = self._file.window if not window else None
		if len(self.callees) > 0:
			location = self._file.name_to_object(self.callees[-1])
		o = self._file.name_to_object(classname)(location) if not window else obj.MainWindow(location)
		definitions: dict[str, str] = {}
		events: dict[str, str] = {}
		ownvars: dict[str, object] = {}
		commonvars: dict[str, object] = {}
		listindex: int = 1 if not window else 0
		for i in range(0, len(self.parameters[listindex])-1, 2):
			key = self.parameters[listindex][i]
			value = self.parameters[listindex][i+1]
			if _process_setting(str(key), value, self._locales, definitions, events, ownvars, commonvars):
				continue
			o._change(key, value, True)
		o.definitions.update(definitions)
		o.events.update(events)
		o.ownvars.update(ownvars)
		o.commonvars.update(commonvars)
		o._load_locales(self._locales)
		if window:
			self._file.window = o
			for _obj in self._file.objects:
				if isinstance(_obj, obj.Main):
					if isinstance(_obj.__location__, obj.MainWindow):
						_obj.__location__ = self._file.window
				elif isinstance(_obj, type):
					if isinstance(_obj.classlocation, obj.MainWindow):
						_obj.classlocation = self._file.window
				else:
					raise TypeError(f"Unknown object type: {type(_obj)}")
		else:
			self._file.objects.append(o)
	
	def _process_newclass(self):
		base_class: str = self.parameters[0]
		classname: str = self.parameters[1]
		base_type: type = self._file.name_to_object(base_class) if classname != self._locales.CLASS_MAINWINDOW else obj.MainWindow
		settings: dict[str, object] = deepcopy(base_type._DEFAULTS)
		definitions: dict[str, str] = {}
		events: dict[str, str] = {}
		ownvars: dict[str, object] = {}
		commonvars: dict[str, object] = {}
		for i in range(0, len(self.parameters[2])-1, 2):
			key = self.parameters[2][i]
			value = self.parameters[2][i+1]
			if _process_setting(str(key), value, self._locales, definitions, events, ownvars, commonvars):
				continue
			if key in self._locales.SETTINGS:
				keyindex = self._locales.SETTINGS.index(key)
				if f"_{keyindex}" in settings:
					key = self._locales.SETTINGS.index(key)
			try:
				settingnum: int = int(key)
				if settingnum > 0 and settingnum <= len(obj.SETTINGS):
					settings[f"_{settingnum}"] = value
				else:
					ownvars[str(settingnum)] = value
			except ValueError:
				ownvars[key] = value
		def __init__(self, location):
			self._initialize(location)
		new_type: type = obj.LogoSettings("obj", **settings)(type(classname, (base_type,), {"__init__": __init__}))
		new_type.classlocation = self._file.window
		new_type.classdefinitions = deepcopy(new_type.classdefinitions)
		new_type.classdefinitions.update(definitions)
		new_type.classevents = deepcopy(new_type.classevents)
		new_type.classevents.update(events)
		new_type.classownvars = deepcopy(new_type.classownvars)
		new_type.classownvars.update(ownvars)
		new_type.classcommonvars = deepcopy(new_type.classcommonvars)
		new_type.classcommonvars.update(commonvars)
		self._file.objects.append(new_type)
		self._file.classes[classname] = new_type
	
	def _process_globalvar(self):
		self._file.globalvars[self.parameters[0]] = self.parameters[1]
	
	def _process_fields(self):
		table: str = self.parameters[0]
		if not table in self._file.fields:
			self._file.fields[table] = {}
		for i in range(0, len(self.parameters[1])-1, 2):
			key = self.parameters[1][i]
			value = self.parameters[1][i+1]
			self._file.fields[table][key] = value
	
	def _process_window_state(self):
		self._process_new(True)
	
	def _process_activeturtle(self):
		o = self._file.name_to_object(self.callees[-1])
		active = None
		if isinstance(self.parameters[0], list):
			active = [self._file.name_to_object(n).__name__ for n in self.parameters[0]]
		else:
			active = self._file.name_to_object(self.parameters[0]).__name__
		o._change(38, active)
		

class LogoFile:
	def __init__(self, header: LogoHeader, settings: LogoProjectSettings):
		self.header: LogoHeader = header
		self.settings: LogoProjectSettings = settings
		self.commands: List[LogoCommand] = []
		self.thumbnail: Optional[LogoThumbnail] = None
		self.graphics: Optional[LGFFile] = None
		self.objects: List[obj.Main | type] = []
		self.window = obj.MainWindow(None)
		self.globalvars: dict[str, object] = {}
		self.fields: dict[str, dict[str, object]] = {}
		self.classes : dict[str, type] = {
			self.header._locales.CLASS_MAIN: obj.Main,
			self.header._locales.CLASS_MAINWINDOW: obj.MainWindow,
			self.header._locales.CLASS_PAGE: obj.Page,
			self.header._locales.CLASS_PANE: obj.Pane,
			self.header._locales.CLASS_TOOLBAR: obj.ToolBar,
			self.header._locales.CLASS_TURTLE: obj.Turtle,
			self.header._locales.CLASS_TEXTBOX: obj.TextBox,
			self.header._locales.CLASS_SLIDER: obj.Slider,
			self.header._locales.CLASS_BUTTON: obj.Button,
			self.header._locales.CLASS_TOOLBUTTON: obj.ToolButton,
			self.header._locales.CLASS_WEB: obj.Web,
			self.header._locales.CLASS_MEDIAPLAYER: obj.MediaPlayer,
			self.header._locales.CLASS_NET: obj.Net,
			self.header._locales.CLASS_JOYSTICK: obj.Joystick,
			self.header._locales.CLASS_COMMPORT: obj.CommPort,
			self.header._locales.CLASS_OLEOBJECT: obj.OleObject,
		}
	
	def __bytes__(self) -> bytes:
		self.update_header()
		res: bytearray = bytearray()
		res += bytes(self.header)
		res += bytes(self.settings)
		for cmd in self.commands:
			res += b"\x0D\x0A\x0D\x0A"
			res += bytes(cmd)
		res += b"\x0D\x0A"
		if self.thumbnail is not None:
			res += bytes(self.thumbnail)
		if self.header.graphics:
			res += bytes(self.graphics)[9:]
		return bytes(res)
	
	def write(self, stream: io.BufferedIOBase):
		stream.write(bytes(self))
	
	def write_file(self, path: str):
		with open(path, "wb") as f:
			self.write(f)
	
	def update_header(self):
		self.header.graphicsnum = len(self.graphics.graphics)+2
		if self.thumbnail is not None:
			self.header.graphicsnum += 1
		self.header.size = 4	#;_ [...] \r\n
		self.header.size += len(bytes(self.settings))
		for cmd in self.commands:
			self.header.size += len(bytes(cmd)) + 4	#\r\n\r\n
	
	def read(stream: io.BufferedIOBase) -> "LogoFile":
		header: LogoHeader = LogoHeader.read(stream)
		commandsraw: bytes = stream.read(header.size - 2)
		with io.BytesIO(commandsraw) as commandsstream:
			settings: LogoProjectSettings = LogoProjectSettings.read(commandsstream)
			lfile: LogoFile = LogoFile(header, settings)
			commands: List[LogoCommand] = []
			while (cmd := _get_command_bytes(commandsstream)) != None:
				if cmd:
					commands.append(LogoCommand(lfile, cmd))
		lfile.commands = commands
		if header.graphics:
			lfile.graphics = LGFFile(4)
			for i in range(header.graphicsnum-2):
				gheader = stream.read(4)
				stream.seek(-4, os.SEEK_CUR)
				if gheader == b"\x49\x43\x5A\x31":	#ICZ1:
					lfile.thumbnail = LogoThumbnail.read(stream)
				elif gheader == b"\x49\x4D\x5A\x31":	#IMZ1:
					lfile.graphics.graphics.append(LogoGraphics.read(stream))
				else:
					raise ValueError(f"Unknown graphics header: {gheader}")
		return lfile
	
	def read_bytes(data: bytes) -> "LogoFile":
		with io.BytesIO(data) as stream:
			return LogoFile.read(stream)
	
	def read_file(path: str) -> "LogoFile":
		with open(path, "rb") as f:
			return LogoFile.read(f)
	
	def cmd_from_str(self, cmd: str) -> LogoCommand:
		return LogoCommand(self, cmd.encode(utils.ENCODING))
	
	def index_to_object(self, index: int):
		if index < 1 or index > len(self.objects):
			raise IndexError("Index out of range")
		return self.objects[index-1]
	
	def name_to_object(self, name: str) -> obj.Main | type:
		if not name:
			raise ValueError("Empty name")
		if name == "fõablak":
			return self.window
		if name.startswith("#"):
			return self.index_to_object(int(name[1:]))
		if name in self.classes:
			return self.classes[name]
		for o in self.objects:
			if o.__name__ == name:
				return o
		raise ValueError("Object not found: " + name)