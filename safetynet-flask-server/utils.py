import base64

def dec_b64(value):
    value = str(value)
    return base64.urlsafe_b64decode(value + '=' * (4 - len(value) % 4))