from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .result_row import ResultRow

class AddedGroup(Adw.PreferencesGroup):
    __gtype_name__ = "AddedGroup"

    def add_row(self, row):
        self.rows.append(row)
        self.add(row)

    def rem_row(self, row):
        if row in self.rows:
            self.rows.remove(row)
            self.remove(row)

    def __init__(self, remote, installation, **kwargs):
        super().__init__(**kwargs)

        self.remote = remote
        self.installation = installation
        self.rows = []

        self.set_title(f"{remote.title}")
        self.set_description(_("Installation: {}").format(installation))

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/pending_page.ui")
class PendingPage(Adw.NavigationPage):
    __gtype_name__ = "PendingPage"
    gtc = Gtk.Template.Child

    stack = gtc()
    none_pending = gtc()
    preferences_page = gtc()

    def add_package_row(self, row):
        self.added_packages.append(row.package)
        row.set_state(ResultRow.PackageState.SELECTED)
        key = f"{row.package.remote}<>{row.package.installation}"
        added_row = ResultRow(row.package, ResultRow.PackageState.ADDED, row.origin_list_box)
        group = None
        try:
            group = self.groups[key]
            group.add_row(added_row)
        except KeyError:
            group = AddedGroup(added_row.package.remote, added_row.package.installation)
            group.add_row(added_row)
            self.groups[key] = group
            self.preferences_page.add(group)

        added_row.connect("activated", self.remove_package_row, group)
        self.stack.set_visible_child(self.preferences_page)

    def remove_package_row(self, row, group):
        # row.origin_row.set_state(ResultRow.PackageState.NEW)
        for item in row.origin_list_box:
            if item.state == ResultRow.PackageState.SELECTED and item.package.is_similar(row.package):
                item.set_state(ResultRow.PackageState.NEW)
                break

        group.rem_row(row)
        if row.package in self.added_packages:
            self.added_packages.remove(row.package)
            
        if len(group.rows) == 0:    
            key = f"{row.package.remote}<>{row.package.installation}"
            self.groups.pop(key, None)
            self.preferences_page.remove(group)
        
        if len(self.added_packages) == 0:
            self.stack.set_visible_child(self.none_pending)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.groups = {} # remote<>installation: adw.preference_group
        self.added_packages = []

        # Connections

        # Apply
