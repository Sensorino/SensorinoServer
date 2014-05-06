#!/usr/bin/python
import sqlite3
import common

class DbCreator:

    @staticmethod
    def createEmpty(filename=None):

        if None == filename:
            filename=common.Config.getDbFilename()                

        print "create db in file :"+filename
        conn = sqlite3.connect(filename)
        print conn

        c = conn.cursor()



        c.execute('''DROP TABLE IF EXISTS sensorinos''')
        c.execute('''CREATE TABLE sensorinos
                     (address TEXT PRIMARY KEY, name TEXT,  description TEXT, owner TEXT, location TEXT)''')


        c.execute('''DROP TABLE IF EXISTS services''')
        c.execute('''CREATE TABLE services
                     (serviceId INTEGER PRIMARY KEY, name TEXT, stype TEXT, dataType TEXT, saddress TEXT, state TEXT)''')


        c.execute('''DROP TABLE IF EXISTS dataServicesLog''')
        c.execute('''CREATE TABLE dataServicesLog
                     (saddress TEXT, serviceId INTEGER, value TEXT, timestamp TEXT)''')


        # Save (commit) the changes
        conn.commit()

        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        conn.close()

if __name__ == '__main__':
    DbCreator.createEmpty()
