import socket, pickle, base64, hashlib
from cryptography.fernet import Fernet
from datetime import datetime

def key(password):
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def encrypt(password, obj):
    return Fernet(key(password)).encrypt(pickle.dumps(obj))

def decrypt(password, data):
    return pickle.loads(Fernet(key(password)).decrypt(data))

SERVER_IP = "0.0.0.0"
SERVER_PORT = 9999

users = {}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))

print("🟢 Serveur UDP prêt")

while True:
    data, addr = sock.recvfrom(8192)
    pwd, payload = data.split(b"|", 1)
    pwd = pwd.decode()

    try:
        msg = decrypt(pwd, payload)
    except:
        continue

    user = users.setdefault(pwd, {
        "profile": {},
        "budget": 0.0,
        "expenses": []
    })

    if msg["action"] == "PROFILE":
        user["profile"] = msg["data"]

    elif msg["action"] == "SET_BUDGET":
        user["budget"] = msg["budget"]

    elif msg["action"] == "ADD_EXPENSE":
        exp = msg["expense"]
        exp["date"] = datetime.now().strftime("%Y-%m-%d")
        user["expenses"].append(exp)

    sock.sendto(
        pwd.encode() + b"|" + encrypt(pwd, user),
        addr
    )
