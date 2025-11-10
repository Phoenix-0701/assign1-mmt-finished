# test_client.py (Bản 701 - Client)
from multiprocessing.managers import BaseManager, DictProxy

print("--- Test Client: GHI (Bản Triệt Để) ---")
print("--- PHIÊN BẢN 701 ---") 

try:
    # 1. Đăng ký stub, nói rõ nó trả về một DictProxy
    BaseManager.register('get_peer_list', proxytype=DictProxy)

    address = ('127.0.0.1', 50001)
    authkey = b'secret'
    
    print("Đang kết nối tới Manager Server...")
    manager = BaseManager(address=address, authkey=authkey)
    manager.connect()
    print("Kết nối thành công!")

    # 2. Lấy proxy của DICT
    shared_dict_proxy = manager.get_peer_list() 
    
    # 3. ĐỌC DỮ LIỆU (Dùng .copy())
    initial_data = shared_dict_proxy.copy()
    print(f"Trạng thái ban đầu (đọc từ server): {initial_data}")
    
    print("...Đã lấy proxy của DICT. Bắt đầu ghi.")

    # 4. GHI VÀO DICT PROXY (Dùng .update())
    key = "peer_Lucas"
    value = {"ip": "192.168.1.10", "port": 9001}
    
    shared_dict_proxy.update({key: value})
    
    print(f"Đã GHI: {key} = {value}")

    key2 = "peer_Emily"
    value2 = {"ip": "192.168.1.11", "port": 9002}
    
    shared_dict_proxy.update({key2: value2})
    
    print(f"Đã GHI: {key2} = {value2}")
    
    # 5. ĐỌC LẠI (Dùng .copy())
    final_data = shared_dict_proxy.copy()
    print(f"Trạng thái dict HIỆN TẠI: {final_data}")

except ConnectionRefusedError:
    print("\n[LỖI] Không thể kết nối. Bạn đã chạy 'manager_server.py' chưa?")
except Exception as e:
    print(f"\n[LỖI] {e}")

print("Write client đã chạy xong.")