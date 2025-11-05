# chat_client.py (Da cap nhat tinh nang /send den kenh cu the)
import socket
import threading
import argparse
import http.client
import json
import time
import os

class ChatClient:
    def __init__(self, username, client_port):
        self.username = username
        self.client_port = client_port
        
        # --- THAY DOI ---
        # self.peer_list se luu tru du lieu kieu long (nested)
        # Format: { "127.0.0.1:8001": {"Bob": {...}, "Carol": {...}},
        #           "127.0.0.1:8002": {"David": {...}} }
        self.peer_list = {} 
        self.channels = {}
        
        self.channel_file = f"{username}_channels.json" 
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.client_ip = s.getsockname()[0]
            s.close()
        except Exception:
            self.client_ip = '127.0.0.1'
            
        self.server_socket = None
        self.running = True

    # --- Cac ham quan ly kenh (load/save/register/logout) ---
    # (Giu nguyen logic cac ham nay, khong can sua)
    def load_channels(self):
        if os.path.exists(self.channel_file):
            try:
                with open(self.channel_file, 'r') as f:
                    self.channels = json.load(f)
                    print(f"[Client] Da tai {len(self.channels)} kenh tu {self.channel_file}")
            except Exception as e:
                print(f"[Client] Loi khi tai file channel: {e}")
        else:
            print("[Client] Khong tim thay file channel, bat dau voi danh sach rong.")

    def save_channels(self):
        try:
            with open(self.channel_file, 'w') as f:
                json.dump(self.channels, f, indent=4)
        except Exception as e:
            print(f"[Client] Loi khi luu file channel: {e}")

    def register_with_all_trackers(self):
        print("[Client] Dang ky voi tat ca cac kenh...")
        if not self.channels:
            print("[Client] Ban chua tham gia kenh nao. Dung lenh: /join <ip:port>")
            return
        payload = {"username": self.username, "ip": self.client_ip, "port": self.client_port}
        headers = {"Content-type": "application/json"}
        for location, info in self.channels.items():
            try:
                conn = http.client.HTTPConnection(info['ip'], info['port'], timeout=3)
                conn.request("POST", "/submit-info", json.dumps(payload).encode('utf-8'), headers)
                response = conn.getresponse()
                if response.status == 200:
                    print(f"[Client] Dang ky thanh cong voi kenh: {location}")
                else:
                    print(f"[Client] Loi dang ky voi {location}: {response.status} {response.reason}")
                conn.close()
            except Exception as e:
                print(f"[Client] Khong the ket noi duoc kenh {location}: {e}")

    def logout_from_all_trackers(self):
        print(f"[Client] Dang thong bao thoat cho tat ca cac kenh...")
        payload = {"username": self.username}
        headers = {"Content-type": "application/json"}
        for location, info in self.channels.items():
            try:
                conn = http.client.HTTPConnection(info['ip'], info['port'], timeout=3)
                conn.request("POST", "/logout", json.dumps(payload).encode('utf-8'), headers)
                response = conn.getresponse()
                if response.status == 200:
                    print(f"[Client] Da logout khoi kenh {location}")
                else:
                    print(f"[Client] Loi khi logout khoi {location}: {response.status} {response.reason}")
                conn.close()
            except Exception as e:
                print(f"[Client] Khong the ket noi tracker {location} de logout: {e}")

    #
    # --- HAM GET_PEER_LIST (DA CAP NHAT) ---
    #
    def get_peer_list(self):
        """
        Lay danh sach peer tu TAT CA cac kenh va luu tru theo cau truc long (nested)
        """
        print("[Client] Dang cap nhat danh sach peer tu tat ca cac kenh...")
        all_peers_by_channel = {}
        for location, info in self.channels.items():
            try:
                conn = http.client.HTTPConnection(info['ip'], info['port'], timeout=3)
                conn.request("GET", "/get-list")
                response = conn.getresponse()
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    peers_in_channel = data.get("peers", {})
                    # Xoa chinh minh khoi danh sach con
                    if self.username in peers_in_channel:
                        del peers_in_channel[self.username]
                    
                    # Luu danh sach peer cua kenh nay
                    all_peers_by_channel[location] = peers_in_channel
                    print(f"[Client] Kenh {location} co {len(peers_in_channel)} peers (khac).")
                conn.close()
            except Exception as e:
                print(f"[Client] Loi khi lay danh sach peer tu {location}: {e}")
        
        self.peer_list = all_peers_by_channel # Luu lai cau truc long
        print(f"[Client] Da cap nhat. Tong so {len(self.channels)} kenh.")

    # --- Ham P2P (Khong thay doi) ---
    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.client_port))
        self.server_socket.listen(5)
        print(f"[Client] Dang lang nghe P2P tren port {self.client_port}")
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_peer_connection, args=(conn, addr)).start()
            except socket.error:
                if self.running: print("[Client] Loi server P2P")
                break
        print("[Client] Da dong server P2P.")

    def handle_peer_connection(self, conn, addr):
        try:
            data = conn.recv(1024).decode('utf-8')
            if data:
                print(f"\r[Tin nhan P2P tu {addr[0]}]: {data}\n[Ban]: ", end="", flush=True)
        except Exception as e:
            print(f"\r[Client] Loi khi nhan tin nhan P2P: {e}")
        finally:
            conn.close()

    #
    # --- HAM BROADCAST (DA CAP NHAT) ---
    #
    def broadcast_message(self, message):
        """
        Gui tin nhan Broadcast den tat ca peer (tu tat ca cac kenh)
        """
        print("[Client] Dang broadcast...")
        self.get_peer_list() # Ham nay da duoc cap nhat
        
        full_message = f"[{self.username} - BROADCAST]: {message}"
        
        # Can tao mot danh sach "phang" de tranh gui trung lap
        all_peers_flat = {}
        for location, peers_in_channel in self.peer_list.items():
            all_peers_flat.update(peers_in_channel)

        if not all_peers_flat:
            print("[Client] Khong co peer nao de broadcast.")
            return

        print(f"[Client] Se gui broadcast den {len(all_peers_flat)} peers...")
        for peer_id, info in all_peers_flat.items():
            peer_ip = info.get("ip")
            peer_port = int(info.get("port"))
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((peer_ip, peer_port))
                peer_socket.sendall(full_message.encode('utf-8'))
                peer_socket.close()
            except Exception as e:
                print(f"[Client] Khong the gui broadcast den {peer_id} ({peer_ip}:{peer_port}): {e}")

    #
    # --- HAM SEND DIRECT (DA CAP NHAT) ---
    #
    def send_direct_message(self, target_username, message):
        """
        Gui tin nhan rieng den mot peer cu the (P2P)
        """
        print(f"[Client] Dang gui tin nhan rieng cho {target_username}...")
        self.get_peer_list() # Cap nhat danh ba

        target_info = None
        # Tim kiem peer do trong tat ca cac kenh
        for location, peers_in_channel in self.peer_list.items():
            if target_username in peers_in_channel:
                target_info = peers_in_channel[target_username]
                break # Tim thay

        if not target_info:
            print(f"[Client] Loi: Khong tim thay nguoi dung '{target_username}' trong bat ky kenh nao.")
            return
        
        full_message = f"[{self.username} - RIENG]: {message}"
        peer_ip = target_info.get("ip")
        peer_port = int(target_info.get("port"))
        
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_ip, peer_port))
            peer_socket.sendall(full_message.encode('utf-8'))
            peer_socket.close()
            print(f"[Client] Da gui tin nhan rieng cho {target_username}.")
        except Exception as e:
            print(f"[Client] Khong the gui den {target_username} ({peer_ip}:{peer_port}): {e}")

    #
    # --- HAM MOI: GUI DEN KENH CU THE ---
    #
    def send_channel_message(self, channel_location, message):
        """
        Gui tin nhan den tat ca peer trong mot kenh cu the.
        """
        # Kiem tra xem co trong danh sach kenh da tham gia khong
        if channel_location not in self.channels:
            print(f"[Client] Loi: Ban chua tham gia kenh {channel_location}. Dung /join de tham gia.")
            return

        print(f"[Client] Dang gui tin nhan den kenh {channel_location}...")
        self.get_peer_list() # Cap nhat danh ba
        
        # Lay danh sach peer CHU RIENG kenh do
        peers_in_this_channel = self.peer_list.get(channel_location)
        
        if not peers_in_this_channel:
            print(f"[Client] Khong co peer nao trong kenh {channel_location} (ngoai ban).")
            return

        full_message = f"[{self.username} @ {channel_location}]: {message}"
        
        print(f"[Client] Se gui den {len(peers_in_this_channel)} peers trong kenh {channel_location}...")
        for peer_id, info in peers_in_this_channel.items():
            peer_ip = info.get("ip")
            peer_port = int(info.get("port"))
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((peer_ip, peer_port))
                peer_socket.sendall(full_message.encode('utf-8'))
                peer_socket.close()
            except Exception as e:
                print(f"[Client] Khong the gui (kenh) den {peer_id} ({peer_ip}:{peer_port}): {e}")

    #
    # --- HAM START (DA CAP NHAT) ---
    #
    def start(self):
        """
        Khoi chay toan bo client
        """
        self.load_channels() 
        self.register_with_all_trackers()
        
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()
        
        try:
            while True:
                msg = input("[Ban]: ")
                
                if msg.lower() == '/quit':
                    break
                
                elif msg.lower() == '/list_channels':
                    print("[Client] Cac kenh da tham gia:")
                    if not self.channels:
                        print(" (Chua tham gia kenh nao)")
                    for location in self.channels.keys():
                        print(f"- {location}")
                    continue
                
                elif msg.startswith('/join '):
                    try:
                        _, location = msg.split(' ', 1)
                        ip, port_str = location.split(':', 1)
                        port = int(port_str)
                        self.channels[location] = {"ip": ip, "port": port}
                        self.save_channels()
                        self.register_with_all_trackers()
                        print(f"[Client] Da tham gia va luu kenh: {location}")
                    except Exception as e:
                        print(f"[Client] Loi cu phap. Su dung: /join <ip:port>. Loi: {e}")
                    continue

                elif msg.startswith('/leave '):
                    try:
                        _, location = msg.split(' ', 1)
                        if location in self.channels:
                            # TODO: Can goi logout cho rieng channel nay
                            del self.channels[location]
                            self.save_channels()
                            print(f"[Client] Da roi kenh {location}. (Hay logout khoi kenh do thu cong neu can)")
                        else:
                            print(f"[Client] Ban chua tham gia kenh {location}")
                    except Exception as e:
                        print(f"[Client] Loi cu phap. Su dung: /leave <ip:port>. Loi: {e}")
                    continue

                elif msg.lower() == '/list':
                    self.get_peer_list()
                    # In ra danh sach peer da duoc phan loai
                    print(json.dumps(self.peer_list, indent=2))
                    continue

                elif msg.startswith('/msg '):
                    try:
                        _, target_username, message = msg.split(' ', 2)
                        self.send_direct_message(target_username, message)
                    except ValueError:
                        print("[Client] Loi: Cu phap sai. Su dung: /msg <username> <message>")
                    continue
                
                # --- LENH MOI ---
                elif msg.startswith('/broadcast '):
                    try:
                        _, message = msg.split(' ', 1)
                        self.broadcast_message(message)
                    except ValueError:
                        print("[Client] Loi cu phap. Su dung: /broadcast <message>")
                    continue

                # --- LENH MOI ---
                elif msg.startswith('/send '):
                    try:
                        # Cu phap: /send 127.0.0.1:8001 Day la tin nhan
                        _, location, message = msg.split(' ', 2)
                        self.send_channel_message(location, message)
                    except Exception as e:
                        print(f"[Client] Loi cu phap. Su dung: /send <ip:port> <message>. Loi: {e}")
                    continue
                
                # Neu khong phai lenh nao ca
                else:
                    if msg.startswith('/'):
                        print(f"[Client] Loi: Khong ro lenh '{msg}'.")
                    else:
                        print("[Client] Loi: Tin nhan phai bat dau bang mot lenh.")
                    print("Cac lenh hop le:")
                    print("  /send <ip:port> <message>   - Gui tin den KÊNH cu the")
                    print("  /broadcast <message>      - Gui tin den TAT CA cac kenh")
                    print("  /msg <username> <message>   - Gui tin nhan RIÊNG")
                    print("  /list                     - Xem danh sach peer (theo kenh)")
                    print("  /list_channels            - Xem cac kenh da tham gia")
                    print("  /join <ip:port>           - Tham gia mot kenh moi")
                    print("  /leave <ip:port>          - Roi mot kenh")
                    print("  /quit                     - Thoat")

        except KeyboardInterrupt:
            print("\n[Client] Dang thoat...")
        finally:
            self.running = False
            self.logout_from_all_trackers() 
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.client_ip, self.client_port))
                s.close()
            except:
                pass 
            server_thread.join(1.0)
            print("[Client] Da thoat hoan toan.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='P2P Chat Client (Multi-Channel)')
    parser.add_argument('--username', required=True, help='Ten cua ban (bat buoc)')
    parser.add_argument('--port', type=int, required=True, help='Port P2P de ban lang nghe (bat buoc)')
    
    args = parser.parse_args()
    
    client = ChatClient(args.username, args.port)
    client.start()