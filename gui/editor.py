from nicegui import ui, events, app

from parser.logofile import LogoFile, _tolocation
import parser.logo_objects as obj
from parser.logographics import LGFFile, LogoImage, LogoFrame
from PIL import Image
import io
import base64

IMAGE_HEIGHT = 50

def img_base64(img: LogoImage) -> str:
    return base64.b64encode(img.get_alpha_bmp()).decode("utf-8")

def create_gif(images):
    imgs = []
    streams = []
    maxx = 0
    maxy = 0
    for img in images:
        stream = io.BytesIO(img)
        _img = Image.open(stream)
        if _img.width > maxx:
            maxx = _img.width
        if _img.height > maxy:
            maxy = _img.height
        imgs.append(_img)
    for i in range(len(imgs)):
        img = imgs[i]
        new_img = Image.new("RGB", (maxx, maxy), color="white")
        x0 = (maxx-img.width)//2
        y0 = (maxy-img.height)//2
        new_img.paste(img, (x0, y0))
        imgs[i] = new_img
    with io.BytesIO() as wstream:
        imgs[0].save(wstream, format="GIF", append_images=imgs[1:], save_all=True, duration=200, loop=0)
        for s in streams:
            s.close()
        return wstream.getvalue()

def get_icon(_obj: obj.Main | type, prefix: str = None) -> str:
    if prefix is None:
        return get_icon(type(_obj), "img:icons/obj_") if isinstance(_obj, obj.Main) else get_icon(_obj, "img:icons/cls_")
    if _obj == obj.Main or _obj == object:
        return prefix + "main.png"
    if _obj == obj.MainWindow:
        return prefix + "mainwindow.png"
    if _obj == obj.Page:
        return prefix + "page.png"
    if _obj == obj.Pane:
        return prefix + "pane.png"
    if _obj == obj.ToolBar:
        return prefix + "toolbar.png"
    if _obj == obj.Turtle:
        return prefix + "turtle.png"
    if _obj == obj.TextBox:
        return prefix + "textbox.png"
    if _obj == obj.Slider:
        return prefix + "slider.png"
    if _obj == obj.Button:
        return prefix + "button.png"
    if _obj == obj.Web or _obj == obj.Net:
        return prefix + "web.png"
    if _obj == obj.MediaPlayer:
        return prefix + "mediaplayer.png"
    if _obj == obj.Main:
        return prefix + "main.png"
    return get_icon(_obj.__bases__[0], prefix)

def get_attributes(id, settings, definitions, events, ownvars, commonvars):
    l = []
    if len(definitions) > 0:
        defs = []
        for def_name in definitions:
            defs.append({"id": f"{id} definition'{def_name}", "name": def_name, "icon":"img:icons/definition.png"})
        l.append({"id": f"{id} definition", "name": "Eljárások", "icon":"img:icons/definition.png", "children": defs})
    if len(ownvars) > 0:
        vars = []
        for var_name in ownvars:
            vars.append({"id": f"{id} ownvar'{var_name}", "name": var_name, "icon":"img:icons/ownvar.png"})
        l.append({"id": f"{id} ownvar", "name": "Saját változók", "icon":"img:icons/ownvar.png", "children": vars})
    if len(commonvars) > 0:
        vars = []
        for var_name in commonvars:
            vars.append({"id": f"{id} commonvar'{var_name}", "name": var_name, "icon":"img:icons/commonvar.png"})
        l.append({"id": f"{id} commonvar", "name": "Közös változók", "icon":"img:icons/commonvar.png", "children": vars})
    if len(events) > 0:
        ev = []
        for event_name in events:
            ev.append({"id": f"{id} event'{event_name}", "name": event_name, "icon":"img:icons/event.png"})
        l.append({"id": f"{id} event", "name": "Események", "icon":"img:icons/event.png", "children": ev})
    if len(settings) > 0:
        s = []
        for setting_name in settings:
            if setting_name == "__name__":
                continue
            s.append({"id": f"{id} setting'{settings[setting_name]}", "name": setting_name, "icon":"img:icons/setting.png"})
        if len(s) > 0:
            l.append({"id": f"{id} setting", "name": "Beállítások", "icon":"img:icons/setting.png", "children": s})
    return l

def get_children(id, _obj, d, indices, locales):
    l = []
    for key in d:
        children = get_children(f"#{indices[key]}", key, d[key], indices, locales)
        l.append({"id": f"#{indices[key]}", "name": key.__name__, "icon":get_icon(key), "children": children})
    if isinstance(_obj, obj.Main):
        settings = {}
        for s in _obj._settings.values():
            if s.localname not in settings:
                settings[s.localname] = s.index
        l += get_attributes(id, settings, _obj.definitions, _obj.events, _obj.ownvars, _obj.commonvars)
    elif isinstance(_obj, type):
        settings = {}
        for s in _obj._DEFAULTS:
            _name = locales.SETTINGS[int(s[1:])]
            if _name not in settings:
                settings[_name] = s[1:]
        l += get_attributes(id, settings, _obj.classdefinitions, _obj.classevents, _obj.classownvars, _obj.classcommonvars)
    return l

def getstr(obj: object) -> str:
    if isinstance(obj, bool):
        return "igaz" if obj else "hamis"
    return str(obj)

def select_object(id: str, file: LogoFile, data_label) -> bool:
    if not id:
        return False
    splitted = id.split(" ")
    if not splitted[0]:
        return False
    if splitted[0] == "_":
        datasplit = splitted[1].split("'")
        datatype = datasplit[0]
        if len(datasplit) == 1:
            return False
        dataname = datasplit[1]
        if not dataname:
            return False
        if datatype == "field":
            data_label._handle_content_change(str(file.fields[dataname]))
            return True
        elif datatype == "globalvar":
            data_label._handle_content_change(str(file.globalvars[dataname]))
            return True
        return False
    _obj = file.name_to_object(splitted[0])
    if len(splitted) == 1:
        data_label._handle_content_change(_tolocation(_obj))
        return True
    else:
        datasplit = splitted[1].split("'")
        datatype = datasplit[0]
        if len(datasplit) == 1:
            return False
        dataname = datasplit[1]
        if not dataname:
            return False
        if isinstance(_obj, obj.Main):
            definitions = _obj.definitions
            ownvars = _obj.ownvars
            commonvars = _obj.commonvars
            events = _obj.events
        elif isinstance(_obj, type):
            definitions = _obj.classdefinitions
            ownvars = _obj.classownvars
            commonvars = _obj.classcommonvars
            events = _obj.classevents
        else:
            return False
        if datatype == "definition":
            data_label._handle_content_change(definitions[dataname].replace("\n", "<br>").replace(" ", "&nbsp;"))
            return True
        if datatype == "ownvar":
            data_label._handle_content_change(getstr(ownvars[dataname]))
            return True
        if datatype == "commonvar":
            data_label._handle_content_change(getstr(commonvars[dataname]))
            return True
        if datatype == "event":
            data_label._handle_content_change(events[dataname])
            return True
        if datatype == "setting":
            data_label._handle_content_change(getstr(getattr(_obj, obj.SETTINGS[int(dataname)]) if isinstance(_obj, obj.Main) else _obj._DEFAULTS[f"_{dataname}"]))
            return True
        return False
    return False

def handle_upload(e: events.UploadEventArguments):
    e.sender.remove(e.sender)
    filename = e.name
    file = None
    graphicsfile = None
    extension = filename.split(".")[-1].lower()
    if extension == "imp":
        file = LogoFile.read(e.content)
        if file.header.graphics:
            graphicsfile = file.graphics
    elif extension == "lgf":
        graphicsfile = LGFFile.read(e.content)
    has_project = file is not None
    has_graphics = graphicsfile is not None
    #filename = file.settings.path.split("\\")[-1]
    with ui.row().classes("no-wrap"):
        if has_project and file.thumbnail is not None:
            ui.image("data:image/png;base64," + base64.b64encode(file.thumbnail.bmp).decode("utf-8")).props("width=25px")
        ui.label(filename)
        #ui.button("Letöltés", on_click=lambda: ui.download.content(bytes(file if has_project else graphicsfile), filename))
        ui.button("Új fájl", on_click=lambda: ui.run_javascript('location.reload();'))
    with ui.tabs().classes("justify-start") as tabs:
        if has_project:
            commands = ui.tab("Parancsok")
            objects = ui.tab("Objektumok")
        if has_graphics:
            graphics = ui.tab("Grafika")
        
    with ui.tab_panels(tabs, value=commands if has_project else graphics if has_graphics else None).classes("w-full"):
        if has_project:
            with ui.tab_panel(commands):
                with ui.scroll_area().classes("h-[80vh] w-full"):
                    for cmd in file.commands:
                        ui.label(str(cmd))
            with ui.tab_panel(objects):
                window = {}
                tree = {file.window: window}
                indices = {}
                ind = 0
                for _obj in file.objects:
                    ind += 1
                    indices[_obj] = ind
                    parent = _obj
                    trace = [_obj]
                    while parent is not None:
                        if isinstance(parent, obj.Main):
                            parent = parent.__location__
                        elif isinstance(parent, type):
                            parent = parent.classlocation
                        if parent is None:
                            break
                        if parent in tree:
                            for t in reversed(trace):
                                d = {}
                                tree[parent][t] = d
                                tree[t] = d
                                parent = t
                            break
                        trace.append(parent)
                nodes = [{"id": "fõablak", "name": "fõablak", "icon":"img:icons/obj_mainwindow.png", "children": get_children("fõablak", file.window, window, indices, file.header._locales)}]
                if len(file.fields) > 0:
                    fields = []
                    for key in file.fields:
                        fields.append({"id": f"_ field'{key}", "name": key, "icon":"img:icons/field.png"})
                    nodes.append({"id": "_ field", "name": "Tulajdonságok", "icon":"img:icons/field.png", "children": fields})
                if len(file.globalvars) > 0:
                    globalvars = []
                    for key in file.globalvars:
                        globalvars.append({"id": f"_ globalvar'{key}", "name": key, "icon":"img:icons/globalvar.png"})
                    nodes.append({"id": "_ globalvar", "name": "Globális változók", "icon":"img:icons/globalvar.png", "children": globalvars})
                with ui.row():
                    data_label = None
                    def _on_select(e):
                        if not select_object(e.value, file, data_label):
                            data_label._handle_content_change("")
                    with ui.scroll_area().classes("h-[70vh] w-[20vw]"):
                        ui.tree(nodes, label_key="name", on_select=_on_select).classes("scroll")
                    with ui.scroll_area().classes("h-[70vh] w-[70vw]"):
                        data_label = ui.html("").classes("")
        if has_graphics:
            with ui.tab_panel(graphics):
                graphics_tabs = []
                with ui.scroll_area().classes("h-[8.3vh] w-full"):
                    with ui.tabs() as gtabs:
                        for i in range(len(graphicsfile.graphics)):
                            graphics_tabs.append(ui.tab(str(i+1)))
                with ui.tab_panels(gtabs, value=graphics_tabs[0]):
                    for i in range(len(graphics_tabs)):
                        g = graphicsfile.graphics[i]
                        with ui.tab_panel(graphics_tabs[i]):
                            with ui.row():
                                def view_frame(frame_row, alpha_checkbox, sl, axl, ayl, dl, frame_view, frame: LogoFrame):
                                    def view_image(img: LogoImage):
                                        frame_view.clear()
                                        alpha_checkbox.set_visibility(img.hasalpha)
                                        alpha_checkbox.click = lambda:view_image(img)
                                        sl.set_text(f"{img.width}x{img.height}")
                                        axl.set_text(f"Aktívpont X: {img.activex}")
                                        ayl.set_text(f"Aktívpont Y: {img.activey}")
                                        dl.set_text(f"Késleltetés: {img.delay}")
                                        with frame_view:
                                            if img.hasalpha and alpha_checkbox.value:
                                                ui.image("data:image/bmp;base64," + base64.b64encode(img.alpha).decode("utf-8")).style("border: 1px solid black;").props("fit=fill")
                                            else:
                                                ui.image("data:image/bmp;base64," + img_base64(img)).style("border: 1px solid black;").props("fit=fill")
                                    frame_row.clear()
                                    frame_view.clear()
                                    with frame_row:
                                        with ui.row().classes("no-wrap w-full"):
                                            for img in frame.images:
                                                width = IMAGE_HEIGHT*(img.width/img.height)
                                                ui.image("data:image/bmp;base64," + img_base64(img)).style("border: 1px solid black; cursor: pointer;").props(f"height={IMAGE_HEIGHT}px width={width}px fit=fill").on("click", lambda i=img:view_image(i))
                                with ui.column():
                                    ui.label(f"Nullszög: {g.angle0}°")
                                    with ui.row():
                                        repeatcb = ui.checkbox("Animáció ismétlése")
                                        repeatcb.set_value(g.repeat)
                                        repeatcb.set_enabled(False)
                                        compasscb = ui.checkbox("Iránytű mód")
                                        compasscb.set_value(g.compass)
                                        compasscb.set_enabled(False)
                                    frames_area = ui.scroll_area().classes("h-[59vh] w-[20vw]")
                                with ui.column():
                                    fr = ui.scroll_area().classes(f"h-[{IMAGE_HEIGHT+32}px] w-[70vw]")
                                    with ui.row():
                                        sizelabel = ui.label("")
                                        axlabel = ui.label("")
                                        aylabel = ui.label("")
                                        delaylabel = ui.label("")
                                    alphacb = ui.checkbox("Átlátszósági maszk").on("click", lambda e:e.sender.click())
                                    alphacb.click = lambda: None
                                    alphacb.set_visibility(False)
                                    fw = ui.scroll_area().classes("h-[59vh] w-[70vw]")        
                                with frames_area:
                                    for i in range(len(g.frames)):
                                        frame = g.frames[i]
                                        if len(frame.images) > 1:
                                            b64 = "data:image/gif;base64," + base64.b64encode(create_gif(map(lambda x:x.get_alpha_bmp(), frame.images))).decode("utf-8")
                                        else:
                                            b64 = "data:image/bmp;base64," + img_base64(frame.images[0])
                                        ui.image(b64).style("border: 1px solid black; cursor: pointer;").props("fit=fill").on("click", lambda r=fr,acb=alphacb,sl=sizelabel,axl=axlabel,ayl=aylabel,dl=delaylabel,v=fw,f=frame:view_frame(r,acb,sl,axl,ayl,dl,v,f))

def try_upload(e: events.UploadEventArguments):
    try:
        handle_upload(e)
    except Exception as e:
        ui.label("Hiba: " + str(e)).classes("text-negative")
        ui.button("Új fájl", on_click=lambda: ui.run_javascript('location.reload();'))
        raise e

@ui.page("/")
def home():
    ui.add_css(".q-tree__icon {width: 23px !IMPORTANT; height: 14px !IMPORTANT;} .nicegui-content, .q-tab-panel {padding-bottom: 0 !IMPORTANT;}")
    ui.upload(on_upload=try_upload, label="Fájl feltöltése (IMP/LGF)").props('accept=".IMP,.lgf"').classes('max-w-full')

def run(host: str = "localhost", port: int = 8080, native: bool = False):
    app.add_static_files("/icons", "gui/icons")
    
    ui.run(host = host, port = port, native = native, title="Imagine Logo szerkesztő", favicon="https://qkrisi.hu/logo/editor/icons/favicon.ico", show = False, show_welcome_message = False)
