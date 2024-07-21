from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .remote_row import RemoteRow
import subprocess

class NewRemoteRow(Adw.ActionRow):
    __gtype_name__ = "NewRemoteRow"

    def idle_stuff(self, *args):
        self.set_title(self.info["title"])
        self.set_subtitle(self.info["description"])
        self.add_suffix(Gtk.Image.new_from_icon_name("plus-large-symbolic"))

    def __init__(self, info, **kwargs):
        super().__init__(**kwargs)
        self.info = info
        GLib.idle_add(self.idle_stuff)
        self.set_activatable(True)
        self.connect("activated", lambda *_: print(info["name"]))

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/remotes_page/remotes_page.ui")
class RemotesPage(Adw.NavigationPage):
    __gtype_name__ = 'RemotesPage'
    gtc = Gtk.Template.Child

    sidebar_button = gtc()
    search_bar = gtc()
    toast_overlay = gtc()
    stack = gtc()
    current_remotes_group = gtc()
    new_remotes_group = gtc()

    # Statuses
    loading_remotes = gtc()
    no_remotes = gtc()
    content_page = gtc()

    # Preselected Remotes
    new_remotes = [
        {
            "title": "AppCenter",
            "name": "appcenter",
            "link": "https://flatpak.elementary.io/repo.flatpakrepo",
            "description": _("The open source, pay-what-you-want app store from elementary")
        },
        {
            "title": "Flathub",
            "name": "flathub",
            "link": "https://dl.flathub.org/repo/flathub.flatpakrepo",
            "description": _("Central repository of Flatpak applications"),
        },
        {
            "title": "Flathub beta",
            "name": "flathub-beta",
            "link": "https://flathub.org/beta-repo/flathub-beta.flatpakrepo",
            "description": _("Beta builds of Flatpak applications"),
        },
        {
            "title": "Fedora",
            "name": "fedora",
            "link": "oci+https://registry.fedoraproject.org",
            "description": _("Flatpaks packaged by Fedora Linux"),
        },
        {
            "title": "GNOME Nightly",
            "name": "gnome-nightly",
            "link": "https://nightly.gnome.org/gnome-nightly.flatpakrepo",
            "description": _("The latest beta GNOME Apps and Runtimes"),
        },
        {
            "title": "KDE Testing Applications",
            "name": "kdeapps",
            "link": "https://distribute.kde.org/kdeapps.flatpakrepo",
            "description": _("Beta KDE Apps and Runtimes"),
        },
        {
            "title": "WebKit Developer SDK",
            "name": "webkit-sdk",
            "link": "https://software.igalia.com/flatpak-refs/webkit-sdk.flatpakrepo",
            "description": _("Central repository of the WebKit Developer and Runtime SDK"),
        }
    ]

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None
    
    def start_loading(self):
        self.stack.set_visible_child(self.loading_remotes)
        for row in self.current_remote_rows:
            self.current_remotes_group.remove(row)
        self.current_remote_rows.clear()

    def end_loading(self):
        self.stack.set_visible_child(self.content_page)
        for install in HostInfo.installations:
            for remote in HostInfo.remotes[install]:
                row = RemoteRow(self, install, remote)
                self.current_remotes_group.add(row)
                self.current_remote_rows.append(row)

    def filter_remote(self, row):
        self.filter_setting.set_boolean("show-apps", True)
        self.filter_setting.set_boolean("show-runtimes", True)
        self.filter_setting.set_string("remotes-list", f"{row.remote.name}<>{row.installation};")
        self.filter_setting.reset("runtimes-list")
        packages_page = self.main_window.pages[self.main_window.packages_row]
        packages_page.filters_page.generate_filters()
        packages_page.apply_filters()
        GLib.idle_add(lambda *_: self.main_window.activate_row(self.main_window.packages_row))

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.__class__.instance = self
        self.main_window = main_window
        ms = main_window.main_split
        self.search_bar.set_key_capture_widget(main_window)
        self.current_remote_rows = []
        self.filter_setting = Gio.Settings.new("io.github.flattool.Warehouse.filter")

        # Connections
        ms.connect("notify::show-sidebar", lambda *_: self.sidebar_button.set_active(ms.get_show_sidebar()))
        self.sidebar_button.connect("toggled", lambda *_: ms.set_show_sidebar(self.sidebar_button.get_active()))

        # Apply
        for item in self.new_remotes:
            row = NewRemoteRow(item)
            self.new_remotes_group.add(row)