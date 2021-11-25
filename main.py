#!/usr/bin/env python3

"""
Automated output switcher for river - a dynamic tiling Wayland compositor https://github.com/riverwm/river

This script allows to automagically focus the output pointed with the mouse pointer. This provides an imperfect
(and hopefully temporary) workaround to this issue: https://github.com/riverwm/river/issues/448. For the script to work,
you need to apply the pending (as for Nov 25th, 2021) pull request first: https://github.com/riverwm/river/pull/475.
You also need to set `focus-follows-cursor normal` in the river ini file.

This is the very first version. It may need some further work, but seems to do the job.

Author: Piotr Miller
e-mail: nwg.piotr@gmail.com
License: GPL3
"""

import sys
import subprocess

import gi
gi.require_version('Gtk', '3.0')
try:
    gi.require_version('GtkLayerShell', '0.1')
except ValueError:
    raise RuntimeError('\n\n' +
                       'If you haven\'t installed GTK Layer Shell, you need to point Python to the\n' +
                       'library by setting GI_TYPELIB_PATH and LD_LIBRARY_PATH to <build-dir>/src/.\n' +
                       'For example you might need to run:\n\n' +
                       'GI_TYPELIB_PATH=build/src LD_LIBRARY_PATH=build/src python3 ' + ' '.join(sys.argv))

from gi.repository import Gtk, Gdk, GtkLayerShell

outputs = {}
windows = []


def list_outputs():
    global outputs
    lines = subprocess.check_output("wlr-randr", shell=True).decode("utf-8").strip().splitlines()
    if lines:
        name, w, h, x, y = None, None, None, None, None
        for line in lines:
            if not line.startswith(" "):
                name = line.split()[0]
            elif "current" in line:
                w_h = line.split()[0].split('x')
                w = int(w_h[0])
                h = int(w_h[1])
            elif "Position" in line:
                x_y = line.split()[1].split(',')
                x = int(x_y[0])
                y = int(x_y[1])
                if name is not None and w is not None and h is not None and x is not None and y is not None:
                    outputs[name] = {'name': name,
                                          'x': x,
                                          'y': y,
                                          'width': w,
                                          'height': h}
        display = Gdk.Display.get_default()
        for i in range(display.get_n_monitors()):
            monitor = display.get_monitor(i)
            geometry = monitor.get_geometry()

            for key in outputs:
                if int(outputs[key]["x"]) == geometry.x and int(outputs[key]["y"]) == geometry.y:
                    outputs[key]["monitor"] = monitor


class SwitcherWindow(Gtk.Window):
    def __init__(self, output):
        Gtk.Window.__init__(self, type_hint=Gdk.WindowTypeHint.NORMAL)
        self.output = output
        self.is_focused = False

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_monitor(self, output["monitor"])
        GtkLayerShell.set_layer(self, 0)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)

        self.connect("enter_notify_event", self.on_window_enter)

        self.connect('destroy', Gtk.main_quit)
        self.show_all()

    def on_window_enter(self, w, e):
        """if not self.is_focused:
            global windows
            for win in windows:
                win.is_focused = False
            self.is_focused = True"""
        subprocess.Popen('exec riverctl focus-output-name {}'.format(self.output["name"]), shell=True)


def main():
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    css = b"""
            window {
                    background-color: rgba (0, 0, 0, 0.0);
            }
        """
    provider.load_from_data(css)
    try:
        subprocess.check_output("command -v wlr-randr", shell=True).decode("utf-8").strip()
        list_outputs()
        print("Found outputs:")
        for key in outputs:
            print(outputs[key])
            win = SwitcherWindow(outputs[key])
            global windows
            windows.append(win)

    except subprocess.CalledProcessError:
        print("wlr-randr conmmand not found")
        sys.exit(1)

    Gtk.main()


if __name__ == '__main__':
    main()
