#!/usr/bin/python
import dbus
import time
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import Gdk, Gtk, AppIndicator3 as AppIndicator

window = None
tree_store = Gtk.TreeStore(int, str)

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
  top_offset = monitor_geometry.y

  window.set_size_request(400, monitor_geometry.height - 24)
  window.move(left_offset - 400, top_offset + 24)

  window.set_opacity(0.9)

  header_bar = Gtk.HeaderBar()
  header_bar.set_show_close_button(True)
  header_bar.props.title = "Notifications"
  window.set_titlebar(header_bar)

  tree_view = Gtk.TreeView(tree_store)
  tree_view.set_headers_visible(False)
  column = Gtk.TreeViewColumn("Event")
  date_time = Gtk.CellRendererText()
  event_string = Gtk.CellRendererText()
  column.pack_start(date_time, True)
  column.pack_start(event_string, True)
  column.add_attribute(date_time, "text", 0)
  column.add_attribute(event_string, "text", 1)
  tree_view.append_column(column)
  window.add(tree_view)

  window.set_type_hint(Gdk.WindowTypeHint.DOCK)
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

def record_notification(app_name, message):
  app_row = [row for row in tree_store if row[1] == app_name]
  app_row = app_row[0] if len(app_row) else tree_store.append(None, [0, app_name])
  tree_store.append(app_row.iter, [int(time.mktime(time.gmtime())), message])

def receive_notifications(bus, message):
  keys = ["app_name", "replaces_id", "app_icon", "summary",
          "body", "actions", "hints", "expire_timeout"]
  args = message.get_args_list()
  if len(args) == 8:
    notification = dict([(keys[i], args[i]) for i in range(8)])
    record_notification(notification["app_name"],
                        notification["summary"] + " " + notification["body"])

if __name__ == "__main__":
  indicator = AppIndicator.Indicator.new(
    "Notifications",
    "/home/kzar/code/notifications/bars.png",
    AppIndicator.IndicatorCategory.APPLICATION_STATUS
  )
  indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
  indicator.set_menu(setup_menu(indicator))

  loop = DBusGMainLoop(set_as_default=True)
  session_bus = dbus.SessionBus()
  session_bus.add_match_string("type='method_call',interface='org.freedesktop.Notifications',member='Notify',eavesdrop=true")
  session_bus.add_message_filter(receive_notifications)

  Gtk.main()
