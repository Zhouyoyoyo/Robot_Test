@echo off
setlocal

REM 切换到 bat 所在目录
cd /d %~dp0

REM 使用当前环境的 python 执行 run.py
python run.py

REM 保持窗口，方便查看日志
pause
