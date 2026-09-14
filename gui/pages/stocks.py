# gui/pages/stocks.py
import threading
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QLabel,
)


class _Sig(QObject):
    text = Signal(str)
    card = Signal(str, str)


class StocksPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sig = _Sig()
        self._sig.text.connect(self._set_detail)
        self._sig.card.connect(self._set_card)
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        title = QLabel("Stocks")
        title.setObjectName("Title")
        root.addWidget(title)
        hint = QLabel("Look up a ticker, or ask Helion in chat for a take.")
        hint.setObjectName("Eyebrow")
        root.addWidget(hint)

        bar = QHBoxLayout()
        self._entry = QLineEdit()
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
        ref = QPushButton("Refresh")
        ref.setObjectName("Action")
        ref.clicked.connect(self.refresh)
        bar.addWidget(ref)
        root.addLayout(bar)

        chips = QHBoxLayout()
        for sym in ["BTC-USD", "ETH-USD", "AAPL", "TSLA", "MSFT", "NIFTY50.NS", "RELIANCE.NS"]:
            b = QPushButton(sym)
            b.setObjectName("Action")
            b.clicked.connect(lambda _=False, s=sym: self.quick(s))
            chips.addWidget(b)
        chips.addStretch(1)
        root.addLayout(chips)

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
        self._detail.setPlainText("Pick a ticker or look one up. Chat with Helion if you want a take on the numbers.")
        body.addWidget(self._detail, 1)
        root.addLayout(body, 1)

    def quick(self, symbol: str):
        self._entry.setText(symbol)
        self.lookup()

    def lookup(self):
        symbol = self._entry.text().strip().upper()
        if not symbol:
            return
        self._detail.setPlainText(f"Fetching {symbol}…")
        threading.Thread(target=self._fetch, args=(symbol,), daemon=True).start()

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
