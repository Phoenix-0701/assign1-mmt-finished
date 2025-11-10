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

# --- Test ---
# Đưa code test vào block __name__ == "__main__" là chuẩn PEP 8
# Nó cho phép file này được import như một module mà không tự chạy test
if __name__ == "__main__":
    
    print("\n--- Testing BiMap (Bản Nhanh, có Docstrings) ---")
    bimap = BiMap()
    bimap.add("alice", "1.1.1.1", 9000)
    bimap.add("bob", "2.2.2.2", 9001)

    # Test trùng value
    try:
        bimap.add("charlie", "1.1.1.1", 9000)
    except Exception as e:
        print(f"LỖI (đúng): {e}")

    # Test tra cứu
    print(f"Ai là 'alice'? -> {bimap.get_value('alice')}")
    print(f"Ai có ('2.2.2.2', 9001)? -> {bimap.get_key('2.2.2.2', 9001)}")

    # Test xóa
    bimap.remove_by_key("alice")
    print(f"List xuôi: {bimap._key_to_value}")
    print(f"List ngược: {bimap._value_to_key}")