#-------------------------------------------------------------------------------
# Purpose:
#
# Author:      Elektroid
#
#-------------------------------------------------------------------------------

import sys
sys.path.append("..")
import json
import messageParser


def main():
    parser=messageParser.MessageParser()
    json_data = open(sys.argv[1])
    parser.processMessage(json.load(json_data))



if __name__ == '__main__':
    main()
