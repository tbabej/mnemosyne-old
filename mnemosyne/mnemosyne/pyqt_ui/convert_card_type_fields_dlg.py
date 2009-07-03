#
# convert_card_type_fields_dlg.py <Peter.Bienstman@UGent.be>
#

from PyQt4 import QtCore, QtGui

from mnemosyne.libmnemosyne.translator import _
from mnemosyne.pyqt_ui.ui_convert_card_type_fields_dlg import \
     Ui_ConvertCardTypeFieldsDlg


class ConvertCardTypeFieldsDlg(QtGui.QDialog, Ui_ConvertCardTypeFieldsDlg):

    def __init__(self, old_card_type, new_card_type,
                 correspondence, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.old_card_type = old_card_type
        self.new_card_type = new_card_type
        self.correspondence = correspondence
        self.comboboxes = {}
        index = 1
        for old_fact_key, old_fact_key_name in old_card_type.fields:
            label = QtGui.QLabel(self)
            label.setText(old_fact_key_name + ":")
            font = QtGui.QFont()
            font.setWeight(50)
            font.setBold(False)
            label.setFont(font)
            self.gridLayout.addWidget(label, index, 0, 1, 1)
            combobox = QtGui.QComboBox(self)
            for new_fact_key, new_key_name in new_card_type.fields:
                combobox.addItem(new_key_name)
            combobox.addItem(_("<none>"))
            combobox.setCurrentIndex(combobox.count()-1)
            self.gridLayout.addWidget(combobox, index, 1, 1, 1)
            self.comboboxes[old_fact_key] = combobox
            index += 1
            self.connect(combobox, QtCore.SIGNAL(\
                "currentIndexChanged(QString)"), self.combobox_updated)

    def combobox_updated(self):
        self.ok_button.setEnabled(False)
        self.correspondence.clear()
        for old_fact_key, old_fact_key_name in self.old_card_type.fields:
            new_fact_key_name = self.comboboxes[old_fact_key].currentText()
            if new_fact_key_name != _("<none>"):
                self.ok_button.setEnabled(True)                
                new_fact_key = \
                     self.new_card_type.key_with_name(new_fact_key_name)
                if new_fact_key in self.correspondence.values():
                    QtGui.QMessageBox.critical(None, _("Mnemosyne"),
                        _("No duplicate in new fields allowed."),
                        _("&OK"), "", "", 0, -1)
                    self.ok_button.setEnabled(False)
                    return           
                self.correspondence[old_fact_key] = new_fact_key
              
    def accept(self):
        self.correspondence.clear()
        for old_fact_key, old_fact_key_name in self.old_card_type.fields:
            new_fact_key_name = self.comboboxes[old_fact_key].currentText()
            if new_fact_key_name != _("<none>"):
                new_fact_key = \
                     self.new_card_type.key_with_name(new_fact_key_name)
                self.correspondence[old_fact_key] = new_fact_key
        QtGui.QDialog.accept(self)
        
