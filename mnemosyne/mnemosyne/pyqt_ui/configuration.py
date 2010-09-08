#
# configuration.py <Peter.Bienstman@UGent.be>
#

from mnemosyne.libmnemosyne.hook import Hook


class PyQtConfiguration(Hook):

    used_for = "configuration_defaults"

    def run(self):
        for key, value in \
            {"list_font": None,
             "card_type_name_of_last_added": "",
             "tags_of_last_added": "",
             "sort_column": None,
             "sort_order": None,
             "previous_statistics_page": 0,
             "previous_configuration_wdgt": 0,
             "previous_variant_for_statistics_page": {}, # dict[page] = variant
             "main_window_size": (0, 0),
             "add_widget_size": (0, 0),
             "edit_widget_size": (0, 0),
             "plugins_dlg_size": (0, 0),
             "browse_dlg_size": (0, 0),
             "statistics_dlg_size": (0, 0),
             "configuration_dlg_size": (0, 0),
             "activate_cards_dlg_size": (0, 0),
             "activate_cards_dlg_splitter": None,
             "sync_help_shown": False,
             "server_for_sync_as_client": "",
             "port_for_sync_as_client": 8512,
             "username_for_sync_as_client": "",
             "password_for_sync_as_client": "",
             "port_for_sync_as_server": 8512,
             "remote_access_username": "",
             "remote_access_password": ""
            }.items():
            self.config().setdefault(key, value)
