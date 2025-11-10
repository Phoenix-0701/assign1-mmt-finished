# test_client.py (PHIÊN BẢN 801 - Test chống trùng)
from multiprocessing.managers import BaseManager, DictProxy

print("--- Test Client: GỌI HÀM (Chống trùng Value) ---")

try:
    # 1. Đăng ký stub cho các hàm
    BaseManager.register('add_peer')
    BaseManager.register('remove_peer')
    # Vẫn cần DictProxy cho hàm get_peer_list
    BaseManager.register('get_peer_list', proxytype=DictProxy)

    address = ('127.0.0.1', 50001)
    authkey = b'secret'
    
    print("Đang kết nối tới Manager Server...")
    manager = BaseManager(address=address, authkey=authkey)
    manager.connect()
    print("Kết nối thành công!")

    # --- BẮT ĐẦU TEST ---

    # A. Thêm 'Alice' với info_A
    print("\n--- Test A: Thêm 'Alice' ---")
    info_A = {"ip": "1.1.1.1", "port": 9001}
    success = manager.add_peer("peer_Alice", info_A)
    print(f"... Đã gọi add_peer('peer_Alice'). Kết quả: {success}")

    # B. Thêm 'Bob' với info_B
    print("\n--- Test B: Thêm 'Bob' ---")
    info_B = {"ip": "2.2.2.2", "port": 9002}
    success = manager.add_peer("peer_Bob", info_B)
    print(f"... Đã gọi add_peer('peer_Bob'). Kết quả: {success}")

    # C. Lấy danh sách (sẽ có Alice và Bob)
    list1 = manager.get_peer_list().copy()
    print(f"List hiện tại: {list1}")

    # D. Thêm 'Charlie' với info_A (TRÙNG GIÁ TRỊ với Alice)
    print("\n--- Test D: Thêm 'Charlie' (TRÙNG VALUE) ---")
    success = manager.add_peer("peer_Charlie", info_A)
    print(f"... Đã gọi add_peer('peer_Charlie'). Kết quả: {success}") # <-- Phải là False

    # E. Lấy danh sách cuối cùng (Charlie không được thêm)
    print("\n--- Test E: Lấy danh sách cuối cùng ---")
    final_list = manager.get_peer_list().copy()
    print(f"List cuối cùng: {final_list}")

except ConnectionRefusedError:
    print("\n[LỖI] Không thể kết nối. Bạn đã chạy 'manager_server.py' chưa?")
except Exception as e:
    print(f"\n[LỖI] {e}")

print("\nClient test đã chạy xong.")