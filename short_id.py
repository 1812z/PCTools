import hashlib
import base64


def generate_short_id(filename: str) -> str:
    '''
    生成校验id
    '''
    sha256_hash = hashlib.sha256(filename.encode()).digest()
    base64_encoded = base64.urlsafe_b64encode(sha256_hash).rstrip(b'=')
    short_id = base64_encoded.decode('utf-8')
    short_id = short_id[:16]
    return short_id
