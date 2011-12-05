#
# review_wdgt_cramming.py <Peter.Bienstman@UGent.be>
#

from PyQt4 import QtCore, QtGui

from mnemosyne.libmnemosyne.translator import _
from mnemosyne.pyqt_ui.review_wdgt import ReviewWdgt
   

class ReviewWdgtCramming(ReviewWdgt):
    
    def __init__(self, component_manager):
        ReviewWdgt.__init__(self, component_manager)
        self.grade_0_button.setText(_("&Wrong"))       
        self.grade_1_button.hide()
        self.line.hide()
        self.grade_2_button.hide()
        self.grade_3_button.hide()
        self.grade_4_button.hide()
        self.grade_5_button.setText(_("&Right"))
        self.grade_5_button.setFocus()
        parent = self.parent()
        self.wrong = QtGui.QLabel("", parent.status_bar)
        self.unseen = QtGui.QLabel("", parent.status_bar)
        self.active = QtGui.QLabel("", parent.status_bar)
        parent.clear_status_bar()
        parent.add_to_status_bar(self.wrong)
        parent.add_to_status_bar(self.unseen)
        parent.add_to_status_bar(self.active)

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslateUi(self)
        # Upon start, there will be a change event before the grade
        # buttons have been created.
        if hasattr(self, "grade_0_button"):
            self.grade_0_button.setText(_("&Wrong"))
            self.grade_5_button.setText(_("&Right"))
        QtGui.QWidget.changeEvent(self, event)
        
    def keyPressEvent(self, event):
        if self.review_controller().state == "SELECT GRADE":
            if event.key() in [QtCore.Qt.Key_0, QtCore.Qt.Key_1]:
                return self.grade_answer(0)
            elif event.key() in [QtCore.Qt.Key_2, QtCore.Qt.Key_3,
                QtCore.Qt.Key_4, QtCore.Qt.Key_5]:
                return self.grade_answer(5)
        ReviewWdgt.keyPressEvent(self, event)
        
    def update_status_bar_counters(self):
        wrong_count, unseen_count, active_count = \
                   self.review_controller().counters()
        self.wrong.setText(_("Wrong: %d ") % wrong_count)
        self.unseen.setText(_("Unseen: %d ") % unseen_count)
        self.active.setText(_("Active: %d ") % active_count)
        
