import pyttsx3
import io
import sys
from loguru import logger

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

engine = pyttsx3.init()

""" RATE"""
engine.setProperty('rate', 150)
rate = engine.getProperty('rate')
logger.info(f'set rate={rate}')

"""VOLUME"""
engine.setProperty('volume', 1)
volume = engine.getProperty('volume')
logger.info(f'set volume={volume}')

"""VOICE"""
engine.setProperty('voice', 'zh')
voice = engine.getProperty('voice')
logger.info(f'set voice={voice}')

lines = ['1 + 1 =', '12 + 4 =']
for line in lines:
    engine.say(line)

engine.runAndWait()
engine.stop()
