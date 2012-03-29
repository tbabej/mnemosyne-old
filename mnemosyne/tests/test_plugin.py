#
# test_plugin.py <Peter.Bienstman@UGent.be>
#

import os
import sys
import shutil
from nose.tools import raises

from mnemosyne_test import MnemosyneTest
from mnemosyne.libmnemosyne import Mnemosyne
from mnemosyne.libmnemosyne.ui_components.main_widget import MainWidget

filename = None
last_error = None

class Widget(MainWidget):

    def show_information(self, s1):
        raise NotImplementedError

    def show_error(self, error):
        global last_error
        last_error = error

    def get_filename_to_open(self, a, b, c):
        return filename

class TestPlugin(MnemosyneTest):

    def setup(self):
        shutil.rmtree("dot_test", ignore_errors=True)

        self.mnemosyne = Mnemosyne(upload_science_logs=False, interested_in_old_reps=True)
        self.mnemosyne.components.insert(0,
           ("mnemosyne.libmnemosyne.translators.gettext_translator", "GetTextTranslator"))
        self.mnemosyne.components.append(\
            ("test_plugin", "Widget"))
        self.mnemosyne.components.append(\
            ("mnemosyne_test", "TestReviewWidget"))
        self.mnemosyne.initialise(os.path.abspath("dot_test"), automatic_upgrades=False)
        self.review_controller().reset()

    @raises(AssertionError)
    def test_1(self):
        from mnemosyne.libmnemosyne.plugin import Plugin
        p = Plugin(self.mnemosyne.component_manager)

    @raises(NotImplementedError)
    def test_2(self):

        from mnemosyne.libmnemosyne.card_types.front_to_back import FrontToBack
        from mnemosyne.libmnemosyne.plugin import Plugin

        class MyCardType(FrontToBack):
            id = "666"

        class MyPlugin(Plugin):
            name = "myplugin"
            description = "MyPlugin"
            components = [MyCardType]

        p = MyPlugin(self.mnemosyne.component_manager)

        old_length = len(self.card_types())
        p.activate()
        assert len(self.card_types()) == old_length + 1
        p.deactivate()
        assert len(self.card_types()) == old_length

        p.activate()

        fact_data = {"f": "question",
                     "b": "answer"}
        card_type = self.card_type_with_id("666")
        self.controller().create_new_cards(fact_data, card_type,
                                              grade=-1, tag_names=["default"])
        p.deactivate() # Pops up an information box that this is not possible.

    def test_3(self):

        from mnemosyne.libmnemosyne.card_types.front_to_back import FrontToBack
        from mnemosyne.libmnemosyne.plugin import Plugin

        class MyCardType(FrontToBack):
            id = "666"

        class MyPlugin(Plugin):
            name = "myplugin"
            description = "MyPlugin"
            components = [MyCardType]

        p = MyPlugin(self.mnemosyne.component_manager)

        old_length = len(self.card_types())
        p.activate()
        assert len(self.card_types()) == old_length + 1
        p.deactivate()
        assert len(self.card_types()) == old_length

        p.activate()

        fact_data = {"f": "question",
                     "b": "answer"}
        card_type = self.card_type_with_id("666")
        card = self.controller().create_new_cards(fact_data, card_type,
                                          grade=-1, tag_names=["default"])[0]
        fact = card.fact
        self.controller().delete_facts_and_their_cards([fact])

        p.deactivate() # Should work without problems.

    def test_4(self):

        from mnemosyne.libmnemosyne.plugin import Plugin
        from mnemosyne.libmnemosyne.card_types.front_to_back import FrontToBack
        from mnemosyne.pyqt_ui.card_type_wdgt_generic import GenericCardTypeWdgt

        class RedGenericCardTypeWdgt(GenericCardTypeWdgt):

            used_for = FrontToBack

            def __init__(self, parent, component_manager):
                GenericCardTypeWdgt.__init__(self, component_manager,
                                             parent, FrontToBack())

        class RedPlugin(Plugin):
            name = "Red"
            description = "Red widget for front-to-back cards"
            components = [RedGenericCardTypeWdgt]

        p = RedPlugin(self.mnemosyne.component_manager)
        p.activate()
        assert self.mnemosyne.component_manager.current\
                    ("generic_card_type_widget", used_for=FrontToBack) != None
        p.deactivate()
        assert self.mnemosyne.component_manager.current\
                    ("generic_card_type_widget", used_for=FrontToBack) == None

    def test_5(self):
        for plugin in self.plugins():
            component = plugin.components[0]
            if component.component_type == "card_type" and component.id == "4":
                plugin.activate()
                plugin.activate()

    @raises(NotImplementedError)
    def test_6(self):
        from mnemosyne.libmnemosyne.hook import Hook
        Hook(self.mnemosyne.component_manager).run()

    def test_install_plugin(self):
        global filename
        filename = os.path.join(os.getcwd(), "tests", "files", "hide_toolbar.plugin")
        import sys
        for module in [module for module in sys.modules if 'hide_toolbar' in module]:
            del sys.modules[module]
        print self.plugins()
        print 'hide_toolbar' in sys.modules
        self.controller().install_plugin()
        print 'hide_toolbar' in sys.modules
        for mod in sys.modules.values():
            reload(mod)

        print self.plugins()
        assert os.path.exists(os.path.join(os.getcwd(), "dot_test", "plugins", "plugin_data"))
        #assert len(self.plugins()) == 4
        for plugin in self.plugins():
            if plugin.__class__.__name__ == "HideToolbarPlugin":
                self.controller().delete_plugin(plugin)
                break
        assert not os.path.exists(os.path.join(os.getcwd(), "dot_test", "plugins", "plugin_data"))
        assert not os.path.exists(os.path.join(os.getcwd(), "dot_test", "plugins", "HideToolbarPlugin.manifest"))
        assert os.path.exists(os.path.join(os.getcwd(), "dot_test", "plugins"))

    def test_install_plugin_cancel(self):
        global filename
        filename = ""
        self.controller().install_plugin()

    def test_install_plugin_missing(self):
        global filename
        global last_error
        import sys
        for module in [module for module in sys.modules if 'hide_toolbar' in module]:
            del sys.modules[module]
        filename = os.path.join(os.getcwd(), "tests", "files", "hide_toolbar_missing.plugin")
        self.controller().install_plugin()
        assert last_error.startswith("No plugin found")
        last_error = None

    def test_install_plugin_corrupt(self):
        global filename
        global last_error
        filename = os.path.join(os.getcwd(), "tests", "files", "hide_toolbar_corrupt.plugin")
        import sys
        for module in [module for module in sys.modules if 'hide_toolbar' in module]:
            del sys.modules[module]
        self.controller().install_plugin()
        assert last_error.startswith("Error when running")
        last_error = None
