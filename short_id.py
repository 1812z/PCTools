import hashlib
import base64

# 生成校验id
def generate_short_id(filename: str) -> str:
    sha256_hash = hashlib.sha256(filename.encode()).digest()
    base64_encoded = base64.urlsafe_b64encode(sha256_hash).rstrip(b'=')
    short_id = base64_encoded.decode('utf-8')
    short_id = short_id[:16]
    return short_id

filename = "example.txt"
short_id = generate_short_id(filename)
print(f"Short ID for '{filename}': {short_id}")
