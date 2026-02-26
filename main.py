from pyzkaccess import ZKAccess


print('hello')

found = ZKAccess.search_devices(dllpath='./plcommpro.dll')
print(f"found {len(found)} devices")
