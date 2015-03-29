#!/usr/bin/python
import cgi
import dbus
import time
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import Gdk, Gtk, Pango, AppIndicator3 as AppIndicator

class NotificationStore(Gtk.TreeStore):
  __gtype_name__ = 'NotificationStore'

  def __init__(self):
    self.applications = {}
    super(NotificationStore, self).__init__(int, str)

  def log_notification(self, app_name, title, message):
    title = cgi.escape(title.strip())
    message = cgi.escape(message.strip())
    if title or message:
      if app_name not in self.applications:
        self.applications[app_name] = self.append(
          None, [0, "<big>%s</big>" % app_name]
        )
      now = int(time.mktime(time.gmtime()))
      self.prepend(self.applications[app_name],
                   [now, "<b>%s</b>\n%s" % (title, message)])

window = Gtk.Window()
notifications = NotificationStore()

def setup_window():
  window.set_opacity(0.9)

  header_bar = Gtk.HeaderBar()
  header_bar.set_show_close_button(True)
  header_bar.props.title = "Notifications"
  window.set_titlebar(header_bar)

  tree_view = Gtk.TreeView(notifications)
  tree_view.set_headers_visible(False)
  column = Gtk.TreeViewColumn("Event")

  event_string = Gtk.CellRendererText()
  event_string.set_property("wrap_width", 30)
  event_string.set_property("wrap_mode", Pango.WrapMode.WORD)
  event_string.set_property("width", 250)
  date_time = Gtk.CellRendererText()

  column.pack_start(event_string, True)
  column.pack_start(date_time, True)
  column.add_attribute(event_string, "markup", 1)
  column.add_attribute(date_time, "text", 0)
  tree_view.append_column(column)
  tree_view.set_show_expanders(False)
  notifications.connect('row-has-child-toggled', lambda *args: tree_view.expand_all())

  window.add(tree_view)
  window.connect('delete-event', lambda w, e: w.hide() or True)
  window.set_type_hint(Gdk.WindowTypeHint.DOCK)

def display_window(button):
  # Figure out which monitor we should display the notification window on
  screen = window.get_screen()
  pointer = screen.get_root_window().get_pointer()
  active_monitor_n = screen.get_monitor_at_point(pointer[1], pointer[2])
  # Position and resize the notification window appropriately on the right
  # hand side of the current monitor.
  # (FIXME avoid hard coding the Ubuntu top-bar height of 24px!)
  left_offset = 0
  for i in range(active_monitor_n + 1):
    monitor_geometry = screen.get_monitor_geometry(i)
    left_offset += monitor_geometry.width
  top_offset = monitor_geometry.y
  window.set_size_request(400, monitor_geometry.height - 24)
  window.move(left_offset - 400, top_offset + 24)
  # Now that the window's ready, we can display it!
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

def receive_notifications(bus, message):
  keys = ["app_name", "replaces_id", "app_icon", "summary",
          "body", "actions", "hints", "expire_timeout"]
  args = message.get_args_list()
  if len(args) == 8:
    notification = dict([(keys[i], args[i]) for i in range(8)])
    notifications.log_notification(
      notification["app_name"],
      notification["summary"],
      notification["body"]
    )

if __name__ == "__main__":
  indicator = AppIndicator.Indicator.new(
    "Notifications",
    "/home/kzar/code/notifications/bars.png",
    AppIndicator.IndicatorCategory.APPLICATION_STATUS
  )
  indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
  indicator.set_menu(setup_menu(indicator))

  setup_window()

  loop = DBusGMainLoop(set_as_default=True)
  session_bus = dbus.SessionBus()
  session_bus.add_match_string("type='method_call',interface='org.freedesktop.Notifications',member='Notify',eavesdrop=true")
  session_bus.add_message_filter(receive_notifications)

  Gtk.main()
