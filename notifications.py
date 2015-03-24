#!/usr/bin/python
from gi.repository import Gdk, Gtk, AppIndicator3 as AppIndicator
import time

window = None
list_store = Gtk.ListStore(int, str, str)

def display_window(button):
  global window
  if window:
    window.close()

  window = Gtk.Window()
  screen = window.get_screen()
  pointer = screen.get_root_window().get_pointer()
  active_monitor_n = screen.get_monitor_at_point(pointer[1], pointer[2])

  left_offset = 0
  for i in range(active_monitor_n + 1):
    monitor_geometry = screen.get_monitor_geometry(i)
    left_offset += monitor_geometry.width

  window.set_size_request(400, monitor_geometry.height)
  window.move(left_offset - 400, 0)

  header_bar = Gtk.HeaderBar()
  header_bar.set_show_close_button(True)
  header_bar.props.title = "Notifications"
  window.set_titlebar(header_bar)

  tree_view = Gtk.TreeView(list_store)
  column = Gtk.TreeViewColumn("Event")
  date_time = Gtk.CellRendererText()
  app_name = Gtk.CellRendererText()
  event_string = Gtk.CellRendererText()
  column.pack_start(date_time, True)
  column.pack_start(app_name, True)
  column.pack_start(event_string, True)
  column.add_attribute(date_time, "text", 0)
  column.add_attribute(app_name, "text", 1)
  column.add_attribute(event_string, "text", 2)
  tree_view.append_column(column)
  window.add(tree_view)

  window.set_keep_above(True)
  #window.set_decorated(False)
  window.show_all()

def setup_menu(indicator):
  def add_item(item):
    item.show()
    menu.append(item)
    return item
  menu = Gtk.Menu()
  show_button = add_item(Gtk.MenuItem("Show Notifications"))
  show_button.connect("activate", display_window)
  indicator.set_secondary_activate_target(show_button)
  add_item(Gtk.MenuItem("Exit")).connect("activate", Gtk.main_quit)
  menu.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
  return menu


indicator = AppIndicator.Indicator.new(
  "Notifications",
  "/home/kzar/code/notifications/bars.png",
  AppIndicator.IndicatorCategory.APPLICATION_STATUS
)
indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
indicator.set_menu(setup_menu(indicator))

import dbus
from dbus.mainloop.glib import DBusGMainLoop

def log_notification(bus, message):
  keys = ["app_name", "replaces_id", "app_icon", "summary",
          "body", "actions", "hints", "expire_timeout"]
  args = message.get_args_list()
  if len(args) == 8:
    notification = dict([(keys[i], args[i]) for i in range(8)])
    list_store.append([int(time.mktime(time.gmtime())),
                       notification["app_name"], notification["summary"] + " " + notification["body"]])
    print notification["summary"], notification["body"]

loop = DBusGMainLoop(set_as_default=True)
session_bus = dbus.SessionBus()
session_bus.add_match_string("type='method_call',interface='org.freedesktop.Notifications',member='Notify',eavesdrop=true")
session_bus.add_message_filter(log_notification)

Gtk.main()
