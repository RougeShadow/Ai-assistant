# gui/hex_canvas.py
"""Interactive Decepticon wireframe that tilts toward the cursor."""
from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QPointF, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QTransform
from PySide6.QtWidgets import QWidget

from gui.theme import C

DECEPTICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "brand" / "decepticon.png"


def paint_hatch(p: QPainter, widget: QWidget):
    origin = widget.mapTo(widget.window() or widget, QPoint(0, 0))
    pen = QPen(QColor(255, 255, 255, 11))
    pen.setWidthF(1.0)
    p.setPen(pen)
    w, h = widget.width(), widget.height()
    step = 7
    ox = origin.x() % step
    for i in range(-h - step, w + h, step):
        x = i - ox
        p.drawLine(x, 0, x + h, h)


def decepticon_crest(w: float, h: float) -> QPainterPath:
    """Angular Decepticon-style crest in unit box, scaled to w x h.
    Coordinates leave empty corners so it does not read as a filled square.
    """
    def P(x, y):
        return QPointF(x * w, y * h)

    outer = QPainterPath()
    # Top spike
    outer.moveTo(P(0.50, 0.02))
    outer.lineTo(P(0.58, 0.14))
    outer.lineTo(P(0.72, 0.10))   # right horn
    outer.lineTo(P(0.88, 0.22))
    outer.lineTo(P(0.70, 0.26))
    outer.lineTo(P(0.84, 0.42))   # right wing
    outer.lineTo(P(0.62, 0.40))
    outer.lineTo(P(0.74, 0.62))
    outer.lineTo(P(0.58, 0.60))
    outer.lineTo(P(0.66, 0.82))   # right jaw
    outer.lineTo(P(0.50, 0.98))   # chin
    outer.lineTo(P(0.34, 0.82))
    outer.lineTo(P(0.42, 0.60))
    outer.lineTo(P(0.26, 0.62))
    outer.lineTo(P(0.38, 0.40))
    outer.lineTo(P(0.16, 0.42))
    outer.lineTo(P(0.30, 0.26))
    outer.lineTo(P(0.12, 0.22))
    outer.lineTo(P(0.28, 0.10))
    outer.lineTo(P(0.42, 0.14))
    outer.closeSubpath()

    eye = QPainterPath()
    eye.moveTo(P(0.50, 0.36))
    eye.lineTo(P(0.60, 0.54))
    eye.lineTo(P(0.40, 0.54))
    eye.closeSubpath()

    brow = QPainterPath()
    brow.moveTo(P(0.42, 0.28))
    brow.lineTo(P(0.50, 0.34))
    brow.lineTo(P(0.58, 0.28))
    brow.lineTo(P(0.50, 0.24))
    brow.closeSubpath()

    return outer.subtracted(eye).united(brow)


class BrandField(QWidget):
    """Layered wireframe crest; mouse-tilted; transparent, not a photo box."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setMouseTracking(True)
        self.setFixedSize(440, 400)
        self.setCursor(Qt.ArrowCursor)
        self._mx = 0.0
        self._my = 0.0
        self._tx = 0.0
        self._ty = 0.0
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _tick(self):
        self._t += 0.028
        self._tx += (self._mx - self._tx) * 0.14
        self._ty += (self._my - self._ty) * 0.14
        self.update()

    def mouseMoveEvent(self, event):
        self._set_pointer(event.position())
        super().mouseMoveEvent(event)

    def _set_pointer(self, pos):
        w = max(self.width(), 1)
        h = max(self.height(), 1)
        self._mx = max(-1.0, min(1.0, (pos.x() / w) * 2.0 - 1.0))
        self._my = max(-1.0, min(1.0, (pos.y() / h) * 2.0 - 1.0))

    def track_from_parent(self, parent_pos):
        local = self.mapFromParent(parent_pos)
        self._set_pointer(local)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        cx, cy = w * 0.5, h * 0.52
        s = min(w, h) * 0.86

        yaw = self._tx * 0.45
        pitch = self._ty * 0.32
        layers = 14
        for i in range(layers):
            t = i / (layers - 1)
            wave = math.sin(self._t * 1.35 + t * 5.5) * 0.012
            scale = s * (0.72 + t * 0.28 + wave * abs(self._tx) * 0.4)
            ox = (w - scale) / 2 + self._tx * (8 + t * 14)
            oy = (h - scale) / 2 + self._ty * (6 + t * 8) + math.sin(self._t + t * 3) * 2
            path = decepticon_crest(scale, scale)
            xform = QTransform()
            xform.translate(ox + scale * 0.5, oy + scale * 0.5)
            xform.rotate(yaw * 10)
            xform.scale(1.0 + pitch * 0.06, 1.0 - pitch * 0.08)
            xform.translate(-scale * 0.5, -scale * 0.5)
            path = xform.map(path)

            a = int(28 + t * 165)
            r_c = int(245 - t * 35)
            g_c = int(70 + t * 70)
            b_c = int(0 + t * 30)
            pen = QPen(QColor(r_c, g_c, b_c, a))
            pen.setWidthF(1.35 if t > 0.75 else 0.95)
            pen.setJoinStyle(Qt.MiterJoin)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)

            # sparse scanlines clipped to the crest (not a filled square)
            if t > 0.55:
                p.save()
                p.setClipPath(path)
                step = 7
                scan = QPen(QColor(r_c, g_c, b_c, int(a * 0.35)))
                scan.setWidthF(0.8)
                p.setPen(scan)
                top = int(path.boundingRect().top())
                bot = int(path.boundingRect().bottom())
                left = path.boundingRect().left()
                right = path.boundingRect().right()
                for y in range(top, bot, step):
                    wobble = math.sin(self._t * 1.6 + y * 0.05 + self._tx) * 2
                    p.drawLine(QPointF(left, y + wobble), QPointF(right, y + wobble))
                p.restore()
        p.end()


HexField = BrandField
