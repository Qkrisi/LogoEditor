from typing import Final

SETTINGS: Final[list[str]] = ['', 'apoz', 'xpozíció', 'ypozíció', 'poz', 'méret', 'szélesség', 'magasság', 'leírás', 'engedélyezett', '???', 'érték', 'formázottszöveg', 'betûtípus', 'szín', 'háttérszín', 'szerkeszthetõ', 'átlátszó', 'szerkeszthetõmarad', 'aktívlap', 'felirat', 'felirat', 'egyszeri', 'stílus', 'lenn', 'mindfenn', 'lapos', 'csoport', 'kép', '???', 'min', 'max', 'érték', 'függõleges', 'kiindulópont', 'háttérvonalszín', 'háttérvonalvastagság', 'háttérkép', 'kiaktívalapon', 'háttérszín', 'irány', 'otthonállapot', 'xpozíció', 'ypozíció', 'töltõszín', 'töltõminta', 'toll', 'tollszín', 'tollvastagság', 'tollminta', 'tartománystílus', 'tartomány', 'képkocka', 'alak', 'alakméret', 'alakszín', 'animáció', 'betûtípus', 'átlátszóklikk', 'szülõkezelés', 'teljeskép', 'hangmenü', 'fõhangmenü', 'képkockaelem', 'vonszolható', 'érzékeny', 'ablakállapot', 'x', 'y', 'z', 'r', 'u', 'v', 'tartományX', 'tartományY', 'tartományZ', 'tartományR', 'tartományU', 'tartományV', 'holtjátékX', 'holtjátékY', 'holtjátékZ', 'holtjátékR', 'holtjátékU', 'holtjátékV', 'tengelyszám', 'gombszám', 'pov', 'gomb1', 'gomb2', 'gomb3', 'gomb4', 'gomb5', 'gomb6', 'gomb7', 'gomb8', 'gomb9', 'gomb10', 'gomb11', 'gomb12', 'gomb13', 'gomb14', 'gomb15', 'gomb16', 'gomb17', 'gomb18', 'gomb19', 'gomb20', 'gomb21', 'gomb22', 'gomb23', 'gomb24', 'gomb25', 'gomb26', 'gomb27', 'gomb28', 'gomb29', 'gomb30', 'gomb31', 'gomb32', 'képkockamód', 'háttérszín', 'csúszkaméret', 'háttérvonalminta', 'kijelölt', 'kijelöltszöveg', 'sebességXY', 'sebesség', 'szög', 'készenlétijel', 'listakészenlétijel', 'láthatótartomány', '__name__', 'kapcsoló', 'csakaktív', 'átlátszó', 'fájlnév', 'mutatgombsor', 'webcím', 'maxméretû', 'stílus', 'kiszolgáló', 'azonosító', 'port', 'csatolások', 'törzs', 'feladó', 'feladónév', 'válaszcím', 'tárgy', 'címzett', 'vakmásolat', 'másolat', 'mutateszköztár', 'szerver', 'késleltetszorzó', 'pozíció', 'lejátszásállapot', 'stílus', 'port', 'vezéreltobjektum', 'igazítás', 'sorrend', 'felirat', 'mutatcímsor', 'felirat', 'mutatcímsor', 'maxméretû', 'stílus', 'végrehajtható', 'becenév', '???', 'szám', 'keretszín', 'fogadparancs', 'fogadgombmenü', 'gombmenü', 'fogadhangmenü', 'rögzített', 'megállítható', 'értékkelnõ', 'egysoros', 'képernyõállapot', 'fõeszközsorlátszik', 'rajzeszközsorlátszik', 'parancsnév', 'port', 'baudráta', 'adatbitek', 'stopbitek', 'paritás', 'RTSCTS', 'XONXOFF', 'aszinkrbemenet', 'csatlakozott']

COMMAND_NEW: Final[str] = ".új."
COMMAND_NEWCLASS: Final[str] = "újosztály"
COMMAND_GLOBALVAR: Final[str] = "globálisváltozó"
COMMAND_FIELDS: Final[str] = "mezõk!"
COMMAND_WINDOWSTATE: Final[str] = ".állapot!."
COMMAND_ACTIVETURTLE: Final[str] = "kiaktívalapon!"

SETTING_SELFDEFINE: Final[str] = "sajáteljárás'"
SETTING_EVENT: Final[str] = "esemény'"
SETTING_OWNVAR: Final[str] = "saját'"
SETTING_COMMONVAR: Final[str] = "közös'"

CLASS_MAIN: Final[str] = "fõ"
CLASS_MAINWINDOW: Final[str] = "fõablak"
CLASS_PAGE: Final[str] = "lap"
CLASS_PANE: Final[str] = "panel"
CLASS_TOOLBAR: Final[str] = "eszközsor"
CLASS_TURTLE: Final[str] = "teknõc"
CLASS_TEXTBOX: Final[str] = "szövegdoboz"
CLASS_SLIDER: Final[str] = "csúszka"
CLASS_BUTTON: Final[str] = "gomb"
CLASS_TOOLBUTTON: Final[str] = "eszközgomb"
CLASS_WEB: Final[str] = "web"
CLASS_MEDIAPLAYER: Final[str] = "médialejátszó"
CLASS_NET: Final[str] = "háló"
CLASS_JOYSTICK: Final[str] = "joystick"
CLASS_COMMPORT: Final[str] = "commport"
CLASS_OLEOBJECT: Final[str] = "oleobject"
