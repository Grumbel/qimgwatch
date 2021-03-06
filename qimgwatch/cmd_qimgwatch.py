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
import datetime
import logging
import os
import collections

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPixmap, QImage
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
        # self.win.setCursor(Qt.BlankCursor)
        self.win.setWindowState(self.win.windowState() | Qt.WindowFullScreen)


class ImageLoader:

    def __init__(self, interval):
        self.win = None
        self.interval = interval
        self.image_source_url = None
        self.network_reply = None
        self.instant_reload = False
        self.output_directory = None

        self.netmgr = QNetworkAccessManager()
        self.netmgr.finished.connect(self._download_finished)

    def set_win(self, win):
        assert self.win is None
        self.win = win
        self.timer = QTimer(self.win)
        self.timer.timeout.connect(self.reload_image)
        self.timer.start(self.interval)

    def set_url(self, url):
        self.image_source_url = url
        self.reload_image()

    def set_output_directory(self, d):
        self.output_directory = d

        if not os.path.isdir(self.output_directory):
            logging.info("creating %s", self.output_directory)
            os.mkdir(self.output_directory)

    def save_image(self, data):
        if self.output_directory is None:
            return

        dt = datetime.datetime.utcnow()
        filename = dt.strftime("%FT%T.%fZ") + ".jpg"
        filename = os.path.join(self.output_directory, filename)
        logging.info("writing %s", filename)
        with open(filename, "wb") as fout:
            fout.write(data)

    def _download_finished(self, reply):
        assert reply == self.network_reply
        data = self.network_reply.readAll()
        self.win.update_pixmap(data)
        self.save_image(data)
        self.win.repaint()
        self.network_reply.deleteLater()
        self.network_reply = None

        if self.instant_reload:
            self.instant_reload = False
            self.reload_image()

    def reload_image(self):
        if self.network_reply is None:
            req = QNetworkRequest(QUrl(self.image_source_url))
            self.network_reply = self.netmgr.get(req)
        else:
            self.instant_reload = True


class ImgWatch(QWidget):

    def __init__(self, loader, history):
        super().__init__()

        self.screen_mode = ScreenMode(self)
        self.image_loader = loader

        self.mpos = QPoint()
        self.pixmap = QPixmap()

        self.setWindowTitle('QImgWatch')
        self.resize(1280, 720)
        self.setStyleSheet("background-color: black;")

        if history:
            self.pixmap_history = collections.deque(maxlen=history)
        else:
            self.pixmap_history = None
        self.pixmap_idx = None

        self.setMouseTracking(True)

    def update_pixmap(self, data):
        if not self.pixmap.isNull() and self.pixmap_history is not None:
            self.pixmap_history.append(self.pixmap)

        self.pixmap = QPixmap()
        image = QImage.fromData(data)
        self.pixmap = QPixmap.fromImage(image)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_F11 or ev.key() == Qt.Key_F:
            self.screen_mode.fullscreen_toggle()
        elif ev.key() == Qt.Key_Escape:
            if self.screen_mode.is_fullscreen():
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

        if self.pixmap_history is not None:
            if ev.pos().y() > self.height() - 200:
                w = self.width() // self.pixmap_history.maxlen
                idx = ev.pos().x() // w
                idx = max(0, min(idx, self.pixmap_history.maxlen))
                if self.pixmap_idx != idx:
                    self.pixmap_idx = idx
                    self.repaint()
            else:
                self.pixmap_idx = None

    def paintEvent(self, ev):
        if self.pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        if self.pixmap_idx is None or self.pixmap_history is None:
            pixmap = self.pixmap
        else:
            if 0 <= self.pixmap_idx < len(self.pixmap_history):
                pixmap = self.pixmap_history[self.pixmap_idx]
            else:
                pixmap = self.pixmap

        sap = pixmap.width() / pixmap.height()
        tap = self.width() / self.height()
        if sap > tap:
            th = self.width() / sap
            painter.drawPixmap(0, self.height() // 2 - th // 2, self.width(), th,
                               pixmap,
                               0, 0, pixmap.width(), pixmap.height())
        else:
            tw = sap * self.height()
            painter.drawPixmap(self.width() // 2 - tw // 2, 0, tw, self.height(),
                               pixmap,
                               0, 0, pixmap.width(), pixmap.height())

        if self.pixmap_history is not None:
            for x, pixmap in enumerate(self.pixmap_history):
                thumb_w = self.width() // self.pixmap_history.maxlen
                thumb_h = 150  # pixmap.height() * thumb_w // self.pixmap.width() * 3
                painter.drawPixmap(x * thumb_w, self.height() - thumb_h, thumb_w, thumb_h,
                                   pixmap,
                                   0, 0, pixmap.width(), pixmap.height())


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Image viewer that automatically reloads the image at a given interval")
    parser.add_argument("URL", nargs=1)
    parser.add_argument("-o", "--outdir", metavar="DIRECTORY", type=str, default=None)
    parser.add_argument("-n", "--interval", metavar="SECONDS", type=float, default=0.5,
                        help="Seconds to wait between updates")
    parser.add_argument("-f", "--fullscreen", action="store_true", default=False,
                        help="Start in fullscreen mode")
    parser.add_argument("-H", "--history", type=int, default=0,
                        help="Amount of frames that should be kept in history")
    return parser.parse_args(args)


def main(argv):
    logging.basicConfig(level=logging.DEBUG)

    args = parse_args(argv[1:])

    interval_msec = int(1000 * args.interval)

    app = QApplication(sys.argv)

    loader = ImageLoader(interval_msec)
    if args.outdir is not None:
        loader.set_output_directory(args.outdir)

    win = ImgWatch(loader, args.history)
    loader.set_win(win)
    loader.set_url(args.URL[0])

    if args.fullscreen:
        win.screen_mode.fullscreen()

    # allow Ctrl-C to close the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    win.show()
    sys.exit(app.exec_())


def main_entrypoint():
    main(sys.argv)


# EOF #
