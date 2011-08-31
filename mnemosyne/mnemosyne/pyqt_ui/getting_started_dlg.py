#
# intro_wizard_dlg.py <Johannes.Baiter@gmail.com>
#

from PyQt4 import QtGui, QtCore

from mnemosyne.pyqt_ui.ui_getting_started_dlg import Ui_GettingStartedDlg
from mnemosyne.libmnemosyne.ui_components.dialogs import GettingStartedDialog

class GettingStartedDlg(QtGui.QWizard, Ui_GettingStartedDlg,
        GettingStartedDialog):

    def __init__(self, component_manager):
        GettingStartedDialog.__init__(self, component_manager)
        QtGui.QWizard.__init__(self, self.main_widget())
        self.setupUi(self)
        watermark = QtGui.QPixmap("pixmaps/mnemosyne.svg").scaledToHeight(
                200, QtCore.Qt.SmoothTransformation)
        self.setPixmap(QtGui.QWizard.WatermarkPixmap, watermark)    
        
    def activate(self):
        GettingStartedDialog.activate(self)
        self.show()

    def accept(self):
        self.config()["upload_science_logs"] = self.upload_box.isChecked()
        QtGui.QWizard.accept(self)
        
