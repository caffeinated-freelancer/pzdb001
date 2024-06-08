@echo off

pushd "project\path"
call .venv\Scripts\activate
python main.py --generate-introducer-reports
call deactivate
popd
chcp 65001
explorer "file\output\path"
