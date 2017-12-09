#!/usr/bin/env python2
"""
Authors: Evan Bluhm
Largely based on github.com/djhazee/strangerlights

"""

import os
# import fileinput
import argparse
import time
import logging
import sys
import random
from neopixel import *
# from pprint import pprint
from slackclient import SlackClient

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Start up random seed
random.seed()

# LED strip configuration:
LED_COUNT = 50      # Number of LED pixels.
LED_PIN = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT = False   # True to invert the signal (when using NPN transistor level shift)

#Predefined Colors and Masks
OFF = Color(0,0,0)
WHITE = Color(255,255,255)
RED = Color(255,0,0)
GREEN = Color(0,255,0)
BLUE = Color(0,0,255)
PURPLE = Color(128,0,128)
YELLOW = Color(255,255,0)
ORANGE = Color(255,50,0)
TURQUOISE = Color(64,224,208)
RANDOM = Color(random.randint(0,255),random.randint(0,255),random.randint(0,255))

#list of colors, tried to match the show as close as possible
COLORS = [YELLOW,GREEN,RED,BLUE,ORANGE,TURQUOISE,GREEN,
          YELLOW,PURPLE,RED,GREEN,BLUE,YELLOW,RED,TURQUOISE,GREEN,RED,BLUE,GREEN,ORANGE,
          YELLOW,GREEN,RED,BLUE,ORANGE,TURQUOISE,RED,BLUE, 
          ORANGE,RED,YELLOW,GREEN,PURPLE,BLUE,YELLOW,ORANGE,TURQUOISE,RED,GREEN,YELLOW,PURPLE,
          YELLOW,GREEN,RED,BLUE,ORANGE,TURQUOISE,GREEN,BLUE,ORANGE]

#bitmasks used in scaling RGB values
REDMASK = 0b111111110000000000000000
GREENMASK = 0b000000001111111100000000
BLUEMASK = 0b000000000000000011111111

# Other vars
# ALPHABET = '*******abcdefghijklm********zyxwvutsrqpon*********'  #alphabet that will be used
ALPHABET = '!*z*y*xw*vu*t**k*l*m*n*op*q*rs***j*i*hgf*ed*cb*a**'  #alphabet that will be used
LIGHTSHIFT = 0  #shift the lights down the strand to the other end 
FLICKERLOOP = 3  #number of loops to flicker

class StrangerBot(object):
    """
    This is actually the first bot better than 100bot (not really <3 u 100bot)

    Hard-coding the bot ID for now, but will pass those in to the constructor
    later
    """

    def __init__(self, slack_token):

        self._bot_id = "U4M6Z42JK"
        self._READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose
        self.sc = SlackClient(slack_token)
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
        self.strip.begin()

    def listen(self):
        slack_client = self.sc
        if slack_client.rtm_connect():
            logging.info("StrangerBot connected and running!")
            while True:
                event = parse_slack_output(slack_client.rtm_read())
                recv_msg = event.get('text').lower().translate(None, string.punctuation)
                if event and recv_msg != "":
                    logging.info("event received from slack: %s",
                                 event.get('text'))
                    initLights(self.strip)
                    time.sleep(random.randint(5,9))
                    for i in range(20):
                        flicker(self.strip,random.randint(LIGHTSHIFT,len(ALPHABET)+LIGHTSHIFT))
                        time.sleep(random.randint(10,50)/1000.0)
                    blinkWords(self.strip, recv_msg)
                    runBlink(self.strip)
                time.sleep(self._READ_WEBSOCKET_DELAY)
        else:
            logging.error("Connection failed. Invalid Slack token or bot ID?")


def parse_slack_output(slack_rtm_output):
    """
    The Slack Real Time Messaging API is an events firehose. This parsing
    function returns the last-seen message if there is one, otherwise returns
    None
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            # We are a creepy bot, we listen to everything you say
            if output and 'text' in output:
                return output
    return None


def try_load_env_var(var_name):
    """Read environment variables into a configuration object

    Args:
        var_name (str): Environment variable name to attempt to read
    """
    value = None
    if var_name in os.environ:
        value = os.environ[var_name]
    else:
        logging.info(
            "Environment variable %s is not set. Will try to read from command-line",
            var_name)
    return value


def initLights(strip):
  """
  initializes the light strand colors 
  inputs: 
    strip = color strip instance to action against
  outputs:
    <none>
  """
  colorLen = len(COLORS)
  #Initialize all LEDs
  for i in range(len(ALPHABET)):
    strip.setPixelColor(i+LIGHTSHIFT, COLORS[i%colorLen])
  strip.show()


def blinkWords(strip, word):
  """
  blinks a string of letters
  inputs: 
    strip = color strip instance to action against
    word = word to blink
  outputs:
    <none>
  """
  #create a list of jumbled ints
  s = list(range(len(ALPHABET)))
  random.shuffle(s)

  #first, kill all lights in a semi-random fashion
  for led in range(len(ALPHABET)):
    strip.setPixelColor(s[led]+LIGHTSHIFT, OFF)
    strip.show()
    time.sleep(random.randint(10,80)/1000.0)

  #quick delay
  time.sleep(1.75)

  #if letter in alphabet, turn on 
  #otherwise, stall
  for character in word:
    if character in ALPHABET:
      strip.setPixelColor(ALPHABET.index(character)+LIGHTSHIFT, RED)
      strip.show()
      time.sleep(1)
      strip.setPixelColor(ALPHABET.index(character)+LIGHTSHIFT, OFF)
      strip.show()
      time.sleep(.5)
    else:
      time.sleep(.75)


def flicker(strip, ledNo):
  """
  creates a flickering effect on a bulb
  inputs: 
    strip = color strip instance to action against
    ledNo = LED position on strand, as integer.
  outputs:
    <none>
  """
  #get origin LED color
  origColor = strip.getPixelColor(ledNo)

  #do FLICKERLOOP-1 loops of flickering  
  for i in range(0,FLICKERLOOP-1):

    #get current LED color, break out to individuals
    currColor = strip.getPixelColor(ledNo)
    currRed = (currColor & REDMASK) >> 16
    currGreen = (currColor & GREENMASK) >> 8
    currBlue = (currColor & BLUEMASK)

    #turn off for a random short period of time
    strip.setPixelColor(ledNo, OFF)
    strip.show()
    time.sleep(random.randint(10,50)/1000.0)

    #turn back on at random scaled color brightness
    #modifier = random.randint(30,120)/100
    modifier = 1
    #TODO: fix modifier so each RGB value is scaled. 
    #      Doesn't work that well so modifier is set to 1. 
    newBlue = int(currBlue * modifier)
    if newBlue > 255:
      newBlue = 255
    newRed = int(currRed * modifier)
    if newRed > 255:
      newRed = 255
    newGreen = int(currGreen * modifier) 
    if newGreen > 255:
      newGreen = 255
    strip.setPixelColor(ledNo, Color(newRed,newGreen,newBlue))
    strip.show()
    #leave on for random short period of time
    time.sleep(random.randint(10,80)/1000.0)

  #restore original LED color
  strip.setPixelColor(ledNo, origColor)

def runBlink(strip):
  """
  blinks the RUN letters
  inputs: 
    strip = color strip instance to action against
  outputs:
    <none>
  """
  word = "run"
  #first blink the word "run", one letter at a time
  blinkWords(strip, word)

  #now frantically blink all 3 letters
  for loop in range(20):
    #turn on all three letters at the same time
    for character in word:
      if character in ALPHABET:
        strip.setPixelColor(ALPHABET.index(character)+LIGHTSHIFT, RED)
    strip.show()

    time.sleep(random.randint(15,100)/1000.0)

    #turn off all three letters at the same time
    for character in word:
      if character in ALPHABET:
        strip.setPixelColor(ALPHABET.index(character)+LIGHTSHIFT, OFF)
    strip.show()

    time.sleep(random.randint(50,150)/1000.0)

  #now frantically blink all lights 
  for loop in range(15):
    #initialize all the lights
    initLights(strip)

    time.sleep(random.randint(50,150)/1000.0)

    #kill all lights
    for led in range(len(ALPHABET)):
      strip.setPixelColor(led+LIGHTSHIFT, OFF)
    strip.show()

    time.sleep(random.randint(50,150)/1000.0)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug",
        dest="debug",
        help="Read input from debug file instead of user input",
        type=str,
        required=False)
    parser.add_argument(
        "--slack-token",
        dest="slack_token",
        help="Slack client token",
        type=str,
        required=False,
        default=try_load_env_var("SLACK_TOKEN"))
    args = parser.parse_args()
    if not (args.slack_token):
        parser.print_help()
        sys.exit(1)

    eb = StrangerBot(slack_token=args.slack_token)
    eb.listen()


if __name__ == "__main__":
    main()
