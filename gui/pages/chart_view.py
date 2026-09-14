# gui/pages/chart_view.py
"""Price chart + volume-at-price profile."""
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget

from gui.theme import C


class MarketChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None
        self.setMinimumHeight(280)

    def set_data(self, data: dict | None):
        self._data = data
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QColor(C["bg"]))
        if not self._data or not self._data.get("bars"):
            p.setPen(QColor(C["text_dim"]))
            p.drawText(self.rect(), Qt.AlignCenter, "Look up a symbol to load the live chart.")
            p.end()
            return

        bars = self._data["bars"]
        profile = self._data.get("profile") or {}
        w, h = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 12, 88, 28, 36
        chart_w = w - pad_l - pad_r
        chart_h = h - pad_t - pad_b
        if chart_w < 40 or chart_h < 40:
            p.end()
            return

        prices = [b["c"] for b in bars]
        lo, hi = min(b["l"] for b in bars), max(b["h"] for b in bars)
        if hi <= lo:
            hi = lo + 1
        vols = [b["v"] for b in bars]
        vmax = max(vols) or 1

        def y_at(price):
            return pad_t + (hi - price) / (hi - lo) * chart_h

        # Volume bars
        bw = max(1.0, chart_w / max(len(bars), 1))
        vol_h = chart_h * 0.22
        for i, b in enumerate(bars):
            x = pad_l + i * bw
            vh = (b["v"] / vmax) * vol_h
            up = b["c"] >= b["o"]
            col = QColor(C["green"] if up else C["red"])
            col.setAlpha(90)
            p.fillRect(QRectF(x, pad_t + chart_h - vh, max(bw - 0.5, 1), vh), col)

        # Close line
        pen = QPen(QColor(C["accent"]))
        pen.setWidthF(1.6)
        p.setPen(pen)
        last = None
        for i, b in enumerate(bars):
            x = pad_l + i * bw + bw * 0.5
            y = y_at(b["c"])
            pt = (x, y)
            if last:
                p.drawLine(last[0], last[1], pt[0], pt[1])
            last = pt

        # Market profile (right)
        buckets = profile.get("buckets") or []
        max_pv = max((x["vol"] for x in buckets), default=1) or 1
        px0 = w - pad_r + 6
        max_bar = pad_r - 16
        poc = profile.get("poc")
        val, vah = profile.get("val"), profile.get("vah")
        for bkt in buckets:
            y = y_at(bkt["price"])
            ww = (bkt["vol"] / max_pv) * max_bar
            col = QColor(C["accent"])
            col.setAlpha(70)
            if poc and abs(bkt["price"] - poc) < (hi - lo) / 40:
                col.setAlpha(180)
            p.fillRect(QRectF(px0, y - 3, ww, 6), col)

        if poc:
            p.setPen(QPen(QColor(C["accent"]), 1, Qt.DashLine))
            p.drawLine(pad_l, y_at(poc), w - pad_r, y_at(poc))
        if val and vah:
            shade = QColor(C["accent"])
            shade.setAlpha(18)
            p.fillRect(QRectF(pad_l, y_at(vah), chart_w, y_at(val) - y_at(vah)), shade)

        p.setPen(QColor(C["text"]))
        p.setFont(QFont("Segoe UI", 10))
        name = self._data.get("name") or self._data.get("symbol")
        price = self._data.get("price")
        title = f"{name}"
        if price is not None:
            title += f"  {price:,.2f} {self._data.get('currency') or ''}"
        p.drawText(12, 18, title)
        p.setPen(QColor(C["text_dim"]))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(w - pad_r + 4, 18, "Vol@px")
        p.end()
