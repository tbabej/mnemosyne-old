#
# card_type_wdgt_generic.py <Peter.Bienstman@UGent.be>
#

from PyQt4 import QtCore, QtGui

from mnemosyne.pyqt_ui.qtextedit2 import QTextEdit2
from mnemosyne.libmnemosyne.ui_components.card_type_widget \
     import GenericCardTypeWidget


class GenericCardTypeWdgt(QtGui.QWidget, GenericCardTypeWidget):

    def __init__(self, component_manager, parent, card_type):
        QtGui.QWidget.__init__(self, parent)
        GenericCardTypeWidget.__init__(self, component_manager)
        self.card_type = card_type
        self.hboxlayout = QtGui.QHBoxLayout(self)
        self.hboxlayout.setMargin(0)
        self.vboxlayout = QtGui.QVBoxLayout()
        self.fact_key_for_edit_box = {}
        self.top_edit_box = None
        for fact_key, fact_key_name, language_code in self.card_type.fields:
            self.vboxlayout.addWidget(QtGui.QLabel(fact_key_name + ":", self))
            t = QTextEdit2(self)
            t.setTabChangesFocus(True)
            t.setUndoRedoEnabled(True)
            t.setReadOnly(False)
            if len(self.card_type.fields) > 2:
                t.setMinimumSize(QtCore.QSize(0, 60))
            else:
                t.setMinimumSize(QtCore.QSize(0, 106))
            self.vboxlayout.addWidget(t)
            self.fact_key_for_edit_box[t] = fact_key
            if not self.top_edit_box:
                self.top_edit_box = t
            self.update_formatting(t)
            t.textChanged.connect(self.text_changed)
            t.currentCharFormatChanged.connect(self.reset_formatting)
        self.hboxlayout.addLayout(self.vboxlayout)
        self.resize(QtCore.QSize(QtCore.QRect(0,0,325,264).size()).\
                    expandedTo(self.minimumSizeHint()))
        
    def update_formatting(self, edit_box):
        fact_key = self.fact_key_for_edit_box[edit_box]
        try:
            colour = self.config()["font_colour"][self.card_type.id][fact_key]
            edit_box.setTextColor(QtGui.QColor(colour))
        except:
            pass
        try:
            colour = self.config()["background_colour"][self.card_type.id]
            p = QtGui.QPalette()
            p.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base,
                       QtGui.QColor(colour))
            edit_box.setPalette(p)
        except:
            pass
        try:
            font_string = self.config()["font"][self.card_type.id][fact_key]
            font = QtGui.QFont()
            font.fromString(font_string)                
            edit_box.setCurrentFont(font)
        except:
            pass

    def reset_formatting(self):

        """Deleting all the text reverts back to the system font, so we have
        to force our custom font again.

        """
        
        for edit_box in self.fact_key_for_edit_box:
            self.update_formatting(edit_box)

    def contains_data(self):
        for edit_box in self.fact_key_for_edit_box:
            if unicode(edit_box.document().toPlainText()):
                return True
        return False

    def data(self):
        fact_data = {}
        for edit_box, fact_key in self.fact_key_for_edit_box.iteritems():
            fact_data[fact_key] = unicode(edit_box.document().toPlainText())
        return fact_data

    def set_data(self, data):
        if data:
            for edit_box, fact_key in self.fact_key_for_edit_box.iteritems():
                if fact_key in data.keys():
                    edit_box.setPlainText(data[fact_key])

    def clear(self):
        for edit_box in self.fact_key_for_edit_box:
            edit_box.setText("")
        self.top_edit_box.setFocus()
    
    def text_changed(self):
        self.parent().set_valid(self.card_type.is_data_valid(self.data()))
