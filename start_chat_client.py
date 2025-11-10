import json
import argparse
from daemon.response import Response
from daemon.request import Request
from urllib.parse import *
# from db.account import select_user, create_connection

# Import lớp WeApRous từ module daemon
from daemon.weaprous import WeApRous

# Đặt một cổng mặc định cho máy chủ chat, khác với các máy chủ khác
PORT = 8001 

# Khởi tạo ứng dụng WeApRous
app = WeApRous()

# -------------------------------------------------------------------
# Đây là "database" tạm thời của máy chủ tracker 
# Nó sẽ lưu danh sách các peer đang hoạt động.
#
# Cấu trúc dữ liệu:
# peer_list = {
#     "username_cu_peer_A": {"ip": "192.168.1.10", "port": 9001},
#     "username_cu_peer_B": {"ip": "192.168.1.11", "port": 9002},
# }
# -------------------------------------------------------------------
class BiMap:
    """Mô phỏng một Từ điển hai chiều (Bi-directional Map) 1:1.

    Class này đảm bảo rằng cả key (khóa) và value (giá trị) đều là duy nhất.
    Việc tra cứu, thêm, và xóa key/value đều có độ phức tạp trung bình O(1).

    Attributes:
        _key_to_value (dict): Ánh xạ xuôi (key -> value).
        _value_to_key (dict): Ánh xạ ngược (value -> key).
    """

    def __init__(self):
        """Khởi tạo hai dictionary rỗng để tra cứu hai chiều."""
        # Tra xuôi: "alice" -> ("1.1.1.1", 9000)
        self._key_to_value = {}  
        # Tra ngược: ("1.1.1.1", 9000) -> "alice"
        self._value_to_key = {}  

    def add(self, key, ip, port):
        """Thêm một cặp (key, value) mới vào map.

        Args:
            key (any): Key duy nhất (ví dụ: username).
            ip (str): Địa chỉ IP của value.
            port (int or str): Cổng của value.

        Raises:
            Exception: Nếu một trong các tham số bị thiếu (None hoặc rỗng).
            Exception: Nếu key đã tồn tại.
            Exception: Nếu value (ip, port) đã tồn tại (thuộc về key khác).
        """
        if not key or not ip or not port:
            raise Exception("Missing arguments.")
        
        value = (ip, port)

        # 1. Kiểm tra Key (O(1) - rất nhanh)
        if key in self._key_to_value:
            raise Exception(f"Key '{key}' đã tồn tại.")

        # 2. Kiểm tra Value (O(1) - rất nhanh)
        if value in self._value_to_key:
            existing_key = self._value_to_key[value]
            raise Exception(
                f"Value '{value}' đã tồn tại (thuộc về '{existing_key}')."
            )
        
        # 3. An toàn để thêm vào cả 2 dict
        self._key_to_value[key] = value
        self._value_to_key[value] = key
        print(f"Added: {key} <-> {value}")

    def remove_by_key(self, key):
        """Xóa một cặp dữ liệu dựa trên key.

        Args:
            key (any): Key của cặp cần xóa.
        """
        # Xóa bằng key
        # Dùng .pop(key, None) để tránh lỗi nếu key không có
        value = self._key_to_value.pop(key, None)
        
        if value:
            # Nếu xóa xuôi thành công, xóa luôn ngược
            self._value_to_key.pop(value)
            print(f"Removed: {key} <-> {value}")
        else:
            print(f"Warning: Key '{key}' not found.")

    def remove_by_value(self, ip, port):
        """(Tùy chọn) Xóa một cặp dữ liệu dựa trên value (ip, port).

        Args:
            ip (str): Địa chỉ IP của value cần xóa.
            port (int or str): Cổng của value cần xóa.
        """
        value = (ip, port)
        key = self._value_to_key.pop(value, None)
        
        if key:
            # Nếu xóa ngược thành công, xóa luôn xuôi
            self._key_to_value.pop(key)
            print(f"Removed: {key} <-> {value}")
        else:
            print(f"Warning: Value '{value}' not found.")

    def get_value(self, key):
        """Lấy value (ip, port) dựa trên key.

        Args:
            key (any): Key cần tra cứu.

        Returns:
            tuple or None: Trả về (ip, port) nếu tìm thấy, 
                           hoặc None nếu không.
        """
        return self._key_to_value.get(key)

    def get_key(self, ip, port):
        """Lấy key (username) dựa trên value (ip, port).

        Args:
            ip (str): Địa chỉ IP của value cần tra cứu.
            port (int or str): Cổng của value cần tra cứu.

        Returns:
            any or None: Trả về key nếu tìm thấy, 
                         hoặc None nếu không.
        """
        return self._value_to_key.get((ip, port))
    
    def get_all(self):
        """
        Trả về tất cả các peers đã kết nối
        """
        return self._key_to_value


connected_peer = BiMap()
chat_messages = {} 

@app.route('/active-peers', methods=['GET'])
def active_peers_page(req):
    req.path = 'active-peers.html'
    resp = Response(req)
    return resp.build_response(req)

@app.route('/js/active-peers.js', methods=['GET'])
def serve_active_peers_js(req):
    try:
        req.path = '/js/active-peers.js'
        resp = Response()
        resp.headers = {"Content-Type": "application/javascript"}
        return resp.build_response(req)
    except:
        return Response().build_not_found({"error": "JS file not found"})

@app.route('/get-tracker', methods=['GET'])
def get_tracker(req):
    import os
    if not os.path.exists("tracker.json"):
        return Response().build_notfound({"error": "tracker not found"})
    with open("tracker.json") as f:
        data = json.load(f)
        print(data)
        print(json.dumps(data))
    return  Response().build_success(data)

@app.route("/add-list", methods=["POST"])
def add_peer(req):
    try:
        body = req.body or ""
        content_type = req.headers.get("Content-Type", "")

        if "application/json" in content_type:
            data = json.loads(body)
        else:
            data = parse_qs(body)

        username = data.get("username")
        ip = data.get("ip")
        port = data.get("port")

        # Nếu parse_qs: lấy phần tử đầu tiên trong list
        username = username[0] if isinstance(username, list) else username
        ip = ip[0] if isinstance(ip, list) else ip
        port = port[0] if isinstance(port, list) else port

        if not username or not ip or not port:
            return Response().build_bad_request({
                "message": "Missing username/ip/port"
            })

        connected_peer.add(key=username, ip=ip,port=port)

        print(f"[Peer] {username} connected: {connected_peer.get_value(username)}")
        print("All connected peers:", connected_peer.get_all())

        return Response().build_success({
            "message": "Added successfully",
            "peer": connected_peer.get_value(username)
        })

    except json.JSONDecodeError:
        return Response().build_bad_request({
            "message": "Invalid JSON format"
        })
    except Exception as e:
        print("Unexpected error:", e)
        return Response().build_internal_error({
            "message": str(e)
        })


@app.route("/get-connected-peer", methods=["GET"])
def get_connected_peer(req):
    try:
        return Response().build_success({
            "message": "Connected peer list returned",
            "peer_list": connected_peer.get_all()
        })
    except Exception as e:
        print("Unexpected error:", e)
        return Response().build_internal_error({
            "message": str(e)
        })


@app.route("/view-my-channels", methods=["GET"])
def view_channels(req):
    try:
        req.path = "/view-my-channels.html"
        resp = Response()
        return resp.build_response(req)
    except Exception as e:
        print("Unexpected error:", e)
        return Response().build_internal_error({
            "message": str(e)
    })

@app.route("/send-message", methods=["POST"])
def send_message(req):
    data = json.loads(req.body)
    receiver = data['receiver']
    message = data['message']
    time_stamp = data['time_stamp']
    chat_messages.setdefault(receiver, []).append({'sender': "Me", 'message': message,'time_stamp': time_stamp})
    print(f"[Peer]: Message sent to {receiver} at {time_stamp}. The content is {message}")
    return Response().build_success({'status': 'ok', 'message': f"Message sent to {receiver} at {time_stamp}"})

# @app.route("/receive-message", methods=["POST", "OPTIONS"])
# def send_message(req):
#     data = json.loads(req.body)
#     receiver = data['receiver']
#     message = data['message']
#     time_stamp = data['time_stamp']
#     chat_messages.setdefault(receiver, []).append({'sender': "Me", 'message': message,'time_stamp': time_stamp})
#     print(f"[Peer]: Message sent to {receiver} at {time_stamp}. The content is [{message}]")
#     return Response().build_success({'status': 'ok', 'message': f"Message sent to {receiver} at {time_stamp}"})

@app.route("/receive-message", methods=["POST", "OPTIONS"])
def receive_message(req):
    try:
        cors_headers = (
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        )
        if req.method == "OPTIONS":
            return (
            "HTTP/1.1 204 No Content\r\n"
            f"{cors_headers}\r\n"
            ).encode("utf-8")
        data = json.loads(req.body)

        sender = data['sender']
        message = data['message']
        time_stamp = data['time_stamp']

        chat_messages.setdefault(sender, []).append({'sender': sender, 'message': message,'time_stamp': time_stamp})
        print(f"[Peer]: Received message from {sender} at {time_stamp}. The content is [{message}]")
        
        # return Response().build_success({'status': 'ok', 'message': f"Received message from {sender} at {time_stamp}"})
        body = json.dumps({"status": "ok"})
        content_length = len (body)
        return (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {content_length}\r\n"
            f"{cors_headers}\r\n"
            f"{body}"
        ).encode("utf-8")
    except Exception as e:
        return Response().build_internal_error({'messages': str(e)})

@app.route("/get-messages", methods=["GET"])
def get_messages(req):
    peer = req.query_params.get('peer', None)
    print(f"[Peer] Get messages with {peer}")
    if not peer:
        return Response().build_bad_request({"message": "Missing peer"})
    messages = chat_messages.get(peer, [])
    return Response().build_success({'messages': messages})


@app.route("/chat.js", methods=["GET"])
def chat_style(req):
    try :
        resp = Response()
        return resp.build_response(req)
    except Exception as e:
        print("Unexpected error:", e)
        return Response().build_internal_error({"message": str(e)})
    
from urllib.parse import urlparse, parse_qs

@app.route("/chat", methods=["GET"])
def chat_page(req):
    """
    Route /chat: Hiển thị trang chat giữa hai peer hoặc trả dữ liệu cần thiết
    Query parameters:
        - user: username của người hiện tại
        - peer: username của peer muốn chat
        - ip: IP của peer
        - port: Port của peer
    """
    if not hasattr(req, "query_params") or req.query_params is None:
        req.query_params = {}
        parsed_url = urlparse(req.path)
        req.query_params = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}

    
    peer = req.query_params.get("peer")
    ip = req.query_params.get("ip")
    port = req.query_params.get("port")

    
    if not all([peer, ip, port]):
        return Response().build_bad_request({
            "message": "Missing query parameters. Required: peer, ip, port"
        })

    
    print(f"[Peer] Đang chat với {peer} tại {ip}:{port}")

    
    try:
        req.path = "/chat.html"  
        resp = Response(req)
        return resp.build_response(req)
    except Exception as e:
        print("Unexpected error:", e)
        return Response().build_internal_error({"message": str(e)})







@app.route("/.well-known/appspecific/com.chrome.devtools.json", methods=["GET"])
def dummy_chrome_devtools(req):
    resp = Response()
    resp.headers.update({"Content-Type": "application/json"})
    return resp.build_success({})


# --- Giai đoạn 1: Client-Server (Tracker) ---
#

# @app.route("/login", methods=["POST"])
# def login(req):
#     from urllib.parse import parse_qs
#     parsed = parse_qs(req.body, keep_blank_values=True)

#     username = parsed.get("username", [""])[0]
#     password = parsed.get("password", [""])[0]

#     conn = create_connection("db/account.db")
#     auth = select_user(conn, username)
#     resp = Response()
#     print(f"[Server] Login attempt: {username}")
#     if auth:
#         if  password == auth[1]:
#             # build login-success response (sets cookie + returns index)
#             resp.cookies.clear()
#             resp.cookies["auth"] = "true; Path=/"
#             resp.cookies["username"] = username
#             # Ensure request points to index for building content
#             req.path = "/index.html"
#             req.method = "GET"
#             print(f"[Tracker] Login success: {username}")
#             return resp.build_response(req)
        
#     print(f"[Tracker] Login failed: {username}")
#     return resp.build_unauthorized()

# @app.route('/login', methods=['GET'])
# def login_form(req):
#     """
#     Trả form đăng nhập (username, password)
#     """
#     print(f"[ChatServer] Nhận yêu cầu /submit-info...")
    
#     try:
#         req.path = "/login.html"
#         return Response().build_response(req)
#     except Exception as e:
#         print(f"[ChatServer] Lỗi không xác định: {e}")
#         return {"status": "error", "message": str(e)}

# @app.route('/submit-info',methods=['GET'])
# def submit_form(req):
#     """
#     Trả form một peer mới tham gia và đăng ký thông tin (IP, port)
#     """
#     try:
#         req.path = "/submit.html"
#         return Response().build_response(req)
#     except Exception as e:
#         print(f"[ChatServer] Lỗi không xác định: {e}")
#         return {"status": "error", "message": str(e)}

# @app.route('/get-list', methods=['GET'])
# def get_list(req):
#     """
#     API để một peer yêu cầu danh sách tất cả các peer 
#     khác đang hoạt động từ tracker.
#     [cite: 247, 263]
#     """
#     print(f"[ChatServer] Nhận yêu cầu /get-list. Đang trả về {len(peer_list)} peers.")
    
#     return {"status": "success", "peers": peer_list}

# @app.route('/logout', methods=['POST'])
# def logout(req):
#     """
#     API để một peer thông báo rằng mình đã thoát (quit).
#     Server sẽ xóa peer này khỏi peer_list.
#     """
#     print(f"[ChatServer] Nhận yêu cầu /logout...")
    
#     try:
#         body=req.body
#         # Tệp httpadapter.py đã chuyển body thành chuỗi
#         data = json.loads(body)
#         peer_id = data.get("username")
        
#         # Kiểm tra xem peer có trong danh sách không
#         if peer_id in peer_list:
#             del peer_list[peer_id] # Xóa peer khỏi danh sách
#             print(f"[ChatServer] Peer đã thoát: {peer_id}. Danh sách còn lại {len(peer_list)} peers.")
#             return {"status": "logged_out", "peer_id": peer_id}
#         else:
#             print(f"[ChatServer] Peer {peer_id} yêu cầu logout nhưng không có trong danh sách.")
#             return {"status": "error", "message": "Peer not found"}
            
#     except json.JSONDecodeError:
#         print("[ChatServer] Lỗi: Body /logout không phải là JSON hợp lệ")
#         return {"status": "error", "message": "Invalid JSON body"}
#     except Exception as e:
#         print(f"[ChatServer] Lỗi /logout không xác định: {e}")
#         return {"status": "error", "message": str(e)}

# --- Khối khởi chạy máy chủ ---
if __name__ == "__main__":
    """
    Phần này tương tự như tệp start_sampleapp.py,
    dùng để parse tham số và khởi chạy máy chủ WeApRous.
   
    """

    parser = argparse.ArgumentParser(
        prog='ChatServer', 
        description='Start the Hybrid Chat Server (Tracker)', 
        epilog='Chat daemon for WeApRous application'
    )
    parser.add_argument('--server-ip', 
        type=str, 
        default='0.0.0.0', 
        help='IP address to bind the server. Default is 0.0.0.0'
    )
    parser.add_argument(
        '--server-port', 
        type=int, 
        default=PORT, 
        help=f'Port number to bind the server. Default is {PORT}.'
    )
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    print(f"[ChatServer] Đang khởi chạy máy chủ tracker tại http://{ip}:{port}")
    app.prepare_address(ip, port)
    app.run()