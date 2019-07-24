# Log WAN IP changes to a synced file.
# Useful as a makeshift dyndns.

import os, time, myip

OUTFILE = os.path.expandvars('%SyncMain%\\data\\wan.log')
INTERVAL_MINUTES = 5

def logLine(s):
    with open(OUTFILE, 'a', encoding='ascii') as f:
        print(s, file=f)

def get_ip_or_error():
    try:
        return myip.query()
    except Exception as x:
        return repr(x)

if __name__ == '__main__':
    print(f'updating WAN IP log every {INTERVAL_MINUTES} minute(s); hit Ctrl-C to end...')
    logLine('--- running on ' + os.environ['COMPUTERNAME'])
    lastIP = None
    while True:
        timestamp = time.ctime()
        try:
            ip = get_ip_or_error()
            if ip != lastIP:
                logLine(f'{timestamp} {ip}')
                lastIP = ip
            time.sleep(INTERVAL_MINUTES * 60)
        except KeyboardInterrupt:
            logLine(f'{timestamp} end')
            break

# The original PowerShell implementation is shown below. It was replaced 
# by a Python script simply for the vastly more elegant Ctrl-C handling.
'''
[CmdletBinding()]
param(
    [int]$IntervalMinutes = 5,
    [string]$OutFile = '~\Dropbox\data\wan.log'
)

Set-StrictMode -Version Latest

function LogLine ($s) {
    $s | Out-File -LiteralPath $OutFile -Append -Encoding Ascii
}

LogLine "--- running on $Env:COMPUTERNAME"
$lastIP = '0.0.0.0'  # dummy value
while ($true) {
    $timestamp = Get-Date -Format o
    $exiting = $true
    try {
        $ip = myip.py
        if ($true -or $ip -ne $lastIP) {
            LogLine "$timestamp $ip"
            $lastIP = $ip
        }
        Start-Sleep -Seconds 10 $($IntervalMinutes * 60)
        $exiting = $false
    }
    finally {
        if ($exiting) {
            LogLine "$timestamp end"
        }
    }
}
'''
