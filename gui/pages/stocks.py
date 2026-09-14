# gui/pages/stocks.py
import threading
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QLabel,
)
from gui.pages.chart_view import MarketChart


class _Sig(QObject):
    text = Signal(str)
    card = Signal(str, str)
    chart = Signal(object)


class StocksPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._symbol = "BTC-USD"
        self._range = "5d"
        self._sig = _Sig()
        self._sig.text.connect(self._set_detail)
        self._sig.card.connect(self._set_card)
        self._sig.chart.connect(self._set_chart)
        self._build()
        self._timer = QTimer(self)
        self._timer.setInterval(45000)
        self._timer.timeout.connect(self._refresh_chart)
        self.refresh()
        self.lookup()

    def showEvent(self, e):
        super().showEvent(e)
        self._timer.start()
        self._refresh_chart()

    def hideEvent(self, e):
        self._timer.stop()
        super().hideEvent(e)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(12)

        title = QLabel("Market")
        title.setObjectName("Title")
        root.addWidget(title)
        hint = QLabel("Live chart and volume-at-price. Refreshes while this page is open.")
        hint.setObjectName("Eyebrow")
        root.addWidget(hint)

        bar = QHBoxLayout()
        self._entry = QLineEdit("BTC-USD")
        self._entry.setPlaceholderText("Symbol — AAPL, BTC-USD, RELIANCE.NS")
        self._entry.returnPressed.connect(self.lookup)
        bar.addWidget(self._entry, 1)
        look = QPushButton("Look up")
        look.setObjectName("Primary")
        look.clicked.connect(self.lookup)
        bar.addWidget(look)
        add = QPushButton("Add to portfolio")
        add.setObjectName("Action")
        add.clicked.connect(self.add_symbol)
        bar.addWidget(add)
        root.addLayout(bar)

        chips = QHBoxLayout()
        for sym in ["BTC-USD", "ETH-USD", "AAPL", "TSLA", "MSFT", "NIFTY50.NS", "RELIANCE.NS"]:
            b = QPushButton(sym)
            b.setObjectName("Action")
            b.clicked.connect(lambda _=False, s=sym: self.quick(s))
            chips.addWidget(b)
        chips.addStretch(1)
        for rng, lab in (("1d", "1D"), ("5d", "5D"), ("1mo", "1M")):
            b = QPushButton(lab)
            b.setObjectName("Action")
            b.clicked.connect(lambda _=False, r=rng: self._set_range(r))
            chips.addWidget(b)
        root.addLayout(chips)

        self._chart = MarketChart()
        root.addWidget(self._chart, 2)

        body = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel("Portfolio"))
        self._list = QListWidget()
        self._list.itemClicked.connect(self._from_list)
        left.addWidget(self._list, 1)
        manage = QPushButton("Remove selected")
        manage.setObjectName("Action")
        manage.clicked.connect(self.remove_selected)
        left.addWidget(manage)
        body.addLayout(left, 0)

        self._detail = QTextEdit()
        self._detail.setObjectName("PageBody")
        self._detail.setReadOnly(True)
        self._detail.setMaximumHeight(140)
        body.addWidget(self._detail, 1)
        root.addLayout(body, 1)

    def _set_range(self, rng: str):
        self._range = rng
        self._refresh_chart()

    def quick(self, symbol: str):
        self._entry.setText(symbol)
        self.lookup()

    def lookup(self):
        symbol = self._entry.text().strip().upper()
        if not symbol:
            return
        self._symbol = symbol
        self._detail.setPlainText(f"Fetching {symbol}…")
        threading.Thread(target=self._fetch, args=(symbol,), daemon=True).start()
        self._refresh_chart()

    def _refresh_chart(self):
        symbol = (self._entry.text() or self._symbol or "").strip().upper()
        if not symbol:
            return
        rng = self._range
        threading.Thread(target=self._fetch_chart, args=(symbol, rng), daemon=True).start()

    def _fetch_chart(self, symbol, rng):
        try:
            from core.tools import get_chart_series
            data = get_chart_series(symbol, rng)
            self._sig.chart.emit(data)
        except Exception as e:
            self._sig.chart.emit({"bars": [], "error": str(e), "symbol": symbol})

    def _set_chart(self, data):
        if data and data.get("error") and not data.get("bars"):
            self._detail.setPlainText(f"Chart unavailable: {data.get('error')}")
        self._chart.set_data(data)

    def _fetch(self, symbol):
        from core.tools import _get_stock
        result = _get_stock({"symbol": symbol, "include_news": True}, None)
        self._sig.text.emit(result)

    def _set_detail(self, text: str):
        self._detail.setPlainText(text)

    def add_symbol(self):
        symbol = self._entry.text().strip().upper()
        if not symbol:
            return
        from core.memory import add_to_portfolio
        add_to_portfolio(symbol)
        self.refresh()

    def remove_selected(self):
        item = self._list.currentItem()
        if not item:
            return
        symbol = item.data(Qt.UserRole) or item.text().split()[0]
        from core.memory import remove_from_portfolio
        remove_from_portfolio(symbol)
        self.refresh()

    def _from_list(self, item):
        symbol = item.data(Qt.UserRole)
        if symbol:
            self.quick(symbol)

    def refresh(self):
        from core.memory import get_portfolio_symbols
        self._list.clear()
        symbols = get_portfolio_symbols()
        if not symbols:
            self._list.addItem("Nothing saved yet")
            return
        for sym in symbols:
            it = QListWidgetItem(sym)
            it.setData(Qt.UserRole, sym)
            self._list.addItem(it)
            threading.Thread(target=self._fill_card, args=(sym,), daemon=True).start()
        self._refresh_chart()

    def _set_card(self, symbol: str, label: str):
        for i in range(self._list.count()):
            it = self._list.item(i)
            if it and it.data(Qt.UserRole) == symbol:
                it.setText(label)
                break

    def _fill_card(self, symbol):
        try:
            from core.tools import _get_stock
            result = _get_stock({"symbol": symbol}, None)
            lines = result.split("\n")
            price_line = next((l for l in lines if "Price:" in l), "")
            change_line = next((l for l in lines if "Change:" in l), "")
            price = price_line.replace("Price:", "").strip().split()[-1] if price_line else "?"
            change = ""
            if change_line:
                parts = change_line.split()
                if len(parts) >= 2:
                    change = " ".join(parts[1:3])
            self._sig.card.emit(symbol, f"{symbol}   {price}  {change}")
        except Exception:
            pass
