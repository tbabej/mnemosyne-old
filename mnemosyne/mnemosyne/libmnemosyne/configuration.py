#
# configuration.py <Peter.Bienstman@UGent.be>
#

import os
import sys
import cPickle

from mnemosyne.libmnemosyne.translator import _
from mnemosyne.libmnemosyne.component import Component
from mnemosyne.libmnemosyne.utils import rand_uuid, traceback_string

config_py = \
"""# Mnemosyne configuration file.

# Science server. Only change when prompted by the developers.
science_server = "mnemosyne-proj.dyndns.org:80"

# Set to True to prevent you from accidentally revealing the answer when
# clicking the edit button.
only_editable_when_answer_shown = False

# The number of daily backups to keep. Set to -1 for no limit.
backups_to_keep = 10

# The moment the new day starts. Defaults to 3 am. Could be useful to change
# if you are a night bird. You can only set the hours, not minutes, and
# midnight corresponds to 0.
day_starts_at = 3

# The number of repetitions that need to happen before autosave.
# Setting this to 1 means saving after every repetition.
save_after_n_reps = 1

# On mobile clients with slow SD cards copying a large database for the backup
# before sync can take longer than the sync itself, so we offer reckless users
# the possibility to skip this.
backup_before_sync = True

# The following setting can be set to False to speed up the syncing process on
# e.g. mobile clients where the media files don't get edited externally.
check_for_edited_local_media_files = True

# Latex preamble. Note that for the pre- and postamble you need to use double
# slashes instead of single slashes here, to have them escaped when Python
# reads them in.
latex_preamble = \"\"\"\\\\documentclass[12pt]{article}
\\\\pagestyle{empty}
\\\\begin{document}\"\"\"

# Latex postamble.
latex_postamble = "\\\\end{document}"

# Latex command.
latex = "latex -interaction=nonstopmode"

# Latex dvipng command.
dvipng = "dvipng -D 200 -T tight tmp.dvi"
"""

class Configuration(Component, dict):

    component_type = "config"

    def __init__(self, component_manager):
        Component.__init__(self, component_manager)
        self.data_dir = None
        self.config_dir = None
        self.keys_to_sync = []

    def activate(self):
        self.determine_dirs()
        self.fill_dirs()
        self.load()
        self.load_user_config()
        
    def set_defaults(self):

        """Fill the config with default values.  Is called after every load,
        since a new version of Mnemosyne might have introduced new keys.

        """

        for key, value in \
            {"path": self.database().default_name + self.database().suffix,
             "import_dir": self.data_dir,
             "import_format": "XML",
             "reset_learning_data_import": False,
             "export_dir": self.data_dir,
             "export_format": "XML",
             "reset_learning_data_export": False,
             "import_img_dir": self.data_dir,
             "import_sound_dir": self.data_dir,
             "import_video_dir": self.data_dir,
             "user_id": None,
             "upload_science_logs": True,
             "science_server": "mnemosyne-proj.dyndns.org:80",
             "max_log_size_before_upload": 64000, # For testability.
             "font": {}, # [card_type.id][fact_key]
             "font_colour": {}, # [card_type.id][fact_key]
             "background_colour": {}, # [card_type.id]
             "alignment": {}, # [card_type.id]
             "hide_pronunciation_field": {}, # [card_type.id]             
             "non_memorised_cards_in_hand": 10,
             "randomise_new_cards": False,
             "randomise_scheduled_cards": False,
             "memorise_sister_cards_on_same_day": False,
             "show_intervals": "never",
             "only_editable_when_answer_shown": False,
             "ui_language": None,
             "backups_to_keep": 10,
             "backup_before_sync": True,
             "check_for_edited_local_media_files": True,
             "interested_in_old_reps": True,
             "day_starts_at": 3,
             "save_after_n_reps": 1,
             "latex_preamble": "\\documentclass[12pt]{article}\n"+
                              "\\pagestyle{empty}\n\\begin{document}",
             "latex_postamble": "\\end{document}",
             "latex": "latex -interaction=nonstopmode",
             "dvipng": "dvipng -D 200 -T tight tmp.dvi",
             "active_plugins": set(), # Plugin classes, not instances.
             "media_autoplay": True,
             "media_controls": False,
             "run_sync_server": False,
             "sync_server_port": 8512,
             "sync_server_username": "",
             "sync_server_password": "",
             "exchange_settings_during_sync": True
            }.items():
            self.setdefault(key, value)
        # These keys will be shared in the sync protocol.
        self.keys_to_sync = ["font", "font_colour", "background_colour",
             "alignment", "hide_pronunciation_field",
             "non_memorised_cards_in_hand", "randomise_new_cards",
             "randomise_scheduled_cards", "memorise_sister_cards_on_same_day",
             "ui_language", "day_starts_at", "latex_preamble",
             "latex_postamble", "latex", "dvipng"]        
        # If the user id is not set, it's either because this is the first run
        # of the program, or because the user deleted the config file. In the
        # latter case, we try to recuperate the id from the history files.
        if self["user_id"] is None:
            _dir = os.listdir(unicode(os.path.join(self.data_dir, "history")))
            history_files = [x for x in _dir if x[-4:] == ".bz2"]
            if not history_files:
                self["user_id"] = rand_uuid()
            else:
                self["user_id"] = history_files[0].split("_", 1)[0]
        # Allow other plugins or frontend to set their configuration data.
        for f in self.component_manager.all("hook", "configuration_defaults"):
            f.run()

    def __setitem__(self, key, value):
        if key in self.keys_to_sync:
            # Don't log when reading the settings from file during startup.
            if self.log().active:
                self.log().edited_setting(key)
        dict.__setitem__(self, key, value)

    def load(self):
        try:
            config_file = file(os.path.join(self.config_dir, "config"), "rb")
            for key, value in cPickle.load(config_file).iteritems():
                self[key] = value
            self.set_defaults()
        except:
            from mnemosyne.libmnemosyne.utils import traceback_string
            raise RuntimeError, _("Error in config:") \
                  + "\n" + traceback_string()
        
    def save(self):
        try:
            config_file = file(os.path.join(self.config_dir, "config"), 'wb')
            cPickle.dump(dict(self), config_file)
        except:
            from mnemosyne.libmnemosyne.utils import traceback_string
            raise RuntimeError, _("Unable to save config file:") \
                  + "\n" + traceback_string()

    def determine_dirs(self):  # pragma: no cover
        # Return if data_dir was already set by the user. In that case, we
        # also store the config in that directory.
        if self.data_dir is not None:
            self.config_dir = self.data_dir
            return
        join = os.path.join
        if sys.platform == "win32":
            import ctypes
            n = ctypes.windll.kernel32.GetEnvironmentVariableW\
                (u"APPDATA", None, 0)
            buf = ctypes.create_unicode_buffer(u"\0"*n)
            ctypes.windll.kernel32.GetEnvironmentVariableW(u"APPDATA", buf, n)
            self.data_dir = join(buf.value, "mnemosyne")
            self.config_dir = self.data_dir
        elif sys.platform == "darwin":
            home = os.path.expanduser("~")
            self.data_dir = join(home, "Library", "Mnemosyne")
            self.config_dir = self.data_dir
        else:
            # Follow the freedesktop standards:
            # http://standards.freedesktop.org/basedir-spec/
            # basedir-spec-latest.html
            home = os.path.expanduser("~")
            if "XDG_DATA_HOME" in os.environ:
                self.data_dir = os.environ["XDG_DATA_HOME"]
            else:
                self.data_dir = join(home, ".local", "share")
            self.data_dir = join(self.data_dir, "mnemosyne")
            if "XDG_CONFIG_HOME" in os.environ:
                self.config_dir = os.environ["XDG_CONFIG_HOME"]
            else:
                self.config_dir = join(home, ".config")
            self.config_dir = join(self.config_dir, "mnemosyne")

    def fill_dirs(self):

        """Fill data_dir and config_dir. Do this even if they already exist,
        because we might have added new files since the last version.

        """

        exists = os.path.exists
        join = os.path.join
        # Create paths.
        if not exists(self.data_dir):
            os.mkdir(self.data_dir)
        if not exists(self.config_dir):
            os.mkdir(self.config_dir)
        for directory in ["history", "plugins", "backups"]:
            if not exists(join(self.data_dir, directory)):
                os.mkdir(join(self.data_dir, directory))
        # Create default configuration.
        if not exists(join(self.config_dir, "config")):
            self.save()
        # Create default config.py.
        config_file = join(self.config_dir, "config.py")
        if not exists(config_file):
            f = file(config_file, "w")
            print >> f, config_py
            f.close()
        # Create machine_id. Do this in a separate file, as extra warning
        # signal that people should not copy this file to a different machine.
        machine_id_file = join(self.config_dir, "machine.id")
        if not exists(machine_id_file):
            f = file(machine_id_file, "w")
            print >> f, rand_uuid()
            f.close()

    def set_card_type_property(self, property_name, property, card_type,
            fact_key=None):

        """Set a property (like font, colour, ..) for a certain card type.
        If fact_key is None, then this will be applied to all fact keys.

        This info is not stored in the database, but in the configuration,
        to allow different clients to have different settings, even though
        they exchange data during sync.

        """

        if property_name not in ["background_colour", "font", "font_colour",
            "alignment", "hide_pronunciation_field"]:
            raise KeyError
        if property_name in ["background_colour", "alignment",
                             "hide_pronunciation_field"]:
            self[property_name][card_type.id] = property
            return
        self[property_name].setdefault(card_type.id, {})
        for key in card_type.keys():
            self[property_name][card_type.id].setdefault(key, None)
        if not fact_key:
            keys = card_type.keys()
        else:
            keys = [fact_key]
        for key in keys:
            self[property_name][card_type.id][key] = property

    def card_type_property(self, property_name, card_type, fact_key=None,
                            default=None):
        if property_name in ["background_colour", "alignment",
                             "hide_pronunciation_field"]:        
            try:
                return self[property_name][card_type.id]
            except KeyError:
                return default
        else:
            try:
                return self[property_name][card_type.id][fact_key]
            except KeyError:
                return default

    def clone_card_type_properties(self, old_card_type, new_card_type):
        for property_name in ["font", "font_colour"]:
            for fact_key in new_card_type.keys():
                old_value = self.card_type_property(property_name,
                    old_card_type, fact_key)
                if old_value:
                    self.set_card_type_property(property_name, old_value, \
                        new_card_type, fact_key)                                       
        for property_name in ["background_colour", "alignment",
                             "hide_pronunciation_field"]:
            old_value = self.card_type_property(property_name, old_card_type)
            if old_value:
                self.set_card_type_property(\
                    property_name, old_value, new_card_type)
            
    def machine_id(self):
        return file(os.path.join(self.config_dir, "machine.id")).\
            readline().rstrip()

    def load_user_config(self):
        sys.path.insert(0, self.config_dir)
        config_file_c = os.path.join(self.config_dir, "config.pyc")
        if os.path.exists(config_file_c):
            os.remove(config_file_c)
        config_file = os.path.join(self.config_dir, "config.py")
        if os.path.exists(config_file):
            try:
                import config
                config = reload(config)
                for var in dir(config):
                    if var in self:
                        self[var] = getattr(config, var)
            except:
                raise RuntimeError, _("Error in config.py:") \
                          + "\n" + traceback_string()

    def change_user_id(self, new_user_id):

        """When a client syncs for the first time with a server, we need to
        set the client's user_id identical to the one of the server, in order
        for the uploaded anonymous logs to be consistent. However, we should only
        do this on a 'virgin' client.

        """

        if new_user_id == self["user_id"]:
            return
        db = self.database()
        if self.log().log_index_of_last_upload() > 1 or not db.is_empty():
            raise RuntimeError, "Unable to change user id."
        old_user_id = self["user_id"]
        self["user_id"] = new_user_id
        from mnemosyne.libmnemosyne.component_manager import \
             migrate_component_manager
        migrate_component_manager(old_user_id, new_user_id)
