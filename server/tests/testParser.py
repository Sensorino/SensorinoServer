#-------------------------------------------------------------------------------
# Purpose:
#
# Author:      Elektroid
#
#-------------------------------------------------------------------------------

import protocol
import sys
sys.path.append("..")
import json


def main():
    protocol=protocol.Protocol()
    json_data = open(sys.argv[1])
    print protocol.treatMessage(json_data)



if __name__ == '__main__':
    main()
