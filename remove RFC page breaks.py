import re
rx = re.compile(r'\n\n\nBerners-Lee, et al +Informational +\[Page \d+\]\n\f\n(?:RFC 1945 +HTTP/1\.0 +May 1996\n\n\n)?')
s = file(r'D:\ref\RFC\rfc1945.txt').read()
s = rx.sub('', s)
file(r'c:\documents and settings\elias\desktop\rfc1945.txt', 'w').write(s)
