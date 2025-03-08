@echo off
set cfg_appname=Tuegist

title %cfg_appname%

set "ShortcutLocation=%__CD__:~,-1%\"

cd /d %~dp0

uv run main.py --tue

