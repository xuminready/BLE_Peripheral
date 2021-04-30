#!/usr/bin/env python3

import math

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

try:
    from gi.repository import GObject  # python3
except ImportError:
    import gobject as GObject  # python2

from ble import (
    Advertisement,
    Characteristic,
    Service,
    Application,
    find_adapter,
    GATT_CHRC_IFACE,
)

from mpu6050 import (
    MPU_Init,
    read_raw_data,
    ACCEL_XOUT_H,
    ACCEL_YOUT_H,
    ACCEL_ZOUT_H,
    GYRO_XOUT_H,
    GYRO_YOUT_H,
    GYRO_ZOUT_H,
)

MainLoop = None
try:
    from gi.repository import GLib

    MainLoop = GLib.MainLoop
except ImportError:
    import gobject as GObject

    MainLoop = GObject.MainLoop

mainloop = None


def readSensorData():
    # Read Accelerometer raw value
    acc_x = read_raw_data(ACCEL_XOUT_H)
    acc_y = read_raw_data(ACCEL_YOUT_H)
    acc_z = read_raw_data(ACCEL_ZOUT_H)

    # Read Gyroscope raw value
    gyro_x = read_raw_data(GYRO_XOUT_H)
    gyro_y = read_raw_data(GYRO_YOUT_H)
    gyro_z = read_raw_data(GYRO_ZOUT_H)

    # Full scale range +/- 250 degree/C as per sensitivity scale factor
    Ax = acc_x / 16384.0 * 9.8
    Ay = acc_y / 16384.0 * 9.8
    Az = acc_z / 16384.0 * 9.8

    Gx = gyro_x / 131.0
    Gy = gyro_y / 131.0
    Gz = gyro_z / 131.0

    return dbus.Array([dbus.Byte(b) for b in (
            math.floor(Ax).to_bytes(4, 'little', signed=True) + math.floor((Ax % 1) * 1000000).to_bytes(4, 'little',
                                                                                                        signed=True)
            + math.floor(Ay).to_bytes(4, 'little', signed=True) + math.floor((Ay % 1) * 1000000).to_bytes(4,
                                                                                                          'little',
                                                                                                          signed=True)
            + math.floor(Az).to_bytes(4, 'little', signed=True) + math.floor((Az % 1) * 1000000).to_bytes(4,
                                                                                                          'little',
                                                                                                          signed=True)
            + math.floor(Gx).to_bytes(4, 'little', signed=True) + math.floor((Gx % 1) * 1000000).to_bytes(4,
                                                                                                          'little',
                                                                                                          signed=True)
            + math.floor(Gy).to_bytes(4, 'little', signed=True) + math.floor((Gy % 1) * 1000000).to_bytes(4,
                                                                                                          'little',
                                                                                                          signed=True)
            + math.floor(Gz).to_bytes(4, 'little', signed=True) + math.floor((Gz % 1) * 1000000).to_bytes(4,
                                                                                                          'little',
                                                                                                          signed=True))],
                      'y')


def str_to_dbusarray(word):
    """Helper function to represent Python string as D-Dbus Byte array"""
    return dbus.Array([dbus.Byte(ord(letter)) for letter in word], 'y')


BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"


class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.freedesktop.DBus.Error.InvalidArgs"


class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotSupported"


class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotPermitted"


class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.InvalidValueLength"


class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.Failed"


class BLEService(Service):
    """
    Dummy test service that provides characteristics and descriptors that
    exercise various API functionality.

    """

    service_UUID = "42673824-33e5-4aeb-ae5c-38dc66250000"

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.service_UUID, True)
        self.add_characteristic(NameCharacteristic(bus, 0, self))
        self.add_characteristic(DemoCharacteristic(bus, 1, self))


class NameCharacteristic(Characteristic):
    uuid = "42673824-33e5-4aeb-ae5c-38dc66250001"
    description = b"service name"

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["read"], service,
        )

    def ReadValue(self, options):
        value = bytearray('MPU6050', encoding="utf8")
        return value


class DemoCharacteristic(Characteristic):
    uuid = "42673824-33e5-4aeb-ae5c-38dc66250002"
    description = b"Motion sensor data"

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["read", 'notify'], service,
        )
        self.notifying = False

        self.count = 0

    def ReadValue(self, options):
        return readSensorData()

    def NotifyTimer_cb(self):
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': readSensorData()}, [])
        return self.notifying

    def StartNotifyTimer(self):
        if not self.notifying:
            return

        print('start notify timer')
        GLib.timeout_add(1000, self.NotifyTimer_cb)

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True
        self.StartNotifyTimer()

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False
        self.StartNotifyTimer()


class BLEAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, "peripheral")
        self.add_manufacturer_data(
            0xFFFF, [0x70, 0x74],
        )
        self.add_service_uuid(BLEService.service_UUID)

        self.add_local_name("MotionSensor")
        self.include_tx_power = True


def register_ad_cb():
    print("Advertisement registered")


def register_ad_error_cb(error):
    print("Failed to register advertisement: " + str(error))
    mainloop.quit()


def register_app_cb():
    print("GATT application registered")


def register_app_error_cb(error):
    print("Failed to register application: " + str(error))
    mainloop.quit()


def main():
    MPU_Init()  # init MPU6050
    global mainloop

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # get the system bus
    bus = dbus.SystemBus()
    # get the ble controller
    adapter = find_adapter(bus)

    if not adapter:
        print("GattManager1 interface not found")
        return

    adapter_obj = bus.get_object(BLUEZ_SERVICE_NAME, adapter)

    adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")

    # powered property on the controller to on
    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

    # Get manager objs
    service_manager = dbus.Interface(adapter_obj, GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(adapter_obj, LE_ADVERTISING_MANAGER_IFACE)

    advertisement = BLEAdvertisement(bus, 0)
    obj = bus.get_object(BLUEZ_SERVICE_NAME, "/org/bluez")

    app = Application(bus)
    app.add_service(BLEService(bus, 2))

    mainloop = MainLoop()

    ad_manager.RegisterAdvertisement(
        advertisement.get_path(),
        {},
        reply_handler=register_ad_cb,
        error_handler=register_ad_error_cb,
    )

    print("Registering GATT application...")

    service_manager.RegisterApplication(
        app.get_path(),
        {},
        reply_handler=register_app_cb,
        error_handler=[register_app_error_cb],
    )

    mainloop.run()
    # ad_manager.UnregisterAdvertisement(advertisement)
    # dbus.service.Object.remove_from_connection(advertisement)


if __name__ == "__main__":
    main()
