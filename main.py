if __name__ == '__main__':
    from module.app import LabelApp
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    label_app = LabelApp()
    label_app.show()
    sys.exit(app.exec())
