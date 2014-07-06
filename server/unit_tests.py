#!/usr/bin/python

import random
import unittest
import common
import coreEngine
import sensorino
import database
from errors import *

class TestX(unittest.TestCase):


    # assertEqual(a, b)   a == b   
    # assertNotEqual(a, b)    a != b   
    # assertTrue(x)   bool(x) is True      
    # assertFalse(x)  bool(x) is False     
    # assertIs(a, b)  a is b  2.7
    # assertIsNot(a, b)   a is not b  2.7
    # assertIsNone(x)     x is None   2.7
    # assertIsNotNone(x)  x is not None   2.7
    # assertIn(a, b)  a in b  2.7
    # assertNotIn(a, b)   a not in b  2.7
    # assertIsInstance(a, b)  isinstance(a, b)    2.7
    # assertNotIsInstance(a, b)   not isinstance(a, b)    2.7
    # assertRaises(SomeException)
    # self.assertRaisesRegexp(ValueError, "invalid literal for.*XYZ'$", int, 'XYZ')


    def setUp(self):
        common.Config.setConfigFile("sensorino_unittests.ini")
        database.DbCreator.createEmpty(common.Config.getDbFilename())
        self.engine=coreEngine.Core()
        self.engine.start()

    def tearDown(self):
        pass



    def test_sensorino_creation_deletion(self):
        self.assertTrue(self.engine.addSensorino(sensorino.Sensorino("tokenSensorino", "1234")))
        self.assertRaises(FailToAddSensorinoError, self.engine.addSensorino, (sensorino.Sensorino("tokenSensorino", "1234")))
        sens=self.engine.findSensorino(saddress="1234")
        self.assertIsNotNone(sens)
        self.assertTrue(self.engine.delSensorino(sens.address))

    def test_findMissingSensorino(self):
        with self.assertRaises(SensorinoNotFoundError) as err:
            self.engine.findSensorino( saddress="666")

    def test_sensorino_nameless_creation_deletion(self):
        self.assertTrue(self.engine.addSensorino(sensorino.Sensorino(None, "1234")))
        sens=self.engine.findSensorino(saddress="1234")
        self.assertIsNotNone(sens)
        self.assertTrue(self.engine.delSensorino(sens.address))


    def test_Service(self):
        self.assertTrue(self.engine.addSensorino(sensorino.Sensorino("tokenSensorino", "1234")))
        sens=self.engine.findSensorino(saddress="1234")
        self.assertTrue(self.engine.createService(sens.address, "testService", 1 ))
        services=self.engine.getServicesBySensorino(sens.address)
        s=None
        for service in services: 
            if "testService" == service.name:
                s=service
                break
        self.assertIsNotNone(s)
        
        # now create channels
        newChans=[{'dataType':'Foo', 'type':"RW"}]
        chans=s.setChannels(newChans) 
        self.assertEqual(chans, 1)

        # publish 
        s.logData(None, "test")
        s.logData(None, "test")
        s.logData(None, "test")
        s.logData(None, "test")
        s.logData(None, "test")

        # getData back
        data=s.getLogs(1)
        self.assertTrue(5==len(data))


#TODO add update service test       

        
          

if __name__ == '__main__':

    suite = unittest.TestLoader().loadTestsFromTestCase(TestX)
    unittest.TextTestRunner(verbosity=2).run(suite)
