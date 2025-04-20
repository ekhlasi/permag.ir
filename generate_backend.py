import secrets
import base64
import random
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

IP_RANGES = {
    "UAE": [("94.200.0.0", "94.200.255.255"), ("213.42.0.0", "213.42.255.255")],
    "Bahrain": [("37.131.0.0", "37.131.255.255"), ("188.221.0.0", "188.221.255.255")],
    "Qatar": [("78.100.0.0", "78.100.255.255"), ("212.77.192.0", "212.77.223.255")]
}

def ip_to_int(ip):
    return sum(int(b) << (8 * (3 - i)) for i, b in enumerate(ip.split(".")))

def int_to_ip(n):
    return ".".join(str((n >> (8 * (3 - i))) & 0xFF) for i in range(4))

def random_ip_from_range(start, end):
    start_int = ip_to_int(start)
    end_int = ip_to_int(end)
    return int_to_ip(random.randint(start_int, end_int))

def random_country_ip(country):
    ranges = IP_RANGES[country]
    selected = random.choice(ranges)
    return random_ip_from_range(*selected)

def generate_wg_key():
    return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')

def generate_dns_list(n=7):
    return ', '.join(f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(n))

def generate_config(country):
    private_key = generate_wg_key()
    public_key = generate_wg_key()
    preshared_key = generate_wg_key()
    address = random_country_ip(country)
    dns_list = generate_dns_list()
    endpoint_ip = random_country_ip(country)
    endpoint_port = random.randint(10000, 65000)
    config = f"""[Interface]
PrivateKey = {private_key}
Address = {address}/24
DNS = 10.202.10.10, {dns_list}
MTU = 1483

[Peer]
PublicKey = {public_key}
PresharedKey = {preshared_key}
Endpoint = {endpoint_ip}:{endpoint_port}
PersistentKeepalive = 47
"""
    return config

def save_to_github(filename, content):
    GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"
    REPO = "ekhlasi/permag.ir"
    path = f"configs/{filename}"
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "message": "Add generated WireGuard config",
        "content": base64.b64encode(content.encode()).decode(),
        "branch": "main"
    }
    r = requests.put(url, headers=headers, data=json.dumps(data))
    return r.ok, r.json()

@app.route('/api/generate-config', methods=['POST'])
def api_generate_config():
    country = request.json.get('country')
    if country not in IP_RANGES:
        return jsonify(success=False, error="کشور نامعتبر است.")
    config = generate_config(country)
    filename = f"wg_{country.lower()}_{random.randint(10000,99999)}.conf"
    ok, resp = save_to_github(filename, config)
    if ok:
        raw_url = f"https://raw.githubusercontent.com/ekhlasi/permag.ir/main/configs/{filename}"
        return jsonify(success=True, config=config, download_url=raw_url)
    else:
        return jsonify(success=False, error="ذخیره در گیت‌هاب ناموفق بود.")
    
if __name__ == "__main__":
    app.run(debug=True)