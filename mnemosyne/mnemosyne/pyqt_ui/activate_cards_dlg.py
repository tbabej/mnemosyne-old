#
# activate_cards_dlg.py <Peter.Bienstman@UGent.be>
#

from PyQt4 import QtCore, QtGui

from mnemosyne.libmnemosyne.translator import _
from mnemosyne.pyqt_ui.card_set_name_dlg import CardSetNameDlg
from mnemosyne.pyqt_ui.ui_activate_cards_dlg import Ui_ActivateCardsDlg
from mnemosyne.libmnemosyne.ui_components.dialogs import ActivateCardsDialog


class ActivateCardsDlg(QtGui.QDialog, Ui_ActivateCardsDlg,
                       ActivateCardsDialog):

    def __init__(self, component_manager):
        ActivateCardsDialog.__init__(self, component_manager)
        QtGui.QDialog.__init__(self, self.main_widget())
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() \
            | QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowFlags(self.windowFlags() \
            & ~ QtCore.Qt.WindowContextHelpButtonHint)
        # Initialise widgets.
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete),
                        self.saved_sets, self.delete_set)
        criterion = self.database().current_criterion()
        self.criterion_classes = \
            self.component_manager.all("criterion")
        current_criterion = self.database().current_criterion()
        self.widget_for_criterion_type = {}
        for criterion_class in self.criterion_classes:
            widget = self.component_manager.current\
                ("criterion_widget", used_for=criterion_class)\
                (self.component_manager, self)
            self.tab_widget.addTab(widget, criterion_class.criterion_type)
            self.widget_for_criterion_type[criterion_class.criterion_type] \
                = widget
        self.tab_widget.setCurrentWidget(self.widget_for_criterion_type\
                                         [current_criterion.criterion_type])
        self.tab_widget.tabBar().setVisible(self.tab_widget.count() > 1)
        self.tab_widget.currentWidget().display_criterion(current_criterion)
        # Restore state.
        state = self.config()["activate_cards_dlg_state"]
        if state:
            self.restoreGeometry(state)
        splitter_state = self.config()["activate_cards_dlg_splitter_state"]
        if not splitter_state:
            self.splitter.setSizes([100, 350])
        else:
            self.splitter.restoreState(splitter_state)
        # Should go last, otherwise the selection of the saved sets pane will
        # always be cleared.
        self.update_saved_sets_pane()

    def change_widget(self, index):
        self.saved_sets.clearSelection()

    def activate(self):
        self.exec_()

    def update_saved_sets_pane(self):
        self.saved_sets.clear()
        self.criteria_by_name = {}
        active_name = ""
        active_criterion = self.database().current_criterion()
        for criterion in self.database().criteria():
            if criterion._id != 1:
                self.criteria_by_name[criterion.name] = criterion
                self.saved_sets.addItem(criterion.name)
                if criterion == active_criterion:
                    active_name = criterion.name
        self.saved_sets.sortItems()
        if active_name:
            item = self.saved_sets.findItems(active_name,
                QtCore.Qt.MatchExactly)[0]
            self.saved_sets.setCurrentItem(item)
        else:
            self.saved_sets.clearSelection()
        splitter_sizes = self.splitter.sizes()
        if self.saved_sets.count() == 0:
            self.splitter.setSizes([0, sum(splitter_sizes)])
        else:
            if splitter_sizes[0] == 0:
                self.splitter.setSizes([100, sum(splitter_sizes)-100])

    def saved_sets_custom_menu(self, pos):
        menu = QtGui.QMenu()
        menu.addAction(_("Delete"), self.delete_set)
        menu.addAction(_("Rename"), self.rename_set)
        menu.exec_(self.saved_sets.mapToGlobal(pos))

    def save_set(self):
        criterion = self.tab_widget.currentWidget().criterion()
        if criterion.is_empty():
            self.main_widget().show_error(\
                _("This set can never contain any cards!"))
            return
        CardSetNameDlg(self.component_manager, criterion,
                       self.criteria_by_name.keys(), self).exec_()
        if not criterion.name:  # User cancelled.
            return
        if criterion.name in self.criteria_by_name.keys():
            answer = self.main_widget().show_question(_("Update this set?"),
                _("&OK"), _("&Cancel"), "")
            if answer == 1:  # Cancel.
                return
            original_criterion = self.criteria_by_name[criterion.name]
            criterion._id = original_criterion._id
            criterion.id = original_criterion.id
            self.database().update_criterion(criterion)
        else:
            self.database().add_criterion(criterion)
        self.update_saved_sets_pane()
        item = self.saved_sets.findItems(criterion.name,
            QtCore.Qt.MatchExactly)[0]
        self.saved_sets.setCurrentItem(item)
        if self.config()["showed_help_on_renaming_sets"] == False:
            self.main_widget().show_information(\
                _("You can right-click on the name of a saved set to rename or delete it."))
            self.config()["showed_help_on_renaming_sets"] = True

    def delete_set(self):
        answer = self.main_widget().show_question(_("Delete this set?"),
            _("&OK"), _("&Cancel"), "")
        if answer == 1:  # Cancel.
            return -1
        else:
            name = unicode(self.saved_sets.currentItem().text())
            criterion = self.criteria_by_name[name]
            self.database().delete_criterion(criterion)
            self.database().save()
            self.update_saved_sets_pane()

    def rename_set(self):
        name = unicode(self.saved_sets.currentItem().text())
        criterion = self.criteria_by_name[name]
        forbidden_names = self.criteria_by_name.keys()
        forbidden_names.remove(name)
        CardSetNameDlg(self.component_manager, criterion,
                       forbidden_names, self).exec_()
        if not criterion.name:  # User cancelled.
            criterion.name = name
            return
        self.database().update_criterion(criterion)
        self.database().save()
        self.update_saved_sets_pane()
        item = self.saved_sets.findItems(criterion.name,
            QtCore.Qt.MatchExactly)[0]
        self.saved_sets.setCurrentItem(item)

        # load_set gets triggered by ItemActivated, but this does not happen
        # when the user changes the sets through the arrow keys (Qt bug?).
        # Therefore, we also catch currentItemChanged and forward it to
        # change_set, but to prevent unwanted firing when loading the widget
        # for the first time (which would erase the current criterion in case
        # it is not a saved criterion), we discard this event if previous_item
        # is None.
        #
        # To test when editing this code: initial start, with and without
        # current criterion being a saved criterion, changing the set through
        # clicking or through the arrows.

    def load_set(self, item, dummy=None):
        # Sometimes item is None, e.g. during the process of deleting a saved
        # set, so we need to discard the event then.
        if item is None:
            return
        name = unicode(item.text())
        criterion = self.criteria_by_name[name]
        self.tab_widget.setCurrentWidget(self.widget_for_criterion_type\
                                             [criterion.criterion_type])
        self.tab_widget.currentWidget().display_criterion(criterion)
        # Restore the selection that got cleared in change_widget.
        item = self.saved_sets.findItems(criterion.name,
            QtCore.Qt.MatchExactly)[0]
        self.saved_sets.setCurrentItem(item)

    def change_set(self, item, previous_item):
        if previous_item is not None:
            self.load_set(item)

    def _store_state(self):
        self.config()["activate_cards_dlg_state"] = \
            self.saveGeometry()
        self.config()["activate_cards_dlg_splitter_state"] = \
            self.splitter.saveState()

    def closeEvent(self, event):
        # Generated when clicking the window's close button.
        self._store_state()

    def accept(self):
        criterion = self.tab_widget.currentWidget().criterion()
        if criterion.is_empty():
            self.main_widget().show_error(\
                _("This set can never contain any cards!"))
            return
        # 'accept' does not generate a close event.
        self.database().set_current_criterion(criterion)
        self._store_state()
        return QtGui.QDialog.accept(self)
