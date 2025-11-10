# manager_server.py (PHIÊN BẢN 801 - Chống trùng Value)
from multiprocessing.managers import BaseManager
from threading import Lock

# 1. Dữ liệu và Khóa
_peer_list_data = {}
_lock = Lock()

# --- 2. Các hàm API (Phần quan trọng) ---

def add_peer(peer_id, peer_info):
    """
    Thêm hoặc cập nhật một peer.
    Sẽ trả về True nếu thành công, False nếu GIÁ TRỊ bị trùng.
    """
    with _lock:
        # KIỂM TRA TRÙNG LẶP (Đây là logic mới)
        # Duyệt qua các giá trị hiện có
        for current_id, current_info in _peer_list_data.items():
            # Nếu peer_id không phải là chính nó (trường hợp update)
            # và giá trị mới đã tồn tại
            if current_id != peer_id and current_info == peer_info:
                print(f"[Manager] LỖI: {peer_info} đã tồn tại (thuộc về {current_id}).")
                return False # Báo lỗi: Giá trị đã tồn tại

        # Nếu không trùng, thì thêm/cập nhật
        print(f"[Manager] Đã thêm/cập nhật: {peer_id} -> {peer_info}")
        _peer_list_data[peer_id] = peer_info
        return True # Báo thành công

def remove_peer(peer_id):
    """Xóa một peer."""
    with _lock:
        if _peer_list_data.pop(peer_id, None):
            print(f"[Manager] Đã xóa: {peer_id}")
            return True
        return False

def get_peer_list():
    """Trả về MỘT BẢN SAO (copy) của danh sách."""
    with _lock:
        return _peer_list_data.copy() 

# --- 3. Đăng ký các hàm ---
BaseManager.register('add_peer', callable=add_peer)
BaseManager.register('remove_peer', callable=remove_peer)
BaseManager.register('get_peer_list', callable=get_peer_list) # Vẫn cần DictProxy bên client

# --- 4. Khởi chạy Server ---
address = ('127.0.0.1', 50001)
authkey = b'secret'
manager = BaseManager(address=address, authkey=authkey)

print(f"--- Server Quản lý (Chống trùng Value) ---")
print(f"Đang host các hàm: add_peer, remove_peer, get_peer_list")
print(f"Tại: {address[0]}:{address[1]}")

try:
    server = manager.get_server()
    server.serve_forever()
except KeyboardInterrupt:
    print("\nĐã tắt Manager Server.")