# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('jpgcomment')

from gi.repository import Gtk, GdkPixbuf # pylint: disable=E0611
import logging
logger = logging.getLogger('jpgcomment')

import os
import pyexiv2

from jpgcomment_lib import Window

# See jpgcomment_lib.Window.py for more details about how this class works
class JpgcommentWindow(Window):
    __gtype_name__ = "JpgcommentWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(JpgcommentWindow, self).finish_initializing(builder)

        self.image_preview = self.builder.get_object("image1")

        self.textview = self.builder.get_object("textview1")
        self.textview.set_editable(False)

        self.liststore = Gtk.ListStore(str)
        self.treeview_images = self.builder.get_object("treeview1")
        self.treeview_images.set_model(self.liststore)
        selection = self.treeview_images.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        selection.connect("changed", self.treeview_selection_changed)

        self.current_image = ''
        self.current_folder = ''

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("File", renderer_text, text=0)
        self.treeview_images.append_column(column_text)
        # Code for other initialization actions should be added here.


    def treeview_selection_changed(self, selection):
        """ handle the preview image and preview label """
        (model, pathlist) = selection.get_selected_rows()
        if not pathlist:
            self.textview.set_editable(False)
            self.textview.get_buffer().set_text('')
            self.current_image = ''
            self.image_preview.clear()
        elif len(pathlist) == 1:
            self.textview.set_editable(True)
            tree_iter = model.get_iter(pathlist[0])
            image = model.get_value(tree_iter,0)

            self.current_image = image

            window_size = self.get_allocation()
            #Get smallest value
            window_size = (window_size.width if window_size.width < window_size.height else window_size.height) - 20

            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(image, window_size, window_size)
            pixbuf = pixbuf.apply_embedded_orientation()
            
            self.image_preview.set_from_pixbuf(pixbuf)
            self.image_preview.set_tooltip_text(image)

            metadata = pyexiv2.ImageMetadata(image)
            metadata.read()
            #latin-1 because of php galleri
            print 'Comment', metadata.comment.decode('latin-1') 
            self.textview.get_buffer().set_text(metadata.comment.decode('latin-1'))

        else:
            #multiple images selected. disable preview
            print 'WTF !!!'

    def on_button1_clicked(self, widget):
        """ choose the folder with images """
        dialog = Gtk.FileChooserDialog(_("Please choose a folder"), self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             "Select", Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)
        
        if self.current_folder:
            dialog.set_filename(self.current_folder)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            #update liststore
            self.current_folder = dialog.get_filename()
            print 'Folder', self.current_folder
            self.liststore_update(self.current_folder)
            #update last used path in settings
        elif response == Gtk.ResponseType.CANCEL:
            pass
        #don't show any preview stuff
        #self.image_preview.hide()
        #self.image_preview_label.hide()
        dialog.destroy()

    def on_button2_clicked(self, widget):
        """ save comment """

        if not self.current_image:
            return

        textbuffer = self.textview.get_buffer()
        text = textbuffer.get_text(textbuffer.get_start_iter() , textbuffer.get_end_iter(), True)

        metadata = pyexiv2.ImageMetadata(self.current_image)
        metadata.read()
        #latin-1 because of php galleri
        metadata.comment = text.decode('utf-8').encode('latin-1')
        metadata.write()
        print 'Saved comment!'

    def liststore_update(self, path):
        """ update the list with images """
        #cleanup current list entries
        self.liststore.clear()
        #add new images from given path

        if os.path.isdir(path):

            self.treeview_images.freeze_child_notify()

            for filename in os.listdir(path):
                if os.path.isfile(os.path.join(path, filename)):
                    print 'file', filename
                    if filename.upper().endswith("JPG") or filename.upper().endswith("JPEG"):
                        self.liststore.append([os.path.join(path, filename)])

            self.treeview_images.thaw_child_notify()
