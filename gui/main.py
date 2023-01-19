from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPixmap
from yandex_api import get_response, get_coords, detect_address, get_org
import gui.design as design
import sys


class MyApp(QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.flag = None
        self.pushButton_search.clicked.connect(self.show_map)
        self.pushButton_search_address.clicked.connect(self.search_address)
        self.pushButton_reset.clicked.connect(self.show_map)
        self.checkBox.clicked.connect(self.search_address)

        radios = [self.radioButton_scheme, self.radioButton_sat, self.radioButton_hybr]
        for r in radios:
            getattr(r, 'clicked').connect(self.show_map)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Shift:
            scale = int(self.lineEdit_scale.text())
            if scale < 17:
                self.lineEdit_scale.setText(str(scale + 1))
                self.show_map()
        elif event.key() == Qt.Key_CapsLock:
            scale = int(self.lineEdit_scale.text())
            if scale > 0:
                self.lineEdit_scale.setText(str(scale - 1))
                self.show_map()

        elif event.key() == Qt.Key_Left:
            new_coord = round(float(self.lineEdit_long.text()) - 0.01, 5)
            if -90 <= new_coord <= 90:
                self.lineEdit_long.setText(str(new_coord))
                print(self.flag)
                self.show_map(self.flag)
        elif event.key() == Qt.Key_Up:
            new_coord = round(float(self.lineEdit_latt.text()) + 0.01, 5)
            if -180 <= new_coord <= 180:
                self.lineEdit_latt.setText(str(new_coord))
                self.show_map(self.flag)
        elif event.key() == Qt.Key_Down:
            new_coord = round(float(self.lineEdit_latt.text()) - 0.01, 5)
            if -180 <= new_coord <= 180:
                self.lineEdit_latt.setText(str(new_coord))
                self.show_map(self.flag)
        elif event.key() == Qt.Key_Right:
            new_coord = round(float(self.lineEdit_long.text()) + 0.01, 5)
            if -90 <= new_coord <= 90:
                self.lineEdit_long.setText(str(new_coord))
                self.show_map(self.flag)

    def mousePressEvent(self, event):
        long = event.pos().x()
        latt = event.pos().y()
        if long in range(12, 613) and latt in range(266, 667):
            delta_long = (long - 313) * 0.00017478333
            delta_latt = (465 - latt) * (0.00017478333 / 1.9) # 0.00000477142
            delta_scale = float(self.lineEdit_scale.text()) - 13
            if delta_scale > 0:
                delta_long /= delta_scale * 2
                delta_latt /= delta_scale * 2
            elif delta_scale < 0:
                delta_long *= delta_scale * 2
                delta_latt *= delta_scale * 2
            self.lineEdit_latt.setText(str(float(self.lineEdit_latt.text()) + delta_latt))
            self.lineEdit_long.setText(str(float(self.lineEdit_long.text()) + delta_long))
            self.show_map()
            ll = self.lineEdit_long.text() + ',' + self.lineEdit_latt.text()
            address, postal_code = detect_address(ll)
            if event.button() == Qt.RightButton:
                organization = get_org(address)
                # self.lineEdit_org.setText(organization)
            if self.checkBox.isChecked():
                address += f'. Почтовый индекс: {postal_code}'
            if len(address) > 50:
                address = address.split(',')
                address.insert(-1, '\n')
                address = ','.join(address)
            self.label_address.setText('Полный адрес: ' + address)
            if 'Почтовый' in address:
                self.lineEdit_address.setText(address.split('. Почтовый')[0])
            else:
                self.lineEdit_address.setText(address)

    def show_map(self, flag=None):
        self.lineEdit_long.setEnabled(False)
        self.lineEdit_latt.setEnabled(False)
        self.lineEdit_scale.setEnabled(False)
        self.lineEdit_address.setEnabled(False)
        ll = f'{self.lineEdit_long.text()},{self.lineEdit_latt.text()}'
        url = 'http://static-maps.yandex.ru/1.x/'
        radios = [self.radioButton_scheme, self.radioButton_sat, self.radioButton_hybr]
        radio_dict = {'Схема': 'map', 'Спутник': 'sat', 'Гибрид': 'sat,skl'}
        for r in radios:
            if r.isChecked():
                l = radio_dict[r.text()]
                break
        self.flag = f'{ll},pm2rdl'
        if flag:
            self.flag = flag
        print(self.flag)
        params = {
            'll': ll,
            'l': l,
            'z': self.lineEdit_scale.text(),
            'size': '600,400',
        }
        try:
            if self.sender().text() == 'Сброс':
                self.label_address.setText('Полный адрес: ')
            else:
                params['pt'] = self.flag
        except:
            params['pt'] = self.flag
        response = get_response(url, params).content
        with open("response.jpg", "wb") as f:
            f.write(response)
        pixmap = QPixmap("response.jpg")
        pixmap = pixmap.scaled(600, 400)
        self.label_map.setPixmap(pixmap)

        self.lineEdit_long.setEnabled(True)
        self.lineEdit_latt.setEnabled(True)
        self.lineEdit_scale.setEnabled(True)
        self.lineEdit_address.setEnabled(True)

    def search_address(self):
        address = self.lineEdit_address.text()
        long_latt, full_address, postal = get_coords(address)
        long, latt = long_latt.split(',')
        self.lineEdit_latt.setText(latt)
        self.lineEdit_long.setText(long)
        self.lineEdit_scale.setText('13')
        final = f'Полный адрес: {full_address}'
        if self.checkBox.isChecked():
            final += f'. Почтовый индекс: {postal}'
        if len(address) > 50:
            final = final.split(',')
            final.insert(-1, '\n')
            final = ','.join(final)
        self.label_address.setText(final)
        self.show_map()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())
