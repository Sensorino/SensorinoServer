#!/usr/bin/env python

#-------------------------------------------------------------------------------
# Purpose:
#
# Author:      Elektroid
#
#-------------------------------------------------------------------------------

import sys
sys.path.append("..")
import protocol
import json


def main():
    prot=protocol.Protocol()
    json_data = open(sys.argv[1])
    data=json_data.read()
    print "treat :"+data
    print prot.treatMessage(data)



if __name__ == '__main__':
    main()
