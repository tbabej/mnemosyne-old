#
# export_metadata_dlg.py <Peter.Bienstman@UGent.be>
#

from PyQt4 import QtGui, QtCore

from mnemosyne.libmnemosyne.translator import _
from mnemosyne.pyqt_ui.ui_export_metadata_dlg import Ui_ExportMetadataDlg
from mnemosyne.libmnemosyne.ui_components.dialogs import ExportMetadataDialog


class ExportMetadataDlg(QtGui.QDialog, Ui_ExportMetadataDlg,
    ExportMetadataDialog):

    def __init__(self, component_manager):
        ExportMetadataDialog.__init__(self, component_manager)
        QtGui.QDialog.__init__(self, self.main_widget())
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.Dialog \
                | QtCore.Qt.CustomizeWindowHint \
                | QtCore.Qt.WindowTitleHint \
                & ~ QtCore.Qt.WindowCloseButtonHint \
                & ~ QtCore.Qt.WindowContextHelpButtonHint)
        self.author_name.setText(self.config()["author_name"])
        self.author_email.setText(self.config()["author_email"])
        self.date.setDate(QtCore.QDate.currentDate())
        self.allow_cancel = True
        self.cancelled = False

    def activate(self):
        ExportMetadataDialog.activate(self)
        return self.exec_()

    def set_values(self, metadata):
        if "card_set_name" in metadata:
            self.card_set_name.setText(metadata["card_set_name"])
        if "author_name" in metadata:
            self.author_name.setText(metadata["author_name"])
        if "author_email" in metadata:
            self.author_email.setText(metadata["author_email"])
        if "tags" in metadata:
            self.tags.setText(metadata["tags"])
        if "date" in metadata:
            date = QtCore.QDate()
            date.fromString(metadata["date"])
            self.date.setDate(date)
        if "revision" in metadata:
            self.revision.setValue(int(metadata["revision"]))
        if "notes" in metadata:
            self.notes.setPlainText(QtCore.QString.fromUtf8(metadata["notes"]))

    def set_read_only(self):
        self.card_set_name.setReadOnly(True)
        self.author_name.setReadOnly(True)
        self.author_email.setReadOnly(True)
        self.tags.setReadOnly(True)
        self.date.setReadOnly(True)
        self.revision.setReadOnly(True)
        self.notes.setReadOnly(True)
        self.allow_cancel = False
        self.setWindowTitle(_("Import cards"))

    def closeEvent(self, event):
        # Generated when clicking the window's close button.
        if self.allow_cancel:
            event.ignore()
            self.reject()
        else:
            event.accept()

    def keyPressEvent(self, event):
        # Note: for the following to work reliably, there should be no
        # shortcuts defined in the ui file.
        if event.key() == QtCore.Qt.Key_Escape or (event.modifiers() in \
            [QtCore.Qt.ControlModifier, QtCore.Qt.AltModifier] and \
            event.key() == QtCore.Qt.Key_E):
            if self.allow_cancel:
                self.reject()
            else:
                event.ignore()
        else:
            QtGui.QDialog.keyPressEvent(self, event)

    def reject(self):
        self.cancelled = True
        return QtGui.QDialog.reject(self)

    def values(self):
        if self.cancelled:
            return None
        metadata = {}
        metadata["card_set_name"] = unicode(self.card_set_name.text())
        metadata["author_name"] = unicode(self.author_name.text())
        metadata["author_email"] = unicode(self.author_email.text())
        metadata["tags"] = unicode(self.tags.text())
        metadata["date"] = unicode(self.date.date().toString())
        metadata["revision"] = str(self.revision.value())
        metadata["notes"] = unicode(self.notes.toPlainText())
        self.config()["author_name"] = unicode(metadata["author_name"])
        self.config()["author_email"] = unicode(metadata["author_email"])
        return metadata