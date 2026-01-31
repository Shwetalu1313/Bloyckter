import json
import os
import hashlib
from cryptography.fernet import Fernet

DATA_FILE = "data.enc"
KEY_FILE = "secret.key"

# loading key
def load_key(): 

    # if path is not exist, generate key
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()

        # open file and write in the binary format
        with open(KEY_FILE, "wb") as f:

            # create new key
            f.write(key)

    else:

        # open file and read in the binary format
        with open(KEY_FILE, "rb") as f:

            # read the key
            key.read()

    # finally return the key
    return key

# =======================================

# create a ciper object
def get_ciper():
    return Fernet(load_key())

# ========================================

# data loading
def load_data():
    # if file is not exists, return path
    if not os.path.exists(DATA_FILE):
        return {}
    
    # ciper object
    ciper = get_ciper()

    # open and read the file in binary format
    with open(DATA_FILE, "rb") as f:
        encrypted = f.read()

    # decrypted the reading in binary format
    decrypted = ciper.decrypt(encrypted)

    # decode in the json format
    return json.loads(decrypted.decode())

# ======================================

# save in encrypted data
def save_data(data):

    # ciper object
    ciper = get_ciper()

    # string to bytes
    raw = json.dump(data).encode()

    # encrypte the bytes
    encrypted = ciper.encrypt(raw)

    # open file and write
    with open (DATA_FILE, "wb") as f:
        f.write(encrypted)

