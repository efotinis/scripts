s = ''
for i in range(32, 256, 32):
    s += ''.join([chr(c) for c in range(i, i+32)]) + '\r\n'
        
f = file('c:\\documents and settings\\elias\\desktop\\asc', 'wb')
f.write(s)
f.close()

