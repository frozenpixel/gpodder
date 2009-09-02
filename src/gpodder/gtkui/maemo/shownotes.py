# -*- coding: utf-8 -*-
#
# gPodder - A media aggregator and podcast client
# Copyright (c) 2005-2009 Thomas Perl and the gPodder Team
#
# gPodder is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# gPodder is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import gtk
import gtk.gdk
import pango
import urllib2
import threading

from xml.sax import saxutils

import gpodder

_ = gpodder.gettext

from gpodder import util

from gpodder.gtkui.interface.common import BuilderWidget
from gpodder.gtkui.interface.shownotes import gPodderShownotesBase

class gPodderShownotes(gPodderShownotesBase):
    def on_create_window(self):
        # Create the menu and set it for this window (Maybe move
        # this to the .ui file if GtkBuilder allows this)
        menu = gtk.Menu()
        menu.append(self.action_play.create_menu_item())
        menu.append(self.action_delete.create_menu_item())
        menu.append(gtk.SeparatorMenuItem())
        menu.append(self.action_download.create_menu_item())
        menu.append(self.action_pause.create_menu_item())
        menu.append(self.action_resume.create_menu_item())
        menu.append(self.action_cancel.create_menu_item())
        menu.append(gtk.SeparatorMenuItem())
        menu.append(self.action_visit_website.create_menu_item())
        menu.append(gtk.SeparatorMenuItem())
        menu.append(self.action_close.create_menu_item())
        self.main_window.set_menu(self.set_finger_friendly(menu))

    def on_scroll_down(self):
        if not hasattr(self.scrolled_window, 'get_vscrollbar'):
            return
        vsb = self.scrolled_window.get_vscrollbar()
        vadj = vsb.get_adjustment()
        step = vadj.step_increment
        vsb.set_value(vsb.get_value() + step)

    def on_scroll_up(self):
        if not hasattr(self.scrolled_window, 'get_vscrollbar'):
            return
        vsb = self.scrolled_window.get_vscrollbar()
        vadj = vsb.get_adjustment()
        step = vadj.step_increment
        vsb.set_value(vsb.get_value() - step)

    def on_show_window(self):
        self.download_progress.set_fraction(0)
        self.download_progress.set_text('')
        self.main_window.set_title(self.episode.title)

    def on_display_text(self):
        heading = self.episode.title
        subheading = _('from %s') % (self.episode.channel.title)
        description = self.episode.description

        b = gtk.TextBuffer()
        b.create_tag('heading', scale=pango.SCALE_LARGE, weight=pango.WEIGHT_BOLD)
        b.create_tag('subheading', scale=pango.SCALE_SMALL)
        b.insert_with_tags_by_name(b.get_end_iter(), heading, 'heading')
        b.insert_at_cursor('\n')
        b.insert_with_tags_by_name(b.get_end_iter(), subheading, 'subheading')
        b.insert_at_cursor('\n\n')
        b.insert(b.get_end_iter(), util.remove_html_tags(description))
        b.place_cursor(b.get_start_iter())
        self.textview.set_buffer(b)

    def on_hide_window(self):
        self.episode = None
        self.textview.set_buffer(gtk.TextBuffer())

    def on_episode_status_changed(self):
        self.download_progress.set_property('visible', \
                self.task is not None and \
                self.task.status != self.task.CANCELLED)
        self.action_play.set_sensitive(\
                (self.task is None and \
                 self.episode.was_downloaded(and_exists=True)) or \
                (self.task is not None and self.task.status in \
                 (self.task.DONE, self.task.CANCELLED)))
        self.action_delete.set_sensitive(\
                self.episode.was_downloaded(and_exists=True))
        self.action_download.set_sensitive((self.task is None and not \
                self.episode.was_downloaded(and_exists=True)) or \
                (self.task is not None and \
                 self.task.status in (self.task.CANCELLED, self.task.FAILED)))
        self.action_pause.set_sensitive(self.task is not None and \
                self.task.status in (self.task.QUEUED, self.task.DOWNLOADING))
        self.action_resume.set_sensitive(self.task is not None and \
                self.task.status == self.task.PAUSED)
        self.action_cancel.set_sensitive(self.task is not None and \
                self.task.status in (self.task.QUEUED, self.task.DOWNLOADING, \
                    self.task.PAUSED))
        self.action_visit_website.set_sensitive(self.episode is not None and \
                self.episode.link is not None)

    def on_download_status_progress(self):
        if self.task:
            self.download_progress.set_fraction(self.task.progress)
            self.download_progress.set_text('%s: %d%% (%s/s)' % ( \
                    self.task.STATUS_MESSAGE[self.task.status], \
                    100.*self.task.progress, \
                    util.format_filesize(self.task.speed)))
