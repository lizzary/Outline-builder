from PyQt6 import QtCore

class Worker(QtCore.QThread):
    returnResult = QtCore.pyqtSignal(str)
    def __init__(self, webScraper,outputFormat:str):
        super().__init__()
        self.webScraper = webScraper
        self.outputFormat = outputFormat

    def run(self):
        connect = self.webScraper.startSearch(self.outputFormat)

        if connect == "error":
            self.returnResult.emit("error")
        else:
            self.returnResult.emit("success")