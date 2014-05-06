#-------------------------------------------------------------------------------
# Name:        modulo1
# Purpose:
#
#
# Created:     08/03/2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys
sys.path.append("..")
import json
import serialEngine
import messageParser


def main():
    parser=messageParser.MessageParser()

    engine=serialEngine.SerialEngine("\\.\COM3")
    engine.startParsing(parser)


if __name__ == '__main__':
    main()
