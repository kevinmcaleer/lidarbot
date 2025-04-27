from picomotordriver import KitronikPicoMotor
from time import sleep

driver = KitronikPicoMotor()

# Move Forward (both motors)
driver.motorOn(1,'f',100)
driver.motorOn(2,'f',100)
sleep(2)

# Stop!
driver.motorOff(1)
driver.motorOff(2)
sleep(1)