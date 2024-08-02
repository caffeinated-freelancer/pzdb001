import win32com.client


def get_usb_info():
    # Find all USB devices
    wmi = win32com.client.GetObject("winmgmts:")
    usb_devices = wmi.ExecQuery("SELECT * FROM Win32_USBHub")

    for device in usb_devices:
        print(f"Device: {device.DeviceID}")
        print(f"PNP Device ID: {device.PNPDeviceID}")
        print(f"Description: {device.Description}")
        print(f"Vendor ID: {device.DeviceID.split('\\')[1][:4]}")
        print(f"Product ID: {device.DeviceID.split('\\')[1][4:8]}")
        print(f"Serial Number: {device.PNPDeviceID.split('\\')[-1]}")
        print("-" * 20)
