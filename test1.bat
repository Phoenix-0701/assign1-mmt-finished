ECHO Dang mo 6 terminal WSL...
::Peer manager
start "" wt -w 0 nt -- wsl bash -ic "cd '%WSL_PATH%' && echo Manager && python3 manager.py
::Proxy
start "" wt -w 0 nt -- wsl bash -ic "cd '%WSL_PATH%' && echo Proxy && python3 start_proxy.py"


:: Server
start "" wt -w 0 nt -- wsl bash -ic "cd '%WSL_PATH%' && echo Server1 && python3 start_chat_server.py --server-ip 127.0.0.1 --server-port 9002"
start "" wt -w 0 nt -- wsl bash -ic "cd '%WSL_PATH%' && echo Server2 && python3 start_chat_server.py --server-ip 127.0.0.1 --server-port 9003"
:: Client 1
start "" wt -w 0 nt -- wsl bash -ic "cd '%WSL_PATH%' && echo Client1 && python3 start_chat_client.py --server-ip 127.0.0.1 --server-port 9100"

:: Client 2
start "" wt -w 0 nt -- wsl bash -ic "cd '%WSL_PATH%' && echo Client2 && python3 start_chat_client.py --server-ip 127.0.0.1 --server-port 9200"

