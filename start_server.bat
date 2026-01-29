@echo off
set PATH=%CD%\ffmpeg-master-latest-win64-gpl\bin;%PATH%
python -m src.server.main
