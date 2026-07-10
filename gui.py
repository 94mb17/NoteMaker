import math
import os
import re
import sys

import doced

from PySide6.QtCore import (
    Qt,
    QTimer,
    QPointF,
    QRectF,
    QRect,
    QObject,
    Signal,
)

import uuid

from PySide6.QtGui import (
    QColor,
    QBrush,
    QCursor,
    QFont,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
    QIcon,
    QAction,
    QPixmap,
)

from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QWidget,
    QFileDialog,
    QSystemTrayIcon,
    QMenu,
    QStyle,
)

import threading
import time

from pynput import mouse
from pynput.keyboard import Controller, Key

keyboard = Controller()

LONG_PRESS_DURATION = 0.7

_current_overlay = None
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
editor = doced.Editor()


#______________________________DRAW______________________________

def draw_heading(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    painter.setFont(QFont("Segoe UI", int(s * 0.75), QFont.Bold))
    painter.drawText(
        QRectF(x - s * 0.4, y - s * 0.4, s * 0.8, s * 0.8),
        Qt.AlignCenter,
        "H",
    )

def draw_bullet(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))

    for dy in (-0.28, 0.0, 0.28):
        yy = y + dy * s
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(x - s * 0.28, yy), 2, 2)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(
            QPointF(x - s * 0.15, yy),
            QPointF(x + s * 0.28, yy),
        )

def draw_image(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    painter.setBrush(Qt.NoBrush)

    w = s * 0.72
    h = s * 0.50
    top = y - h * 0.35

    painter.drawRect(QRectF(x - w / 2, top, w, h))
    painter.drawRect(
        QRectF(
            x - w * 0.16,
            top - h * 0.22,
            w * 0.32,
            h * 0.22,
        )
    )

    r = h * 0.32
    painter.drawEllipse(QPointF(x, top + h / 2), r, r)

def draw_link(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    painter.setBrush(Qt.NoBrush)

    r = s * 0.20

    painter.drawEllipse(QPointF(x - 5, y - 5), r, r)
    painter.drawEllipse(QPointF(x + 5, y + 5), r, r)

    painter.drawLine(
        QPointF(x - 3, y - 3),
        QPointF(x + 3, y + 3),
    )

def draw_view(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    painter.setBrush(Qt.NoBrush)

    w = s * 0.90
    h = s * 0.50

    rect = QRectF(
        x - w / 2,
        y - h / 2,
        w,
        h,
    )

    painter.drawArc(rect, 0, 180 * 16)
    painter.drawArc(rect, 180 * 16, 180 * 16)

    r = h * 0.32

    painter.setBrush(QBrush(color))
    painter.drawEllipse(QPointF(x, y), r, r)
    painter.setBrush(Qt.NoBrush)

def draw_save(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    painter.setBrush(Qt.NoBrush)

    w = s * 0.68

    left = x - w / 2
    top = y - w / 2

    painter.drawRect(QRectF(left, top, w, w))

    painter.drawRect(
        QRectF(
            x - w * 0.26,
            top,
            w * 0.52,
            w * 0.42,
        )
    )

    painter.drawRect(
        QRectF(
            x - w * 0.30,
            top + w * 0.58,
            w * 0.60,
            w * 0.34,
        )
    )

def draw_quit(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    painter.setBrush(Qt.NoBrush)

    r = s * 0.34

    rect = QRectF(
        x - r,
        y - r,
        2 * r,
        2 * r,
    )

    painter.drawArc(rect, 250 * 16, 260 * 16)

    painter.drawLine(
        QPointF(x, y - r - 3),
        QPointF(x, y - r * 0.15),
    )

def draw_undo(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    painter.setBrush(Qt.NoBrush)

    r = s * 0.32

    rect = QRectF(
        x - r,
        y - r,
        2 * r,
        2 * r,
    )

    painter.drawArc(rect, 40 * 16, 240 * 16)

    arrow = QPolygonF(
        [
            QPointF(x - r - 6, y - 2),
            QPointF(x - r + 2, y - 8),
            QPointF(x - r + 1, y + 4),
        ]
    )

    painter.setBrush(QBrush(color))
    painter.drawPolygon(arrow)
    painter.setBrush(Qt.NoBrush)

def draw_redo(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    painter.setBrush(Qt.NoBrush)

    r = s * 0.32

    rect = QRectF(
        x - r,
        y - r,
        2 * r,
        2 * r,
    )

    painter.drawArc(rect, 260 * 16, 240 * 16)

    arrow = QPolygonF(
        [
            QPointF(x + r + 6, y - 2),
            QPointF(x + r - 2, y - 8),
            QPointF(x + r - 1, y + 4),
        ]
    )

    painter.setBrush(QBrush(color))
    painter.drawPolygon(arrow)
    painter.setBrush(Qt.NoBrush)

def draw_folder(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    painter.setBrush(Qt.NoBrush)

    w = s * 0.90
    h = s * 0.60

    top = y - h * 0.30

    painter.drawRect(
        QRectF(
            x - w / 2,
            top - h * 0.28,
            w * 0.42,
            h * 0.28,
        )
    )

    painter.drawRect(
        QRectF(
            x - w / 2,
            top,
            w,
            h,
        )
    )

def draw_paragraph(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    painter.setBrush(Qt.NoBrush)

    font = QFont("Georgia", max(1, int(s * 0.95)), QFont.Bold)
    painter.setFont(font)

    painter.drawText(
        QRectF(
            x - s * 0.5,
            y - s * 0.5,
            s,
            s,
        ),
        Qt.AlignCenter,
        "\u00B6",
    )

def draw_bullet_dot(painter, x, y, s, color):
    """Filled dot + line — the 'Normal' bullet variant."""
    painter.setPen(QPen(color, 2))
    r = s * 0.14
    painter.setBrush(QBrush(color))
    painter.drawEllipse(QPointF(x - s * 0.32, y), r, r)
    painter.setBrush(Qt.NoBrush)
    painter.drawLine(QPointF(x - s * 0.10, y), QPointF(x + s * 0.34, y))

def draw_bullet_circle(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    painter.setBrush(Qt.NoBrush)
    r = s * 0.16
    painter.drawEllipse(QPointF(x - s * 0.32, y), r, r)
    painter.drawLine(QPointF(x - s * 0.10, y), QPointF(x + s * 0.34, y))

def draw_bullet_square(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    side = s * 0.28
    painter.setBrush(QBrush(color))
    painter.drawRect(QRectF(x - s * 0.32 - side / 2, y - side / 2, side, side))
    painter.setBrush(Qt.NoBrush)
    painter.drawLine(QPointF(x - s * 0.10, y), QPointF(x + s * 0.34, y))

def draw_bullet_check(painter, x, y, s, color):
    painter.setPen(QPen(color, 2))
    cx = x - s * 0.32
    cy = y
    painter.drawLine(QPointF(cx - s * 0.14, cy), QPointF(cx - s * 0.02, cy + s * 0.12))
    painter.drawLine(QPointF(cx - s * 0.02, cy + s * 0.12), QPointF(cx + s * 0.16, cy - s * 0.16))
    painter.drawLine(QPointF(x - s * 0.10, y), QPointF(x + s * 0.34, y))

def draw_icon(painter, name, x, y, size, color):
    painter.save()

    drawer = ICON_DRAWERS.get(name)

    if drawer is not None:
        drawer(painter, x, y, size, color)

    painter.restore()

def make_circle_icon(letter, diameter=64, bg_color="#2a6df5", fg_color="#ffffff"):
    pixmap = QPixmap(diameter, diameter)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(QColor(bg_color)))
    painter.drawEllipse(0, 0, diameter, diameter)

    painter.setPen(QPen(QColor(fg_color)))
    font = QFont("Segoe UI", int(diameter * 0.5), QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, letter)

    painter.end()
    return QIcon(pixmap)

ICON_DRAWERS = {
    "heading": draw_heading,
    "paragraph": draw_paragraph,
    "bullet": draw_bullet,
    "image": draw_image,
    "hyperlink": draw_link,
    "view": draw_view,
    "save": draw_save,
    "quit": draw_quit,
    "undo": draw_undo,
    "redo": draw_redo,
    "open": draw_folder,
    "bullet_dot": draw_bullet_dot,
    "bullet_circle": draw_bullet_circle,
    "bullet_square": draw_bullet_square,
    "bullet_check": draw_bullet_check,
}



# ____________________________POPUP DEFINE__________________________

class PopupController:

    def __init__(self):

        self.popup_open = False
        self.menu_active = False
        self.current_menu = None

popup_controller = PopupController()



# __________________________________THE ACTION SECTORS__________________________________

def quit_app():
    QTimer.singleShot(0, _do_quit)


def _do_quit():
    msg = QMessageBox()
    msg.setWindowTitle("Quit")
    msg.setText("Do you want to save your document before quitting?")

    save_btn = msg.addButton("Save", QMessageBox.AcceptRole)
    discard_btn = msg.addButton("Don't Save", QMessageBox.DestructiveRole)
    cancel_btn = msg.addButton("Cancel", QMessageBox.RejectRole)

    msg.exec()

    clicked = msg.clickedButton()

    if clicked == cancel_btn:
        return

    if clicked == discard_btn:
        editor.cache.delete()
        QApplication.quit()
        return

    if clicked == save_btn:
        if do_save():
            QApplication.quit()

def do_heading1(text):
    editor.execute(doced.Heading(text, 1))

def do_heading2(text):
    editor.execute(doced.Heading(text, 2))

def do_heading3(text):
    editor.execute(doced.Heading(text, 3))

def do_heading4(text):
    editor.execute(doced.Heading(text, 4))

def do_heading5(text):
    editor.execute(doced.Heading(text, 5))

def do_heading6(text):
    editor.execute(doced.Heading(text, 6))

def do_paragraph(text):
    editor.execute(doced.Paragraph(text))

def do_bullet_normal(text):
    editor.execute(doced.Bullet(text, symbol="bullet"))

def do_bullet_check(text):
    editor.execute(doced.Bullet(text, symbol="check"))

def do_bullet_square(text):
    editor.execute(doced.Bullet(text, symbol="square"))

def do_bullet_circle(text):
    editor.execute(doced.Bullet(text, symbol="circle"))

def do_hyperlink(url):
    editor.execute(doced.Hyperlink(url))

def undo_available(_):
    return len(editor.document.inuse) > 0


def redo_available(_):
    return len(editor.document.redo) > 0

def do_undo():
    editor.undo()

def do_redo():
    editor.redo()



# ____________________________SAVE____________________________

def show_save():
    QTimer.singleShot(0, do_save)

def ask_save_filename():

    filename, _ = QFileDialog.getSaveFileName(
        None,
        "Save Document",
        "document.docx",
        "Word Documents (*.docx)"
    )

    return filename or None

def do_save():

    filename = ask_save_filename()

    if filename is None:
        return False

    try:
        renderer = doced.WordRenderer()
        renderer.render(editor.document, filename, mode=editor.document.mode)
        editor.cache.delete()

        return True

    except Exception as e:
        QMessageBox.critical(
            None,
            "Save Failed",
            str(e),
        )
        return False
    


# ____________________________VIEW_______________________________

preview_window = None

def show_view():
    QTimer.singleShot(0, do_view)

def do_view():

    global preview_window

    renderer = doced.HtmlRenderer()

    filename = renderer.render(
        editor.document
    )

    if preview_window is None:
        preview_window = doced.PreviewWindow()

    preview_window.show_preview(filename)




# _____________________________OPEN__________________________________

def show_open():
    QTimer.singleShot(0, do_open)

def do_open():

    filename, _ = QFileDialog.getOpenFileName(
        None,
        "Select Word Document",
        "",
        "Word Documents (*.docx)",
    )

    if not filename:
        return

    editor.document.filename = filename
    editor.document.mode = "append"

def text_only(content):
    return content is not None and content[0] == "text"

def always(_):
    return True

URL_PATTERN = re.compile(r"^(https?://|www\.)\S+$", re.IGNORECASE)

def hyperlink_only(content):

    return (
        content is not None
        and content[0] == "text"
        and URL_PATTERN.match(content[1].strip())
    )




# _____________________IMAGE_____________________

def capture(left, top, right, bottom):
    try:
        filename = os.path.join(
            doced.IMAGE_DIR,
            f"{uuid.uuid4()}.png",
        )

        screen = QGuiApplication.primaryScreen()
        pixmap = screen.grabWindow(
            0,
            int(left),
            int(top),
            int(right - left),
            int(bottom - top),
        )
        pixmap.save(filename)

        editor.execute(doced.Image(filename))

    except Exception as e:
        print(f"Screenshot failed: {e}")



class ScreenshotOverlay(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setWindowOpacity(0.3)
        self.setCursor(Qt.CrossCursor)
        self.setStyleSheet("background-color: black;")

        virt_rect = QRect()
        for screen in QGuiApplication.screens():
            virt_rect = virt_rect.united(screen.geometry())
        self.setGeometry(virt_rect)

        self._pressed = False
        self._start = QPointF()
        self._current = QPointF()

    def paintEvent(self, event):
        if not self._pressed:
            return
        painter = QPainter(self)
        painter.setPen(QPen(QColor("red"), 2))
        painter.setBrush(Qt.NoBrush)
        rect = QRectF(self._start, self._current).normalized()
        painter.drawRect(rect)

    def mousePressEvent(self, event):
        self._pressed = True
        self._start = event.position()
        self._current = event.position()
        self.update()

    def mouseMoveEvent(self, event):
        if self._pressed:
            self._current = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        global _current_overlay
        if not self._pressed:
            print("[screenshot] ignoring stray release with no matching press")
            return
        self._pressed = False

        rect = QRectF(self._start, event.position()).normalized()
        abs_left = self.x() + rect.left()
        abs_top = self.y() + rect.top()
        abs_right = self.x() + rect.right()
        abs_bottom = self.y() + rect.bottom()

        if rect.width() < 5 or rect.height() < 5:
            print("[screenshot] selection too small, cancelled")
            return

        self.close()

        QTimer.singleShot(
            150,
            lambda: capture(abs_left, abs_top, abs_right, abs_bottom),
        )

        _current_overlay = None

    def keyPressEvent(self, event):
        global _current_overlay
        if event.key() == Qt.Key_Escape:
            self.close()
            _current_overlay = None


def show_insert_image():
    QTimer.singleShot(0, do_insert_image)

def do_insert_image():
    global _current_overlay

    if _current_overlay is not None:
        return

    _current_overlay = ScreenshotOverlay()
    _current_overlay.show()




# _______________________SECTORS_______________________


LEFT_SECTOR_DEFS = [
    {
        "key": "heading",
        "label": "Heading",
        "icon": "heading",
        "enabled": text_only,
        "submenu": [
            {"key": "heading1", "label": "H1", "icon": "heading", "command": do_heading1},
            {"key": "heading2", "label": "H2", "icon": "heading", "command": do_heading2},
            {"key": "heading3", "label": "H3", "icon": "heading", "command": do_heading3},
            {"key": "heading4", "label": "H4", "icon": "heading", "command": do_heading4},
            {"key": "heading5", "label": "H5", "icon": "heading", "command": do_heading5},
            {"key": "heading6", "label": "H6", "icon": "heading", "command": do_heading6},
        ],
    },
    {
        "key": "bullet",
        "label": "Bullet",
        "icon": "bullet",
        "enabled": text_only,
        "submenu": [
            {"key": "bullet_normal", "label": "Normal", "icon": "bullet_dot", "command": do_bullet_normal},
            {"key": "bullet_check", "label": "Check", "icon": "bullet_check", "command": do_bullet_check},
            {"key": "bullet_square", "label": "Square", "icon": "bullet_square", "command": do_bullet_square},
            {"key": "bullet_circle", "label": "Circle", "icon": "bullet_circle", "command": do_bullet_circle},
        ],
    },
    {
        "key": "paragraph",
        "label": "Paragraph",
        "icon": "paragraph",
        "enabled": text_only,
        "command": do_paragraph,
    },
    {
        "key": "hyperlink",
        "label": "Hyperlink",
        "icon": "hyperlink",
        "enabled": hyperlink_only,
        "command": do_hyperlink,
    },
    {
        "key": "screenshot",
        "label": "Screenshot",
        "icon": "image",
        "enabled": always,
        "command": show_insert_image,
    },
]

RIGHT_SECTOR_DEFS = [
    {
        "key": "quit",
        "label": "Quit",
        "icon": "quit",
        "enabled": always,
        "command": quit_app,
    },
    {
        "key": "save",
        "label": "Save",
        "icon": "save",
        "enabled": always,
        "command": show_save,
    },
    {
        "key": "view",
        "label": "View",
        "icon": "view",
        "enabled": always,
        "command": show_view,
    },
    {
        "key": "open",
        "label": "Open",
        "icon": "open",
        "enabled": always,
        "command": show_open,
    },
    {
        "key": "undo",
        "label": "Undo",
        "icon": "undo",
        "enabled": undo_available,
        "command": do_undo,
    },
    {
        "key": "redo",
        "label": "Redo",
        "icon": "redo",
        "enabled": redo_available,
        "command": do_redo,
    },
]

# Which sector list + visual theme belongs to which trigger button.
SIDE_SECTORS = {
    "left": LEFT_SECTOR_DEFS,
    "right": RIGHT_SECTOR_DEFS,
}

SIDE_THEME = {
    "left": "cyan",
    "right": "grey",
}


# ____________________ Radial Menu ____________________


WEDGE_PALETTE = {
    "fill": QColor(22, 26, 33, 235),
    "fill_dim": QColor(16, 19, 24, 225),
    "fill_disabled": QColor(13, 14, 17, 200),
    "gold_a": QColor("#f3c063"),
    "gold_b": QColor("#c9862a"),
    "divider": QColor(150, 168, 210, 110),
    "icon": QColor("#e9ecf5"),
    "icon_disabled": QColor("#454952"),
    "icon_on_gold": QColor("#2a1a05"),
    "text": QColor("#e9ecf5"),
    "text_dim": QColor("#8a8f9b"),
    "text_disabled": QColor("#4a4e55"),
    "text_on_gold": QColor("#2a1a05"),
    "hub_fill": QColor(12, 14, 18, 240),
    "title": QColor("#ffffff"),
    "subtitle": QColor("#9aa2b1"),
}

ACCENT_BY_THEME = {
    "cyan": QColor("#5adcff"),
    "grey": QColor("#c9c9cc"),
}

HUB_R = 58           
RING_BW = 78           
WEDGE_MARGIN = 26     


class RadialMenu(QWidget):

    def __init__(
        self,
        cx,
        cy,
        root_items,
        on_cancel,
        popup_controller,
        theme="cyan",
        title="Menu",
        subtitle="",
    ):
        super().__init__()

        self.popup_controller = popup_controller
        self.on_cancel = on_cancel
        self._result = None

        self.accent = ACCENT_BY_THEME.get(theme, ACCENT_BY_THEME["cyan"])

        self.root_title = title
        self.root_subtitle = subtitle

        self.rings = [root_items]     # rings[i] = items shown in ring i
        self.path = []                # rings[i]'s chosen index, for i < len(path)
        self.chosen_items = []        # the chosen item dict at each drilled level

        self.hover = None             # (ring_index, item_index)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        max_depth = self._max_depth(root_items)
        outer_r = HUB_R + max_depth * RING_BW
        size = int((outer_r + WEDGE_MARGIN) * 2)
        self.center = size / 2

        self.setFixedSize(size, size)
        self.move(int(cx - self.center), int(cy - self.center))

        self._update_hub_text()


    def _max_depth(self, items):
        depth = 1
        for it in items:
            if it.get("submenu"):
                depth = max(depth, 1 + self._max_depth(it["submenu"]))
        return depth

    def _point(self, r, angle_deg):
        c = self.center
        rad = math.radians(angle_deg)
        return QPointF(c + r * math.cos(rad), c - r * math.sin(rad))

    def _ring_bounds(self, ring_index):
        r_inner = HUB_R + ring_index * RING_BW
        r_outer = r_inner + RING_BW
        return r_inner, r_outer

    def _wedge_start(self, n, j):
        angle_per = 360 / n
        return 90 - j * angle_per, -angle_per

    def _update_hub_text(self):
        if self.chosen_items:
            self.title_text = self.chosen_items[-1]["label"]
            self.subtitle_text = " \u203A ".join(
                [self.root_title] + [c["label"] for c in self.chosen_items[:-1]]
            ) or self.root_title
        else:
            self.title_text = self.root_title
            self.subtitle_text = self.root_subtitle


    def _hit_test(self, x, y):
        dx = x - self.center
        dy = y - self.center
        dist = math.hypot(dx, dy)

        if dist <= HUB_R:
            return ("hub", None, None)

        theta = math.degrees(math.atan2(-dy, dx)) % 360

        for i, items in enumerate(self.rings):
            r_inner, r_outer = self._ring_bounds(i)
            if r_inner < dist <= r_outer:
                n = len(items)
                if n == 0:
                    return ("outside", None, None)
                angle_per = 360 / n
                rel = (90 - theta) % 360
                j = int(rel // angle_per) % n
                return ("ring", i, j)

        return ("outside", None, None)


    def _wedge_path(self, r_inner, r_outer, start_deg, span_deg):
        c = self.center
        outer_rect = QRectF(c - r_outer, c - r_outer, 2 * r_outer, 2 * r_outer)
        inner_rect = QRectF(c - r_inner, c - r_inner, 2 * r_inner, 2 * r_inner)

        path = QPainterPath()
        path.moveTo(self._point(r_outer, start_deg))
        path.arcTo(outer_rect, start_deg, span_deg)
        path.lineTo(self._point(r_inner, start_deg + span_deg))
        path.arcTo(inner_rect, start_deg + span_deg, -span_deg)
        path.closeSubpath()
        return path

    def _paint_ring(self, painter, ring_index):
        items = self.rings[ring_index]
        n = len(items)
        if n == 0:
            return

        r_inner, r_outer = self._ring_bounds(ring_index)
        p = WEDGE_PALETTE
        is_chosen_ring = ring_index < len(self.path)

        for j, item in enumerate(items):
            start_deg, span_deg = self._wedge_start(n, j)
            wedge = self._wedge_path(r_inner, r_outer, start_deg, span_deg)

            enabled = item.get("enabled", True)
            is_chosen = is_chosen_ring and self.path[ring_index] == j
            is_hovered = self.hover == (ring_index, j)
            gold = enabled and (is_chosen or is_hovered)

            if not enabled:
                fill = p["fill_disabled"]
            elif gold:
                grad = QRadialGradient(self.center, self.center, r_outer)
                grad.setColorAt(0.0, p["gold_a"])
                grad.setColorAt(1.0, p["gold_b"])
                fill = QBrush(grad)
            else:
                fill = p["fill"] if ring_index == len(self.rings) - 1 else p["fill_dim"]

            painter.setPen(QPen(p["divider"], 1.2))
            painter.setBrush(QBrush(fill) if not isinstance(fill, QBrush) else fill)
            painter.drawPath(wedge)

            if not enabled:
                icon_color, text_color = p["icon_disabled"], p["text_disabled"]
            elif gold:
                icon_color, text_color = p["icon_on_gold"], p["text_on_gold"]
            else:
                icon_color, text_color = p["icon"], (p["text"] if ring_index == len(self.rings) - 1 else p["text_dim"])

            mid_angle = start_deg + span_deg / 2
            icon_pt = self._point(r_inner + RING_BW * 0.36, mid_angle)
            label_pt = self._point(r_inner + RING_BW * 0.76, mid_angle)

            icon_scale = min(24, RING_BW * 0.3)
            draw_icon(painter, item.get("icon", ""), icon_pt.x(), icon_pt.y(), icon_scale, icon_color)

            painter.setPen(QPen(text_color))
            painter.setFont(QFont("Segoe UI", 7, QFont.DemiBold))
            label_w = min(80, RING_BW + 10)
            label_rect = QRectF(label_pt.x() - label_w / 2, label_pt.y() - 9, label_w, 18)
            painter.drawText(label_rect, Qt.AlignCenter, item.get("label", ""))

            if item.get("submenu") and enabled:
                dot_pt = self._point(r_outer - 8, mid_angle)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(icon_color))
                painter.drawEllipse(dot_pt, 2.2, 2.2)

    def _paint_hub(self, painter):
        c = self.center
        p = WEDGE_PALETTE

        painter.setPen(QPen(self.accent, 2))
        painter.setBrush(QBrush(p["hub_fill"]))
        painter.drawEllipse(QPointF(c, c), HUB_R, HUB_R)

        painter.setPen(QPen(QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 90), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(c, c), HUB_R - 6, HUB_R - 6)

        painter.setPen(QPen(p["title"]))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(
            QRectF(c - HUB_R + 8, c - 22, 2 * HUB_R - 16, 20),
            Qt.AlignCenter,
            self.title_text,
        )

        painter.setPen(QPen(p["subtitle"]))
        painter.setFont(QFont("Segoe UI", 6, QFont.Normal))
        painter.drawText(
            QRectF(c - HUB_R + 8, c - 2, 2 * HUB_R - 16, 16),
            Qt.AlignCenter,
            self.subtitle_text,
        )

        chev_y = c + HUB_R * 0.42
        painter.setPen(QPen(p["subtitle"], 2))
        if self.path:
            painter.drawLine(QPointF(c + 5, chev_y - 5), QPointF(c - 3, chev_y))
            painter.drawLine(QPointF(c - 3, chev_y), QPointF(c + 5, chev_y + 5))
        else:
            d = 4
            painter.drawLine(QPointF(c - d, chev_y - d), QPointF(c + d, chev_y + d))
            painter.drawLine(QPointF(c - d, chev_y + d), QPointF(c + d, chev_y - d))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        c = self.center

        for i in range(len(self.rings)):
            self._paint_ring(painter, i)

        self._paint_hub(painter)


    def _select(self, ring_index, item_index):
        item = self.rings[ring_index][item_index]

        if not item.get("enabled", True):
            return

        if ring_index < len(self.path) and self.path[ring_index] == item_index:
            return

        self.path = self.path[:ring_index]
        self.rings = self.rings[:ring_index + 1]
        self.chosen_items = self.chosen_items[:ring_index]

        if item.get("submenu"):
            self.path.append(item_index)
            self.chosen_items.append(item)
            self.rings.append(item["submenu"])
            self.hover = None
            self._update_hub_text()
            self.update()
        else:
            self._result = item
            self.close()

    def _go_back(self):
        if not self.path:
            self._result = None
            self.close()
            return

        self.path.pop()
        self.rings = self.rings[:len(self.path) + 1]
        if self.chosen_items:
            self.chosen_items.pop()
        self._update_hub_text()
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position()
        kind, i, j = self._hit_test(pos.x(), pos.y())
        new_hover = (i, j) if kind == "ring" else None
        if new_hover != self.hover:
            self.hover = new_hover
            self.update()

    def mousePressEvent(self, event):
        pos = event.position()
        kind, i, j = self._hit_test(pos.x(), pos.y())

        if kind == "hub":
            self._go_back()
        elif kind == "ring":
            self._select(i, j)
        else:
            self._result = None
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._result = None
            self.close()

    def closeEvent(self, event):
        self.popup_controller.current_menu = None
        if self._result is not None:
            self._result["command"]()
        else:
            self.on_cancel()
        event.accept()


# ______________________________SHOWPOPUP______________________________

MENU_COPY = {
    "left": {"title": "Format Menu", "subtitle": "Insert into document"},
    "right": {"title": "Action Menu", "subtitle": "File & history"},
}


def show_popup(content, side="left"):
    if popup_controller.popup_open:
        return

    popup_controller.popup_open = True
    popup_controller.menu_active = True
    pos = QCursor.pos()

    def finish():
        popup_controller.popup_open = False
        QTimer.singleShot(300, lambda: setattr(popup_controller, "menu_active", False))

    TEXT_COMMANDS = {do_heading1, do_heading2, do_heading3, do_heading4,
                     do_heading5, do_heading6, do_paragraph, do_hyperlink,
                     do_bullet_normal, do_bullet_check, do_bullet_square, do_bullet_circle}

    def leaf(func, content):
        def wrapper():
            if func is None:
                return
            if func in TEXT_COMMANDS:
                func(content[1])
            else:
                func()
            finish()
        return wrapper

    def build_sector(item):
        sector = {
            "label": item["label"],
            "icon": item["icon"],
            "enabled": item["enabled"](content) if item.get("enabled") else True,
            "command": leaf(item.get("command"), content),
        }
        if "submenu" in item:
            sector["submenu"] = [
                {
                    "label": sub["label"],
                    "icon": sub["icon"],
                    "enabled": True,
                    "command": leaf(sub["command"], content),
                }
                for sub in item["submenu"]
            ]
        return sector

    sector_defs = SIDE_SECTORS.get(side, LEFT_SECTOR_DEFS)
    theme = SIDE_THEME.get(side, "cyan")
    copy = MENU_COPY.get(side, MENU_COPY["left"])

    sectors = [build_sector(item) for item in sector_defs]

    popup_controller.current_menu = RadialMenu(
        pos.x(), pos.y(), sectors, finish, popup_controller,
        theme=theme, title=copy["title"], subtitle=copy["subtitle"],
    )
    popup_controller.current_menu.show()





# _________________RECOVERY_________________

if os.path.exists(editor.cache.filename):

    msg = QMessageBox()

    msg.setWindowTitle("Recover Session")
    msg.setText("An unsaved document was found.")

    recover = msg.addButton("Recover", QMessageBox.AcceptRole)
    discard = msg.addButton("Discard", QMessageBox.DestructiveRole)

    msg.exec()

    clicked = msg.clickedButton()

    if clicked == recover:
        editor.cache.recover(editor.document)

    else:
        editor.cache.delete()



# _____________________________BRIDGE___________________________



# ---------------- Cross-thread bridge ----------------
# The mouse listener and long-press timer run on background threads, but all
# Qt widgets must be created/shown on the main (Qt) thread. Emitting a signal
# from a background thread and connecting it to a slot that lives on an
# object owned by the main thread makes Qt marshal the call onto the main
# thread's event loop automatically (a queued connection) — this is the Qt
# equivalent of the old root.after(0, ...) trick.
#
# The signal now carries which button triggered the popup ("left"/"right")
# alongside the captured content, so show_popup can pick the right sector
# list and theme.
class Bridge(QObject):
    request_popup = Signal(object, str)

bridge = Bridge()
bridge.request_popup.connect(show_popup)




# __________________________CLLIPBOARD_________________________


def read_clipboard_text():
    clipboard = QGuiApplication.clipboard()
    text = clipboard.text()
    return text if text else None


def do_copy_and_show_popup(side):

    popup_controller.menu_active = True

    previous = read_clipboard_text()

    keyboard.press(Key.ctrl)
    keyboard.press("c")
    keyboard.release("c")
    keyboard.release(Key.ctrl)

    time.sleep(0.2)

    new = read_clipboard_text()

    if new and new != previous:
        content = ("text", new.strip())
    else:
        content = None

    bridge.request_popup.emit(content, side)


# ______________________________START____________________________


BUTTON_SIDE = {
    mouse.Button.left: "left",
    mouse.Button.right: "right",
}

button_state = {
    side: {"down": False, "timer": None}
    for side in BUTTON_SIDE.values()
}


def restart_timer(side):
    state = button_state[side]

    if state["timer"]:
        state["timer"].cancel()

    state["timer"] = threading.Timer(
        LONG_PRESS_DURATION,
        lambda: do_copy_and_show_popup(side),
    )

    state["timer"].start()


app_enabled = True


def on_click(x, y, button, pressed):
    if not app_enabled:
        return
    if popup_controller.menu_active:
        return
    side = BUTTON_SIDE.get(button)
    if side is None:
        return

    state = button_state[side]

    if not pressed:
        # Always process releases, even while the menu is active/closing,
        # so `down` and the timer never get stuck in a stale state.
        state["down"] = False
        if state["timer"]:
            state["timer"].cancel()
            state["timer"] = None
        return

    if popup_controller.menu_active:
        return

    state["down"] = True
    restart_timer(side)


def on_move(x, y):
    if not app_enabled:
        return
    if popup_controller.menu_active:
        return

    for side, state in button_state.items():
        if state["down"]:
            restart_timer(side)


def set_app_enabled(value):
    global app_enabled
    app_enabled = value

    if not value:
        for side, state in button_state.items():
            state["down"] = False
            if state["timer"]:
                state["timer"].cancel()
                state["timer"] = None

    if tray_icon is not None:
        toggle_action.setChecked(value)
        color = "#2a6df5" if value else "#8a8f9b"
        tray_icon.setIcon(make_circle_icon("N", bg_color=color))
        tray_icon.setToolTip("doced — enabled" if value else "doced — disabled")
        

tray_icon = QSystemTrayIcon()
tray_icon.setIcon(make_circle_icon("N"))
tray_icon.setToolTip("doced — enabled")

tray_menu = QMenu()

toggle_action = QAction("Enabled", tray_menu)
toggle_action.setCheckable(True)
toggle_action.setChecked(True)
toggle_action.toggled.connect(set_app_enabled)
tray_menu.addAction(toggle_action)


tray_menu.addSeparator()

quit_action = QAction("Quit", tray_menu)
quit_action.triggered.connect(quit_app)
tray_menu.addAction(quit_action)

tray_icon.setContextMenu(tray_menu)
tray_icon.show()



mouse_listener = mouse.Listener(
    on_click=on_click,
    on_move=on_move,
)

mouse_listener.start()


try:
    sys.exit(app.exec())
finally:
    mouse_listener.stop()
