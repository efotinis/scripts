:: Resets monitor.
:: Fix for laptop BIOS losing track of the monitor on resume.
:: Note: DEVCON requires admin rights.
@echo off
devcon remove =monitor
devcon rescan
