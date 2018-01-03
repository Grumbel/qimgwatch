#!/usr/bin/env python3

# qimgwatch - Automatically Refreshing Image Viewer
# Copyright (C) 2018 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import argparse
import urllib.request
import sys
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QSizePolicy
from PyQt5.QtGui import QPainter, QColor, QFont, QPixmap, QBrush
from PyQt5.QtCore import Qt, QTimer, QPoint
import signal


class ImgWatch(QWidget):

    def __init__(self, interval):
        super().__init__()

        self.image_source_url = None

        self.setGeometry(0, 0, 1280, 720)

        self.setWindowTitle('QImgWatch')

        self.setStyleSheet("background-color: black;")

        self.pixmap = QPixmap()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.reload_image)
        self.timer.start(interval)

        self.show()

    def set_image_source_url(self, url):
        self.image_source_url = url
        self.reload_image()

    def reload_image(self):
        url = self.image_source_url
        data = urllib.request.urlopen(url).read()
        self.pixmap.loadFromData(data)
        self.repaint()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_F11 or e.key() == Qt.Key_F:
            self.fullscreen_toggle()

    def mouseDoubleClickEvent(self, ev):
        self.fullscreen_toggle()

    def fullscreen_toggle(self):
        state = self.windowState()

        if state & Qt.WindowFullScreen:
            self.unsetCursor()
            self.setWindowState(state & ~Qt.WindowFullScreen)
        else:
            self.setCursor(Qt.BlankCursor)
            self.setWindowState(state | Qt.WindowFullScreen)

    def fullscreen(self):
        state = self.windowState()
        self.setWindowState(state | Qt.WindowFullScreen)
        self.setCursor(Qt.BlankCursor)

    def paintEvent(self, ev):
        if self.pixmap.isNull():
            return

        painter = QPainter(self)
        # painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        sap = self.pixmap.width() / self.pixmap.height()
        tap = self.width() / self.height()
        if sap > tap:
            th = self.width() / sap
            painter.drawPixmap(0, self.height() // 2 - th // 2, self.width(), th,
                               self.pixmap,
                               0, 0, self.pixmap.width(), self.pixmap.height())
        else:
            tw = sap * self.height()
            painter.drawPixmap(self.width() // 2 - tw // 2, 0, tw, self.height(),
                               self.pixmap,
                               0, 0, self.pixmap.width(), self.pixmap.height())


def parse_args(args):
    parser = argparse.ArgumentParser(description="Image viewer that automatically reloads the image at a given interval")
    parser.add_argument("URL", nargs=1)
    parser.add_argument("-n", "--interval", metavar="SECONDS", type=float, default=0.5,
                        help="Seconds to wait between updates")
    parser.add_argument("-f", "--fullscreen", action="store_true", default=False,
                        help="Start in fullscreen mode")
    return parser.parse_args(args)


def main(argv):
    args = parse_args(argv[1:])

    interval_msec = int(1000 * args.interval)

    app = QApplication(sys.argv)
    win = ImgWatch(interval_msec)
    win.set_image_source_url(args.URL[0])

    if args.fullscreen:
        win.fullscreen()

    # allow Ctrl-C to close the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(app.exec_())


def main_entrypoint():
    main(sys.argv)


# EOF #
