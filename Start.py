#pyinstaller -w -F -i package\icon.ico --splash package/loading.png Start.py
#pyinstaller -w -F -i package\icon.ico Start.py
from package.ui.main import Ui_BaseWidget

if __name__ == "__main__":
    try:
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass

    Ui_BaseWidget.runUi()