import sys
import traceback
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QVBoxLayout, 
    QPushButton, QTextEdit, QLabel, QMessageBox
)
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QPainter, QPageLayout, QPageSize, QFont
from PyQt6.QtCore import QSizeF, QMarginsF

# =====================================================================
# ၁။ CRASH ဖြစ်လျှင် ပိတ်မကျဘဲ ERROR ပြပေးမယ့် စနစ် (CRITICAL FOR DEBUGGING)
# =====================================================================
def catch_exceptions(exc_type, exc_value, exc_traceback):
    """Program ကောက်ခါငင်ကာ ပိတ်ကျသွားရင် ဘာကြောင့်လဲဆိုတာကို ပြပေးမယ့် Exception Handler"""
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("=== CRITICAL ERROR DETECTED ===")
    print(error_msg)
    
    # GUI ပေါ်မှာလည်း Error Box ပြပေးမယ်
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText("စနစ်အတွင်း အမှားအယွင်းတစ်ခု ဖြစ်ပွားခဲ့သည်!")
    msg.setInformativeText(str(exc_value))
    msg.setDetailedText(error_msg)
    msg.setWindowTitle("System Error")
    msg.exec()

sys.excepthook = catch_exceptions


# =====================================================================
# ၂။ RECEIPT DIALOG CLASS
# =====================================================================
class ReceiptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Receipt Preview")
        self.setMinimumSize(400, 500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.label = QLabel("ဘောက်ချာ နမူနာပြသခြင်း -")
        layout.addWidget(self.label)
        
        # စာသားတွေကို ပြသဖို့အတွက် Text Edit
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.generate_sample_receipt()
        layout.addWidget(self.text_edit)
        
        # Print Button
        self.btn_print = QPushButton("Print Receipt (Thermal 80x297mm)")
        self.btn_print.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.btn_print.clicked.connect(self.print_receipt)
        layout.addWidget(self.btn_print)
        
        self.setLayout(layout)
        
    def generate_sample_receipt(self):
        """ပြသမယ့် ဘောက်ချာပုံစံစာသား"""
        receipt_text = (
            "      ဇေ (ဖိတ်စာလုပ်ငန်း)      \n"
            "   မြဝတီမြို့၊ ဖုန်း - ၀၉-xxxxxxx   \n"
            "================================\n"
            "Date: 2026-06-07   Time: 14:15\n"
            "Receipt No: #100234\n"
            "--------------------------------\n"
            "Item           Qty   Price   Amt\n"
            "--------------------------------\n"
            "Printing Svc    1     500    500\n"
            "Stationery      2     300    600\n"
            "Ice Cream       1    1000   1000\n"
            "--------------------------------\n"
            "Total Amount:           2,100 MMK\n"
            "================================\n"
            "     လာရောက်အားပေးမှုကို      \n"
            "      အထူးကျေးဇူးတင်ပါသည်။     \n"
        )
        self.text_edit.setText(receipt_text)

    def print_receipt(self):
        """Thermal Printer သို့ ပရင့်ထုတ်ပေးမည့် Function"""
        try:
            # HighResolution မုဒ်ဖြင့် Printer တည်ဆောက်ခြင်း
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            
            # မှတ်ချက် - Printer နာမည်သတ်မှတ်ချင်ရင် အောက်က line ကို သုံးနိုင်ပါတယ်
            # printer.setPrinterName("Your_Thermal_Printer_Name")
            
            # 80mm x 297mm Custom Page Size သတ်မှတ်ခြင်း (Millimeter Unit)
            page_size = QPageSize(QSizeF(80, 297), QPageSize.Unit.Millimeter)
            
            # Layout သတ်မှတ်ခြင်း (Portrait + ဘေးဘောင် 2mm စီ ချန်မယ်)
            layout = QPageLayout()
            layout.setPageSize(page_size)
            layout.setOrientation(QPageLayout.Orientation.Portrait)
            layout.setMargins(QMarginsF(2, 2, 2, 2))
            
            printer.setPageLayout(layout)
            
            # Painter စတင်ခြင်း
            painter = QPainter()
            if not painter.begin(printer):
                QMessageBox.warning(self, "Warning", "Printer Driver သို့ ချိတ်ဆက်၍မရပါ။ Driver သို့မဟုတ် ကြိုးကို စစ်ဆေးပါ။")
                return
                
            # စာလုံး Font သတ်မှတ်ခြင်း (Thermal printer အတွက် သင့်တော်မယ့် font size)
            font = QFont("Courier New", 10) 
            painter.setFont(font)
            
            # Text Edit ထဲက စာသားတွေကို တစ်လိုင်းချင်းစီ ပရင့်ဆွဲထုတ်ခြင်း
            receipt_content = self.text_edit.toPlainText()
            y_position = 20 # အပေါ်ဆုံးကနေ စချမယ့် အကွာအဝေး (Pixel/Point)
            line_height = 25 # စာတစ်လိုင်းနဲ့ တစ်လိုင်း အကွာအဝေး
            
            for line in receipt_content.split('\n'):
                # x=10, y=y_position နေရာမှာ စာသားကို ရိုက်နှိပ်ပါမယ်
                painter.drawText(10, y_position, line)
                y_position += line_height
                
            # Printer လုပ်ငန်းစဉ် အောင်မြင်စွာ ပိတ်သိမ်းခြင်း (အလွန်အရေးကြီး - မပိတ်ရင် Crash ဖြစ်တတ်ပါတယ်)
            painter.end()
            
            QMessageBox.information(self, "Success", "ပရင့်ထုတ်ခြင်း အောင်မြင်ပါသည်။")
            
        except Exception as e:
            # အကယ်၍ Print ထုတ်စဉ် Error တက်ခဲ့ရင် Program ပိတ်မကျဘဲ ဒီမှာ လာပြပါလိမ့်မယ်
            QMessageBox.critical(self, "Printing Error", f"အောက်ပါအချက်ကြောင့် Print ထုတ်မရပါ-\n{str(e)}")


# =====================================================================
# ၃။ MAIN WINDOW CLASS
# =====================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main POS System")
        self.setMinimumSize(300, 200)
        
        # Center Button တစ်ခုတည်းပါမယ့် Layout
        layout = QVBoxLayout()
        self.btn_open_dialog = QPushButton("Open Receipt Dialog")
        self.btn_open_dialog.setStyleSheet("font-size: 14px; padding: 15px;")
        self.btn_open_dialog.clicked.connect(self.open_receipt_dialog)
        layout.addWidget(self.btn_open_dialog)
        
        # Main Widget သတ်မှတ်ခြင်း
        from PyQt6.QtWidgets import QWidget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
    def open_receipt_dialog(self):
        # Dialog ကို သီးသန့် variable တစ်ခုအနေနဲ့ ခေါ်ယူခြင်းက Memory Garbage Collection ပြဿနာကို ကျော်လွှားစေပါတယ်
        self.dialog = ReceiptDialog(self)
        self.dialog.exec()


# =====================================================================
# ၄။ PROGRAM RUNNER
# =====================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Main Window ကို ပြသခြင်း
    main_win = MainWindow()
    main_win.show()
    
    sys.exit(app.exec())