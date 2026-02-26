from pyzkaccess import ZKAccess


print('hello')

found = ZKAccess.search_devices('192.168.1.255', dllpath='./plcommpro.dll')
print(found)
