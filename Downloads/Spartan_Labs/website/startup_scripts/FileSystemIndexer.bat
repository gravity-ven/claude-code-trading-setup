@echo off
REM File System Indexer Silent Launcher
REM Batch wrapper for PowerShell script
powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0FileSystemIndexer.ps1"
exit
