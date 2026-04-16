import hmac, hashlib, time, struct, base64, secrets

def generate_secret_totp(length = 32):
    # calculate bytes that required for key with specific length
    byte_length = (length * 5) // 8

    raw_bytes = secrets.token_bytes(byte_length)
    secret_base32 = base64.b32encode(raw_bytes).decode('utf-8')

    return secret_base32.replace('=', '')

# TOTP with RFC 6238 standart
def verify_totp(secret: str, code: str, window=1):
    # secret user key in bytes
    key = base64.b32decode(secret, casefold=True)

    # Current interval timestamp
    counter = int(time.time() // 30)

    # check current and closed time windows 
    for i in range(-window, window + 1):
        msg = struct.pack(">Q", counter + i)

        digest = hmac.new(key, msg, hashlib.sha1).digest()

        # Dynamic Truncation
        offset = digest[-1] & 0x0f
        binary = struct.unpack(">I", digest[offset:offset+4])[0] & 0x7fffffff
        otp = binary % 1000000

        if int(code) == otp:
            return True
        
    return False
