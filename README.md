QImgWatch
=========

QImgWatch is similar to the command line tool `watch`, but instead of
watching a programs output, it is watching a given URL that is
pointing to an image and refreshing it automatically at regular
intervals.

The image is automatically scaled to the window size and a fullscreen
mode is provided as well.


Installation
------------

    sudo -H pip3 install .

Usage
-----

    $ qimgwatch --help
    usage: qimgwatch [-h] [-n SECONDS] [-f] URL
    
    Image viewer that automatically reloads the image at a given interval
    
    positional arguments:
      URL
    
    optional arguments:
      -h, --help            show this help message and exit
      -n SECONDS, --interval SECONDS
                            Seconds to wait between updates
      -f, --fullscreen      Start in fullscreen mode
