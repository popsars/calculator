# -*- coding: utf-8 -*-
import hashlib
import itertools
import math
import os
import pdfkit
import re
from bs4 import BeautifulSoup
from lxml.etree import Element, HTML, SubElement, QName, tostring
from typing import Dict, List, Union


class Config:
    value_min: int = 0
    value_max: int = 20
    numbers: int = 3
    operates: List[str] = ['+', '-']  # 必须是 + - * /
    bracket: bool = True   # 是否含有括号
    length_formula: int = 0

    @classmethod
    def validate(cls):
        assert isinstance(cls.value_min, int)
        assert isinstance(cls.value_max, int)
        assert cls.value_min <= cls.value_max
        assert isinstance(cls.numbers, int) and cls.numbers >= 3
        assert cls.operates and all(map(lambda x: x in ['+', '-', '*', '/'], cls.operates))
        if cls.numbers <= 3:
            cls.bracket = False
        assert isinstance(cls.bracket, bool)
        cls.length_formula = cls.numbers + len(str(cls.value_max)) * (cls.numbers + 1)
        if cls.bracket:
            cls.length_formula += 2


def generate_csv():
    Config.validate()

    operates: str = ''.join(Config.operates).translate(str.maketrans('+-*/', '\u002B\u002D\u00D7\u00F7'))
    filename: str = f'test_{Config.value_min}_{Config.value_max}_{operates}_{Config.numbers}.{int(Config.bracket) if Config.numbers > 3 else 0}.csv'
    with open(filename, 'w', encoding='utf-8') as f:
        for i, question in enumerate(generate_one()):
            f.write(f'{question}\n')
            if i % 1000 == 0 and i > 0:
                print(i, question)


def generate_one():
    values: List[int] = [v for v in range(Config.value_min, Config.value_max + 1)]
    for i, vs in enumerate(itertools.product(*[values] * Config.numbers)):
        vs: List[int] = list(vs)
        for equal_position in range(1, Config.numbers):
            left_part: List[int] = vs[:equal_position]
            right_part: List[int] = vs[equal_position:]

            left_extended = []  # 左侧组合
            for left in get_operated_list(left_part):
                if eval(stringify(left)) >= 0:
                    left_extended.append(left)
                if Config.bracket:
                    for x in get_bracketed_list(left):
                        if eval(stringify(x)) >= 0:
                            left_extended.append(x)

            right_extended = []  # 右侧组合
            for right in get_operated_list(right_part):
                if eval(stringify(right)) >= 0:
                    right_extended.append(right)
                if Config.bracket:
                    for x in get_bracketed_list(right):
                        if eval(stringify(x)) >= 0:
                            right_extended.append(x)

            for a, b in itertools.product(left_extended, right_extended):
                if eval(stringify(a)) == eval(stringify(b)) >= 0:   # 等式成立
                    formula: str = f'{stringify(a)}={stringify(b)}'
                    # 生成题目
                    es: List[Union[int, str]] = [*a, '=', *b]
                    for j, e in enumerate(es):
                        if isinstance(e, int):
                            question = es.copy()
                            question[j] = ' ' + '_' * (Config.length_formula - len(stringify(es[:j])) - len(stringify(es[j + 1:])) - 2) + ' '
                            yield stringify(question)


def get_operated_list(part: List[int]) -> List[Union[int, str]]:
    for operates in itertools.product(*[Config.operates] * (len(part) - 1)):
        _part: List[Union[int, str]] = part.copy()
        for i, operate in zip(range(len(part) - 1, 0, -1), operates[::-1]):
            _part.insert(i, operate)
        yield _part


def get_bracketed_list(part: List[Union[int, str]]) -> List[Union[int, str]]:
    numbers: int = math.ceil(len(part) / 2)
    index_left: List[int] = list(range(0, numbers * 2 - 2, 2))    # 左半括号位置
    index_right: List[int] = list(range(3, numbers * 2, 2))    # 右半括号位置
    # assert len(index_left) == len(index_right)
    for l, r in itertools.product(index_left, index_right):
        if 2 <= r - l < len(part):
            _part: List[Union[int, str]] = part.copy()
            _part.insert(r, ')')
            _part.insert(l, '(')
            if eval(stringify(_part[l + 1: r + 1])) >= 0:   # 括号里的结果不小于0
                yield _part


def stringify(value: List[Union[int, str]]) -> str:
    return ''.join([str(v) for v in value])


def generate_html(filename: str):
    r = re.findall(r'^test_([+-]?\d+)_([+-]?\d+)_([^_]+)_(\d+)\.(\d).csv$', filename.lower())[0]
    Config.value_min = int(r[0])
    Config.value_max = int(r[1])
    Config.operates = list(r[2].translate(str.maketrans('\u002B\u002D\u00D7\u00F7', '+-*/')))
    Config.numbers = int(r[3])
    Config.bracket = bool(r[4])
    Config.validate()

    with open(filename, 'r', encoding='utf-8') as f:
        questions: List[str] = f.read().splitlines()
    # random.shuffle(questions)
    questions.sort(key=lambda x: hashlib.md5(x.encode('utf-8')).hexdigest())

    page_source: str = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Title</title>
    <style type="text/css">
        * {font-family: "Courier New", courier, monospace;}
        .questions {width: 800px;}
        .question {float: left; margin: 10px 20px 10px 20px; font-size: 20px;}
    </style>
</head>
<body>
    <div class="questions"></div>
</body>
</html>
'''
    tree = HTML(page_source)
    e: Element = tree.xpath('//div[@class="questions"]')[0]
    tree.xpath('//head/title')[0].text = filename
    for question in questions:
        q = Element('pre', attrib={'class': 'question'})
        q.text = question
        e.append(q)
    page_source: str = tostring(tree, encoding='utf-8', pretty_print=True).decode('utf-8')
    soup = BeautifulSoup(page_source, 'html.parser')
    with open(f'{os.path.splitext(filename)[0]}.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

    from pdfkit.configuration import Configuration
    configuration = Configuration(wkhtmltopdf='./wkhtmltopdf.exe')
    pdf = pdfkit.PDFKit(soup.prettify(), type_='string', configuration=configuration)
    pdf.to_pdf('out.pdf')
    # pdfkit.from_string(soup.prettify(), f'{os.path.splitext(filename)[0]}.pdf')


if __name__ == '__main__':
    generate_csv()
    generate_html('test_0_20_+-_3.0.csv')
    # generate_html('test_0_20_+-_4.0.csv')
    # generate_html('test_0_20_+-_4.1.csv')
