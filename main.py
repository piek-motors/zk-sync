from pyzkaccess import ZKAccess


print('hello')

found = ZKAccess.search_devices('192.168.0.255', dllpath='./plcommpro.dll')
print(f"found {len(found)} devices")
