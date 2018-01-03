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
import signal
import sys

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtCore import Qt, QTimer, QPoint, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest


class ScreenMode:

    def __init__(self, win):
        self.win = win

    def fullscreen_toggle(self):
        if self.is_fullscreen():
            self.window()
        else:
            self.fullscreen()

    def is_fullscreen(self):
        return self.win.windowState() & Qt.WindowFullScreen

    def window(self):
        self.win.unsetCursor()
        self.win.setWindowState(self.win.windowState() & ~Qt.WindowFullScreen)

    def fullscreen(self):
        self.win.setCursor(Qt.BlankCursor)
        self.win.setWindowState(self.win.windowState() | Qt.WindowFullScreen)


class ImgWatch(QWidget):

    def __init__(self, interval):
        super().__init__()

        self.screen_mode = ScreenMode(self)

        self.image_source_url = None
        self.network_reply = None
        self.instant_reload = False
        self.mpos = QPoint()
        self.pixmap = QPixmap()

        self.netmgr = QNetworkAccessManager()
        self.netmgr.finished.connect(self._download_finished)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.reload_image)
        self.timer.start(interval)

        self.setWindowTitle('QImgWatch')
        self.resize(1280, 720)
        self.setStyleSheet("background-color: black;")

    def _download_finished(self, reply):
        assert reply == self.network_reply
        data = self.network_reply.readAll()
        self.pixmap.loadFromData(data)
        self.repaint()
        self.network_reply = None

        if self.instant_reload:
            self.instant_reload = False
            self.reload_image()

    def set_image_source_url(self, url):
        self.image_source_url = url
        self.reload_image()

    def reload_image(self):
        if self.network_reply is None:
            req = QNetworkRequest(QUrl(self.image_source_url))
            self.network_reply = self.netmgr.get(req)
        else:
            self.instant_reload = True

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_F11 or ev.key() == Qt.Key_F:
            self.screen_mode.fullscreen_toggle()
        elif ev.key() == Qt.Key_Escape:
            if self.screen_modev.is_fullscreen():
                self.window()
        elif ev.key() == Qt.Key_Q:
            self.close()

    def mouseDoubleClickEvent(self, ev):
        self.screen_mode.fullscreen_toggle()

    def mousePressEvent(self, ev):
        self.mpos = ev.pos()

    def mouseMoveEvent(self, ev):
        if ev.buttons() & Qt.LeftButton:
            diff = ev.pos() - self.mpos
            newpos = self.pos() + diff
            self.move(newpos)

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
    parser = argparse.ArgumentParser(
        description="Image viewer that automatically reloads the image at a given interval")
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
        win.screen_mode.fullscreen()

    # allow Ctrl-C to close the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    win.show()
    sys.exit(app.exec_())


def main_entrypoint():
    main(sys.argv)


# EOF #
