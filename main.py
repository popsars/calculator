# -*- coding: utf-8 -*-
import enum
import random
import redis
import statistics
import time
import ujson
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from typing import List
from loguru import logger


redisc = redis.from_url(url='redis://127.0.0.1:6379', db=1, decode_responses=True)


class OperationType(enum.Enum):
    ADDITION = ('+', '+')
    SUBTRACTION = ('-', '-')
    MULTIPLICATION = ('×', '*')
    DIVISION = ('÷', '/')


class Setting:
    @classmethod
    def load_range(cls, username, key: str) -> List[int]:
        values = redisc.hget(f'{username}/range', key)
        if values:
            return ujson.loads(values)
        return [0, 0, 0, 0, 0, 0]

    @classmethod
    def save_range(cls, username, key: str, values: List[int]) -> None:
        redisc.hset(f'{username}/range', key, ujson.dumps(values))


class Configurator(QDialog):
    @logger.catch
    def __init__(self, parent=None, username=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.username: str = username
        self.setWindowTitle(f'{username}/{self.__class__.__name__}')
        self.buttons = [QPushButton(op.value[0]) for op in OperationType]
        for button in self.buttons:
            button.clicked.connect(self.on_clicked)
        self.set_layout()

    def set_layout(self):
        layout = QVBoxLayout()
        for button in self.buttons:
            layout.addWidget(button)
        layout.addStretch()
        # layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(layout)

    @logger.catch
    def on_clicked(self, *args):
        text = self.sender().text()
        for operation in OperationType:
            if operation.value[0] == text:
                calculator = Calculator(parent=self, operation=operation)
                calculator.exec()
                break


class RangeSetting(QDialog):
    @logger.catch
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.username: OperationType = self.parent().username
        self.operation: OperationType = self.parent().operation
        self.setWindowTitle(f'{self.username}/{self.operation.value[0]}/{self.__class__.__name__}')
        self.x1_spb = QSpinBox()
        self.x2_spb = QSpinBox()
        self.y1_spb = QSpinBox()
        self.y2_spb = QSpinBox()
        self.answer1_spb = QSpinBox()
        self.answer2_spb = QSpinBox()
        self.spbs = [self.x1_spb, self.x2_spb, self.y1_spb, self.y2_spb, self.answer1_spb, self.answer2_spb]
        for spb in self.spbs:
            spb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            spb.setRange(0, 1000)
        if self.operation in [OperationType.MULTIPLICATION, OperationType.DIVISION]:
            self.x1_spb.setMinimum(max(2, self.x1_spb.value()))
            self.x2_spb.setMinimum(max(self.x1_spb.value(), self.x2_spb.value()))
            self.y1_spb.setMinimum(max(2, self.y1_spb.value()))
            self.y2_spb.setMinimum(max(self.y1_spb.value(), self.y2_spb.value()))
        values = Setting.load_range(self.username, self.operation.name)
        for value, spb in zip(values, self.spbs):
            spb.setValue(value)
        for spb in self.spbs:
            spb.valueChanged.connect(self.save)
        self.set_layout()

    def set_layout(self):
        grid = QGridLayout()
        grid.addWidget(QLabel('X:'), 0, 0, 1, 1)
        grid.addWidget(self.x1_spb, 0, 1, 1, 1)
        grid.addWidget(QLabel('~'), 0, 2, 1, 1)
        grid.addWidget(self.x2_spb, 0, 3, 1, 1)
        grid.addWidget(QLabel('Y:'), 1, 0, 1, 1)
        grid.addWidget(self.y1_spb, 1, 1, 1, 1)
        grid.addWidget(QLabel('~'), 1, 2, 1, 1)
        grid.addWidget(self.y2_spb, 1, 3, 1, 1)
        grid.addWidget(QLabel('Z:'), 2, 0, 1, 1)
        grid.addWidget(self.answer1_spb, 2, 1, 1, 1)
        grid.addWidget(QLabel('~'), 2, 2, 1, 1)
        grid.addWidget(self.answer2_spb, 2, 3, 1, 1)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(self.operation.name))
        layout.addLayout(grid)
        # layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(layout)

    @logger.catch
    def save(self, *args):
        xs = x1, x2 = sorted([self.x1_spb.value(), self.x2_spb.value()])
        ys = y1, y2 = sorted([self.y1_spb.value(), self.y2_spb.value()])
        answers = sorted([self.answer1_spb.value(), self.answer2_spb.value()])
        # 检查结果范围
        if self.operation == OperationType.ADDITION:
            a1 = x1 + y1
            a2 = x2 + y2
        elif self.operation == OperationType.SUBTRACTION:
            a1 = x1 - y2
            a2 = x2 - y1
            assert a2 >= 0
        elif self.operation == OperationType.MULTIPLICATION:
            a1 = x1 * y1
            a2 = x2 * y2
        elif self.operation == OperationType.DIVISION:
            a1 = x1 // y2
            a2 = x2 // y1
            assert a2 >= 0
        else:
            return
        answers = [max(max(0, a1), answers[0]), min(max(0, a2), answers[1])]
        self.answer1_spb.setValue(answers[0])
        self.answer2_spb.setValue(answers[1])
        Setting.save_range(username=self.username, key=self.operation.name, values=xs + ys + answers)


class ValueLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        self.mousePressEvent = lambda e: None
        self.mouseMoveEvent = lambda e: None
        self.mouseReleaseEvent = lambda e: None


class PlayGround(QDialog):
    @logger.catch
    def __init__(self, parent=None, seconds=60):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.operation: OperationType = self.parent().operation
        self.username: str = self.parent().username
        values = Setting.load_range(self.username, self.operation.name)
        self.x1, self.x2, self.y1, self.y2, self.a1, self.a2 = values
        self.seconds: int = seconds
        self.setWindowTitle(f'{self.seconds} Seconds Play')

        self.start_at = time.time()
        self.stop_at = self.start_at + self.seconds
        self.progress = QProgressBar()
        self.progress.setMaximum(10000)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(1)
        self.value1_spb = QSpinBox()
        self.value1_spb.setLineEdit(ValueLineEdit())
        self.value1_spb.setMaximum(max(self.x2, self.y2))
        self.value1_spb.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.operation_lbl = QLabel(self.operation.value[0])
        self.value2_spb = QSpinBox()
        self.value2_spb.setLineEdit(ValueLineEdit())
        self.value2_spb.setMaximum(max(self.x2, self.y2))
        self.value2_spb.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.equal_lbl = QLabel('=')
        self.answer_spb = QSpinBox()
        self.answer_spb.setAlignment(Qt.AlignCenter)
        self.answer_spb.setRange(0, 2 ** 16)
        self.answer_spb.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.answer_spb.focusOutEvent = lambda x: self.answer_spb.setFocus()
        self.answer_spb.lineEdit().returnPressed.connect(self.check)
        self.tests: List[List] = []
        self.widgets = [self.value1_spb, self.operation_lbl, self.value2_spb, self.equal_lbl, self.answer_spb]
        for w in self.widgets:
            w.setStyleSheet('border: none; background: transparent; font-size: 128px;')
        self.answer_spb.setStyleSheet('font-size: 128px;')
        self.result_edt = QPlainTextEdit()
        self.result_edt.setReadOnly(True)
        self.result_edt.setVisible(False)
        self.set_layout()
        self.show()
        self.next()
        self.timer = self.startTimer(50, Qt.PreciseTimer)

    def set_layout(self):
        body = QHBoxLayout()
        body.addStretch()
        body.addWidget(self.value1_spb)
        body.addWidget(self.operation_lbl)
        body.addWidget(self.value2_spb)
        body.addWidget(self.equal_lbl)
        body.addWidget(self.answer_spb)
        body.addStretch()
        layout = QVBoxLayout()
        layout.addWidget(self.progress)
        layout.addStretch()
        layout.addLayout(body)
        layout.addWidget(self.result_edt)
        layout.addStretch()
        self.setLayout(layout)

    def timerEvent(self, *args, **kwargs):
        progress = int((time.time() - self.start_at) / self.seconds * self.progress.maximum())
        self.progress.setValue(progress)
        if time.time() >= self.stop_at:
            self.killTimer(self.timer)
            self.score()

    @logger.catch
    def next(self):
        while True:
            x = random.randint(self.x1, self.x2)
            y = random.randint(self.y1, self.y2)
            opc = self.operation.value[1]
            ref = int(eval(f'{x}{opc}{y}'))
            if self.a1 <= ref <= self.a2:
                self.value1_spb.setValue(x)
                self.value2_spb.setValue(y)
                self.answer_spb.clear()
                self.answer_spb.start_at = time.time()
                self.answer_spb.setFocus()
                break

    @logger.catch
    def check(self, *args):
        if not self.answer_spb.lineEdit().text():
            return
        value1 = self.value1_spb.value()
        value2 = self.value2_spb.value()
        opc = self.operation.value[1]
        oph = self.operation.value[0]
        answer = self.answer_spb.value()
        ref = int(eval(f'{value1}{opc}{value2}'))
        correct = answer == ref
        start_at = self.answer_spb.start_at
        finish_at = time.time()
        self.tests.append([
            value1,
            opc,
            oph,
            value2,
            answer,
            ref,
            correct,
            [finish_at - start_at, start_at, finish_at]
        ])
        self.next()

    @logger.catch
    def score(self):
        for widget in self.widgets:
            widget.setVisible(False)
        self.progress.setVisible(False)
        self.result_edt.setVisible(True)

        pipe = redisc.pipeline(transaction=True)
        for test in self.tests:
            pipe.rpush(f'{self.username}/tests', ujson.dumps(test))
        pipe.execute()
        print(f'{self.username}/tests', redisc.llen(f'{self.username}/tests'))

        incorrect = [test for test in self.tests if test[6] is False]
        correct = [test for test in self.tests if test[6] is True]
        total = len(self.tests)
        rate_incorrect = len(incorrect) / max(1, total)
        speed_correct = [test[7][0] for test in correct]
        speed_correct = statistics.mean(speed_correct) if speed_correct else 0

        text = f'错误: {len(incorrect)} / {total} [{rate_incorrect:0.1%}]\n速度: {speed_correct:0.1f}秒\n'
        for value1, opc, oph, value2, answer, ref, correct, (t, t1, t2) in incorrect:
            text += f'{value1} {oph} {value2} = {answer} [{ref}]\n'
        self.result_edt.setPlainText(text)


class Calculator(QDialog):
    @logger.catch
    def __init__(self, parent=None, operation=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.operation: OperationType = operation
        self.username: str = self.parent().username
        self.setWindowTitle(f'{self.username}/{self.operation.value[0]}/{self.__class__.__name__}')
        self.range_lbl = QLabel()
        self.config_btn = QPushButton('Config')
        self.seconds_cmb = QComboBox()

        for i, seconds in enumerate([] + list(range(60, 660, 60))):
            self.seconds_cmb.addItem(f'{seconds}')
            self.seconds_cmb.setItemData(i, Qt.AlignRight, Qt.TextAlignmentRole)
        self.start_btn = QPushButton(f'Start {self.operation.value[0]} Test')
        self.config_btn.clicked.connect(self.on_config)
        self.update_range()
        self.start_btn.clicked.connect(self.on_started)
        self.set_layout()
        self.start_btn.setFocus()

    def set_layout(self):
        header = QGridLayout()
        header.addWidget(self.config_btn, 0, 0, 1, 2)
        header.addWidget(QLabel('测试时间(秒):'), 1, 0, 1, 1)
        header.addWidget(self.seconds_cmb, 1, 1, 1, 1)
        header.addWidget(self.start_btn, 2, 0, 1, 2)
        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addStretch()
        self.setLayout(layout)

    def update_range(self, *args):
        values = Setting.load_range(self.username, self.operation.name)
        x1, x2, y1, y2, a1, a2 = values
        self.config_btn.setText(f'[{x1},{x2}] {self.operation.value[0]} [{y1},{y2}] = [{a1},{a2}]')
        if all(map(lambda x: x == 0, values)):
            self.on_config()

    def on_config(self, *args):
        RangeSetting(parent=self).exec()
        self.update_range()

    def on_started(self, *args):
        seconds = int(self.seconds_cmb.currentText())
        playground = PlayGround(parent=self, seconds=seconds)
        playground.exec()


class LoginPage(QDialog):
    @logger.catch
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle('登录')
        self.names = ['徐琬清', '徐梓清', '徐驸骅', ]
        self.buttons = [QPushButton(n) for n in self.names]
        for button in self.buttons:
            button.clicked.connect(self.on_login)
        self.set_layout()

    def set_layout(self):
        layout = QVBoxLayout()
        for button in self.buttons:
            layout.addWidget(button)
        self.setLayout(layout)

    def on_login(self, *args):
        configurator = Configurator(parent=self, username=self.sender().text())
        configurator.exec()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    # app.setAttribute(Qt.AA_EnableHighDpiScaling)
    window = LoginPage()
    window.show()
    app.exec()
