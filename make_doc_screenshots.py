#!/usr/bin/env python3

import os
import sys
import time

import PIL.Image

os.environ['KEEP_ENV'] = "1"
os.environ["LANG"] = "C"

from gi.repository import GLib

import pytestshot

from tests import paperwork

from paperwork_backend.util import rm_rf

OUT_DIRECTORY = "doc_screenshots"


def get_widget_position(widget):
    return widget.translate_coordinates(
        widget.get_toplevel(), 0, 0
    )


def save_sc(filename, image,
            crop_around_widget=None, crop_diameter=150,
            add_cursor=False):
    img_size = image.size

    if crop_around_widget:
        position = get_widget_position(crop_around_widget)
        size = (
            crop_around_widget.get_allocated_width(),
            crop_around_widget.get_allocated_height()
        )
        center = (
            min(max(0, position[0] + int(size[0] / 2)), img_size[0]),
            min(max(0, position[1] + int(size[1] / 2)), img_size[1])
        )
        crop = (
            min(max(0, position[0] - crop_diameter), img_size[0]),
            min(max(0, position[1] - crop_diameter), img_size[1]),
            min(max(0, position[0] + crop_diameter), img_size[0]),
            min(max(0, position[1] + crop_diameter), img_size[1])
        )
        image = image.crop(crop)
        if add_cursor and not isinstance(add_cursor, tuple):
            add_cursor = (center[0] - crop[0] + 10, center[1] - crop[1] + 10)

    if add_cursor and not isinstance(add_cursor, tuple):
        add_cursor = (int(img_size[0] / 2), int(img_size[1] / 2))

    if add_cursor:
        cursor = PIL.Image.open("cursor.png")
        image.paste(cursor, add_cursor, cursor)

    image.save(os.path.join(OUT_DIRECTORY, filename))


def gen_adf_access(pw):
    menu = pw.main_window.widget_tree.get_object("menubuttonOtherScans")
    menu.clicked()
    pw.wait()
    time.sleep(1)
    img = pytestshot.screenshot(pw.gdk_window)
    save_sc("adf_access.png", img, menu, add_cursor=True)


def gen_adf_multiscan(pw):
    doc = pw.docsearch.get_doc_from_docid("20121213_1946_26")
    pw.main_window.show_doc(doc)
    pw.wait()

    action = pw.main_window.actions['multi_scan'][1]
    GLib.idle_add(action.do)
    pw.wait()

    try:
        GLib.idle_add(action.dialog.actions['add_doc'][1].do)
        pw.wait()

        treeview = action.dialog.lists['docs']['gui']
        treeview.get_selection().select_path([1])
        pw.wait()
        img = pytestshot.screenshot(action.dialog.window.get_window())
        save_sc("adf_multiscan.png", img,
                add_cursor=(500, 75))
    finally:
        GLib.idle_add(action.dialog.window.destroy)
    pw.wait()


SCREENSHOTS = {
    "adf_access": gen_adf_access,
    "adf_multiscan": gen_adf_multiscan,
}


def main(argv):
    rm_rf(OUT_DIRECTORY)
    os.mkdir(OUT_DIRECTORY)

    args = argv[1:]

    for (sc_name, sc_method) in SCREENSHOTS.items():
        if args != [] and sc_name not in args:
            continue

        paperwork_inst = paperwork.PaperworkInstance()
        paperwork_inst.start()
        try:
            sc_method(paperwork_inst)
        finally:
            paperwork_inst.stop()


if __name__ == "__main__":
    main(sys.argv)