@echo off
ECHO Dang mo 5 terminal WSL...

for /f "delims=" %%i in ('wsl wslpath "%cd%"') do set WSL_PATH=%%i

:: Proxy
start "" wt -w 0 nt -- wsl bash -ic "cd '%WSL_PATH%' && echo Proxy && python3 start_proxy.py || echo LOI PROXY && read -n 1"

:: Server
start "" wt -w 0 nt -- wsl bash -ic "cd '%WSL_PATH%' && echo Server && python3 start_chat_server.py --server-ip 127.0.0.1 --server-port 9000"

:: Client 1
start "" wt -w 0 nt -- wsl bash -ic "cd '%WSL_PATH%' && echo Client1 && python3 start_chat_client.py --server-ip 127.0.0.1 --server-port 9001"

:: Client 2
start "" wt -w 0 nt -- wsl bash -ic "cd '%WSL_PATH%' && echo Client2 && python3 start_chat_client.py --server-ip 127.0.0.1 --server-port 9002"

:: Client 3
start "" wt -w 0 nt -- wsl bash -ic "cd '%WSL_PATH%' && echo Client3 && python3 start_chat_client.py --server-ip 127.0.0.1 --server-port 9003"
