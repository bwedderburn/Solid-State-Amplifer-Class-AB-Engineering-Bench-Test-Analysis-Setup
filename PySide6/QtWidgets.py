# Minimal subset of QtWidgets API used in tests
class _Base:
    def __init__(self,*a,**k): pass
    def setReadOnly(self, *a, **k): pass
    def addWidget(self, *a, **k): pass
    def addLayout(self, *a, **k): pass
    def addItems(self, *a, **k): pass
    def setMaximumWidth(self, *a, **k): pass
    def setMaximumHeight(self, *a, **k): pass
    def clicked(self): return self
    def connect(self, *a, **k): pass
    def setEnabled(self, *a, **k): pass
    def setFont(self, *a, **k): pass
    def __getattr__(self, name):
        def _noop(*a, **k):
            return None
        return _noop

class QApplication:
    _inst=None
    def __init__(self, *a, **k): QApplication._inst=self
    @staticmethod
    def instance(): return QApplication._inst
    def applicationName(self): return "stub"

class QWidget(_Base):
    pass


class QTabWidget(_Base):
    def __init__(self, *a, **k):
        self._tabs = []

    def addTab(self, widget, title):
        self._tabs.append((widget, title))
        return len(self._tabs) - 1


class QVBoxLayout(_Base):
    def addSpacing(self, *a, **k):
        pass


class QHBoxLayout(_Base):
    def addSpacing(self, *a, **k):
        pass
class QLabel(_Base):
    def __init__(self, text="", **kwargs):
        self.text = text
        self._alignment = None

    def setAlignment(self, align):
        self._alignment = align
class QCheckBox(_Base):
    def __init__(self, text=""):
        self.text = text
        self._checked = False

    def setChecked(self, val: bool):
        self._checked = bool(val)

    def isChecked(self):
        return self._checked
class QSpinBox(_Base):
    def __init__(self, *a, **k):
        self._min = 0
        self._max = 99
        self._val = 0

    def setRange(self, a, b):
        self._min, self._max = a, b

    def setValue(self, v):
        self._val = v

    def value(self):
        return self._val
class QPushButton(_Base):
    class _Signal:
        def connect(self, *a, **k):
            pass

    def __init__(self, text=""):
        self.text = text
        self.clicked = QPushButton._Signal()
class QTextEdit(_Base):
    def __init__(self, *a, **k):
        self._content = ""
class QLineEdit(_Base):
    def __init__(self, text=""): self.text=text
class QComboBox(_Base):
    pass
