from picomotordriver import KitronikPicoMotor
from time import sleep

driver = KitronikPicoMotor()

driver.motorOn(1,'f',100)
driver.motorOn(2,'f',100)
sleep(2)
driver.motorOff(1)
driver.motorOff(2)
sleep(1)