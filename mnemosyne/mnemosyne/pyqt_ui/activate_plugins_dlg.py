#
# activate_plugins_dlg.py <Peter.Bienstman@UGent.be>
#

import gettext
_ = gettext.gettext

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ui_activate_plugins_dlg import Ui_ActivatePluginsDlg

from mnemosyne.libmnemosyne.component_manager import config, plugins


class PluginListModel(QAbstractTableModel):

    def rowCount(self, parent=QModelIndex()):
        return len(plugins())
    
    def columnCount(self, parent=QModelIndex()):
        return 3
    
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if index.column() == 1:
                return QVariant(plugins()[index.row()].name)
            elif index.column() == 2:
                return QVariant(plugins()[index.row()].description)
        if role == Qt.CheckStateRole:
            if index.column() == 0:
                return QVariant(Qt.Checked)
        return QVariant()

    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsEnabled|Qt.ItemIsUserCheckable|Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled|Qt.ItemIsSelectable

    def setData(self, index, value, role):
        print index.column(), value, role
        if index.isValid() and index.column() == 0:
            if role == Qt.CheckStateRole:
                if value == Qt.Checked:
                    print 'checked'
                else:
                    print 'unchecked'
            self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                      index, index)
            return True
        return False
                    
    def headerData(self, index, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if index == 0:
                return QVariant(_("Active"))
            elif index == 1:
                return QVariant(_("Name"))
            elif index == 2:
                return QVariant(_("Description"))
        return QVariant()

class ActivatePluginsDlg(QDialog, Ui_ActivatePluginsDlg):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.model = PluginListModel()
        self.plugins_table.setModel(self.model)
        self.plugins_table.setWordWrap(True) 
        self.plugins_table.resizeColumnsToContents()
       
