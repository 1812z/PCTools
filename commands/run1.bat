@echo off
if "%1" == "h" goto begin
mshta vbscript:createobject("wscript.shell").run("%~nx0 h",0)(window.close)&&exit
:begin
C:\Users\i\AppData\LocalLow\CollapseLauncher\GameFolder\SRCN\Games\StarRail.exe