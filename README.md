# BLE_Peripheral
create BLE peripheral using BlueZ, Dbus and python3 on Linux

# usage: 

### Demo1
python3 app.py

### Demo2 
(require MPU6050 sensor)

sudo apt-get install -y python3-dbus python3-smbus

python3 motionSensorApp.py 

## bluetooth pairing request on iPhone
solution, stop Bluez Battery plugin from loading at boot.

modify Bluez service at /lib/systemd/system/bluetooth.service

`ExecStart=/usr/lib/bluetooth/bluetoothd `**`-P battery`**

[source](https://stackoverflow.com/a/66807717)

# credit
BLE code is modified from
[GitHub: PunchThrough / espresso-ble ](https://github.com/PunchThrough/espresso-ble)

a very good article about BLE with BlueZ, python3
[Creating a BLE Peripheral with BlueZ](https://punchthrough.com/creating-a-ble-peripheral-with-bluez)

more BLE example
[BlueZ examples](https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/test)

[MPU6050 (Accelerometer+Gyroscope) Interfacing with Raspberry Pi](https://www.electronicwings.com/raspberry-pi/mpu6050-accelerometergyroscope-interfacing-with-raspberry-pi)
