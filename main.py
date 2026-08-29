import requests
import os
import hashlib
import base64
import uuid
import time
import json
import secrets
import zipfile
import io
import threading
import re
import sqlite3
import random
import string
import ipaddress
from datetime import datetime, timezone
from flask import Flask, jsonify, request, session as flask_session, g, send_file

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

GAME_DATA_ZIP_URL = "https://raw.githubusercontent.com/Alphamageddon/Animal-Company-Copy-Tutorial/refs/heads/main/game-data/Mining%20Update.zip"
META_APP_TOKEN = "OC|9014197565357495|14d90662e4f2cfdc4878a6ca7937567e"
EXPECTED_PACKAGE = "com.Sunday.Taggers"
SECRET_KEY = "hgdfsdjhcgshdgfcsdhjghjgsdfjhsd"

_session_store = {}
_session_store_lock = threading.Lock()
_user_active_sid = {}
MAX_SESSION_LIFETIME = 2 * 3600
TOKEN_TTL = 3600

_used_nonces = {}
_used_nonces_lock = threading.Lock()
_NONCE_TTL = 300

_rate_limit_store = {}
_rate_limit_lock = threading.Lock()

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pp_userdata.db')

def _is_rate_limited(key, max_requests, window_seconds):
    now = time.time()
    with _rate_limit_lock:
        timestamps = _rate_limit_store.get(key, [])
        timestamps = [t for t in timestamps if now - t < window_seconds]
        if len(timestamps) >= max_requests:
            _rate_limit_store[key] = timestamps
            return True
        timestamps.append(now)
        _rate_limit_store[key] = timestamps
        return False

def _rate_limit_response():
    return jsonify({"error": "rate limit exceeded, slow down"}), 429

BANNED_USERNAMES = {"ChubbyonAC", "Djbone", "Dracula12345", "Edgarrr_vr_4real", "GioP.vr", "JensonR31", "KTDsmith2015", "Lendy123", "Owner.9", "Pump.2HP", "Unknown8229", "Wooty2.820", "YUGUZAAA", "billy.4536.12", "r1ftvr1", "r1ftvrrrr", "scoooop", "thatonecatonvr", "therealpalcola.2"}
BANNED_OCULUS_IDS = {"fc84009a-0d4a-4e01-a2cb-723291a84a13", "0cd81d68-9cd2-471f-af0e-4a8cf671fc61", "be08a848-8400-434b-929e-2a9949e48337", "bfb682cc-341f-456d-9fd5-5da3e22582fe", "e57b74c3-ca40-41be-b41d-64cfc312fad2", "56b71840-4517-4a78-bde2-90ec21a1a87d, a27c22fe-dede-4021-be49-0024b6cf55b8"}
BAN_MESSAGE = "<size=15><color=red>join discord.gg/2mPK3kJc7b to appeal your ban</color></size>"

WHITELIST_ENABLED = False
WHITELISTED_USERNAMES = {"EvanBlokEnder", "Dagger.480855"}
WHITELIST_MESSAGE = {"message": "<size=15><color=red>Game has shut down forer</color></size>"}

MOD_USER = "EvanBlokEnder", "Rainn_67"

_game_data_cache = {}

WEBHOOK_LOGINS = "https://discord.com/api/webhooks/1500090236754202684/5pbdVOl59ytQQg0y6c-RDOnvfR0D88CDHWpWnnjVn-bwqoHam4NdAzIBkRoc7vJMfkrl"
WEBHOOK_BANS   = "https://discord.com/api/webhooks/1500090380656312381/bpH0c9R6VifLB8GrwFMswSPaN9Jj8j0ncb_OFRomaCRXRZblIReN45KCRJQYhxxiaE_B"
WEBHOOK_ERRORS = "https://discord.com/api/webhooks/1500090524877459617/Cvj9a3QVt40X-GZQgyj_Cv4gkQ3o1KC6N4g6vLBKVk-x5wVmNbcLCjfT_ZJWWIIftoCc"

def _send_webhook(url, message):
    def _send():
        try:
            requests.post(url, json={"content": message}, timeout=5)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()

def log_login(message):
    _send_webhook(WEBHOOK_LOGINS, message)

def log_ban(message):
    _send_webhook(WEBHOOK_BANS, message)

def log_error(message):
    _send_webhook(WEBHOOK_ERRORS, message)

def server_log(msg):
    print(msg)
    try:
        with open('server.log', 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except Exception:
        pass

def _init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            ip TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            custom_id TEXT NOT NULL,
            create_time REAL NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS banned_ips (
            ip TEXT PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

_init_db()

def _get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)

def _gen_custom_id():
    return ''.join(random.choices(string.digits, k=17))

def _gen_username():
    return 'pp+' + ''.join(random.choices(string.ascii_uppercase, k=6))

def _db_get_user(ip):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM banned_ips WHERE ip = ?', (ip,))
    if cur.fetchone():
        conn.close()
        return None, True
    cur.execute('SELECT username, custom_id FROM users WHERE ip = ?', (ip,))
    result = cur.fetchone()
    session_username = flask_session.get('username')
    username = session_username or None
    if username:
        custom_id = result[1] if result else _gen_custom_id()
        if not result:
            cur.execute('INSERT INTO users (ip, username, custom_id, create_time) VALUES (?, ?, ?, ?)', (ip, username, custom_id, time.time()))
            conn.commit()
        else:
            banned = _load_banned_users_file()
            if str(username).strip().lower() in banned:
                conn.close()
                return None, True
    else:
        if result:
            username, custom_id = result
            banned = _load_banned_users_file()
            if str(username).strip().lower() in banned:
                conn.close()
                return None, True
        else:
            username = '0x11' if ip == '127.0.0.1' else _gen_username()
            custom_id = _gen_custom_id()
            cur.execute('INSERT INTO users (ip, username, custom_id, create_time) VALUES (?, ?, ?, ?)', (ip, username, custom_id, time.time()))
            conn.commit()
    conn.close()
    return {'username': username, 'custom_id': custom_id}, False

def _load_banned_users_file():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'banned users.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(str(u).strip().lower() for u in data if u)
            if isinstance(data, dict):
                for k in ('banned users', 'banned'):
                    if k in data and isinstance(data[k], list):
                        return set(str(u).strip().lower() for u in data[k] if u)
        return set()
    except Exception:
        return set()

def _save_banned_users_file(users):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'banned users.json')
    try:
        users_list = sorted(set(str(u).strip().lower() for u in users if u))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(users_list, indent=2, ensure_ascii=False))
        return True
    except Exception:
        return False

def get_banned_users():
    return _load_banned_users_file()

def save_banned_users(users):
    return _save_banned_users_file(users)

def _load_mod_users():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mod users.json')
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
    except Exception:
        pass
    return set()

def _load_dev_users():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'devs.json')
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
    except Exception:
        pass
    return set()

def get_mod_users():
    return _load_mod_users()

def get_dev_users():
    return _load_dev_users()

def _load_banned_ips():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'banned_ips.json')
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
            if isinstance(data, dict):
                for k in ('banned_ips', 'ips', 'banned'):
                    if k in data and isinstance(data[k], list):
                        return set(data[k])
        return set()
    except Exception:
        return set()

def _save_banned_ips(ips):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'banned_ips.json')
    try:
        ips_list = sorted(list(set(str(ip).strip() for ip in ips if ip)))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(ips_list, separators=(',', ':'), indent=None))
        return True
    except Exception:
        return False

def get_banned_ips():
    return _load_banned_ips()

def ban_ip(ip_address):
    if not ip_address:
        return False
    ip_address = str(ip_address).strip()
    banned_ips = _load_banned_ips()
    banned_ips.add(ip_address)
    success = _save_banned_ips(banned_ips)
    if success:
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute('INSERT OR IGNORE INTO banned_ips (ip) VALUES (?)', (ip_address,))
            conn.commit()
            conn.close()
        except Exception:
            pass
    return success

def unban_ip(ip_address):
    if not ip_address:
        return False
    ip_address = str(ip_address).strip()
    banned_ips = _load_banned_ips()
    if ip_address in banned_ips:
        banned_ips.discard(ip_address)
        success = _save_banned_ips(banned_ips)
        if success:
            try:
                conn = sqlite3.connect(DB_FILE)
                cur = conn.cursor()
                cur.execute('DELETE FROM banned_ips WHERE ip = ?', (ip_address,))
                conn.commit()
                conn.close()
            except Exception:
                pass
        return success
    return True

def is_ip_banned(ip_address):
    if not ip_address:
        return False
    ip_address = str(ip_address).strip()
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM banned_ips WHERE ip = ?', (ip_address,))
        result = cur.fetchone()
        conn.close()
        if result:
            return True
    except Exception:
        pass
    return ip_address in get_banned_ips()

def _get_avatar_file_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pp_avatar.json')

def _load_avatars():
    path = _get_avatar_file_path()
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        return {}
    except Exception:
        return {}

def _save_avatars(avatars):
    path = _get_avatar_file_path()
    try:
        if not isinstance(avatars, dict):
            avatars = {}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(avatars, f, indent=2)
        return True
    except Exception:
        return False

def get_user_avatar(username):
    avatars = _load_avatars()
    return avatars.get(username)

def get_econ_data(collection_name):
    """Get econ data from the game data cache"""
    data = get_game_data(collection_name)
    return data if data else []

def save_user_avatar(username, avatar_data):
    avatars = _load_avatars()
    if not isinstance(avatars, dict):
        avatars = {}
    avatars[username] = avatar_data
    return _save_avatars(avatars)

def _get_items_file_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pp_items.json')

def _load_items():
    path = _get_items_file_path()
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

def _save_items(items):
    path = _get_items_file_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2)
        return True
    except Exception:
        return False


    # Add this helper function near the top of your file after the imports
    def get_db():
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'storage.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        # Create storage table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS storage (
                user_id TEXT,
                collection TEXT,
                key TEXT,
                value TEXT,
                version TEXT,
                permission_read INTEGER,
                permission_write INTEGER,
                create_time TEXT,
                update_time TEXT,
                PRIMARY KEY (user_id, collection, key)
            )
        ''')
        conn.commit()
        return conn
        
def get_user_items(username, collection='user_inventory', key='avatar'):
    items = _load_items()
    user_data = items.get(username, {})
    if isinstance(user_data, dict):
        collections = user_data.get('collections', {})
        collection_key = f"{collection}:{key}"
        return collections.get(collection_key, None)
    return None

def save_user_items(username, item_data, collection='user_inventory', key='avatar'):
    items = _load_items()
    if username not in items:
        items[username] = {'collections': {}}
    if 'collections' not in items[username]:
        items[username]['collections'] = {}
    collection_key = f"{collection}:{key}"
    items[username]['collections'][collection_key] = item_data
    return _save_items(items)

def _get_currency_file_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'currency.json')

def _load_currencies():
    path = _get_currency_file_path()
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

def _save_currencies(currencies):
    path = _get_currency_file_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(currencies, f, indent=2)
        return True
    except Exception:
        return False

def get_user_currency(username):
    currencies = _load_currencies()
    if username not in currencies:
        currencies[username] = {'rp': 20000000, 'nuts': 20000000, 'cc': 20000000}
        _save_currencies(currencies)
    return currencies.get(username, {})

def save_user_currency(username, currency_data):
    currencies = _load_currencies()
    currencies[username] = currency_data
    return _save_currencies(currencies)

def update_user_currency(username, rp=None, nuts=None, cc=None):
    currencies = _load_currencies()
    if username not in currencies:
        currencies[username] = {'rp': 20000000, 'nuts': 20000000, 'cc': 20000000}
    if rp is not None:
        currencies[username]['rp'] = rp
    if nuts is not None:
        currencies[username]['nuts'] = nuts
    if cc is not None:
        currencies[username]['cc'] = cc
    _save_currencies(currencies)
    return currencies[username]

def _get_colors_file_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pp_colors.json')

def _load_colors():
    path = _get_colors_file_path()
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

def _save_colors(colors):
    path = _get_colors_file_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(colors, f, indent=2)
        return True
    except Exception:
        return False

def get_user_color(username):
    colors = _load_colors()
    val = colors.get(username)
    if val is None:
        return None
    if isinstance(val, str):
        return {'color': val, 'display': None}
    if isinstance(val, dict):
        color = val.get('color') or val.get('colour') or val.get('value')
        display = val.get('display') or val.get('display_name') or val.get('nametag')
        return {'color': color, 'display': display}
    return None

def set_user_color(username, color, display_name=None):
    colors = _load_colors()
    if isinstance(color, dict):
        entry = {
            'color': color.get('color') or color.get('colour') or color.get('value'),
            'display': color.get('display') or color.get('display_name') or color.get('nametag') or display_name
        }
    else:
        entry = {'color': color, 'display': display_name}
    colors[username] = entry
    return _save_colors(colors)

def remove_user_color(username):
    colors = _load_colors()
    if username in colors:
        del colors[username]
        return _save_colors(colors)
    return True

def format_display_username(base_username, color_entry):
    if not color_entry:
        return base_username
    if isinstance(color_entry, dict):
        color = color_entry.get('color')
        display = color_entry.get('display') or base_username
    else:
        color = color_entry
        display = base_username
    if color:
        return f"<color={color}>{display}</color>"
    return display

def _get_loadout_file_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pp_loadout.json')

def _load_loadouts():
    path = _get_loadout_file_path()
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set([str(u).strip().lower() for u in data if u])
                if isinstance(data, dict) and 'allowed' in data and isinstance(data['allowed'], list):
                    return set([str(u).strip().lower() for u in data['allowed'] if u])
        return set()
    except Exception:
        return set()

def _save_loadouts(allowed_set):
    path = _get_loadout_file_path()
    try:
        out = {'allowed': sorted(list(allowed_set))}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2)
        return True
    except Exception:
        return False

def is_user_allowed_loadout(username):
    if not username:
        return False
    allowed = _load_loadouts()
    return str(username).strip().lower() in allowed

def add_user_to_loadout_allowlist(username):
    if not username:
        return False
    allowed = _load_loadouts()
    allowed.add(str(username).strip().lower())
    return _save_loadouts(allowed)

def remove_user_from_loadout_allowlist(username):
    if not username:
        return False
    allowed = _load_loadouts()
    if str(username).strip().lower() in allowed:
        allowed.remove(str(username).strip().lower())
        return _save_loadouts(allowed)
    return False

def _get_leaderboard_file_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'leaderboard.json')

def _load_leaderboard():
    path = _get_leaderboard_file_path()
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

def _save_leaderboard(data):
    path = _get_leaderboard_file_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False

def get_leaderboard(leaderboard_id):
    lb = _load_leaderboard()
    return lb.get(leaderboard_id, [])

def update_leaderboard_score(leaderboard_id, username, score, metadata=None):
    lb = _load_leaderboard()
    if leaderboard_id not in lb:
        lb[leaderboard_id] = []
    entries = lb[leaderboard_id]
    existing = next((e for e in entries if e.get('username') == username), None)
    if existing:
        if score > existing.get('score', 0):
            existing['score'] = score
            existing['metadata'] = metadata or {}
            existing['update_time'] = int(time.time())
    else:
        entries.append({
            'username': username,
            'score': score,
            'metadata': metadata or {},
            'create_time': int(time.time()),
            'update_time': int(time.time()),
        })
    entries.sort(key=lambda e: e.get('score', 0), reverse=True)
    lb[leaderboard_id] = entries
    _save_leaderboard(lb)

def _get_default_avatar():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pp_default_avatar.json')
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return {
                        'value': json.dumps(data),
                        'update_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                        'version': secrets.token_hex(8)
                    }
                if isinstance(data, str):
                    return {
                        'value': data,
                        'update_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                        'version': secrets.token_hex(8)
                    }
    except Exception:
        pass
    return None

def _item_slot(item_id):
    parts = str(item_id).split('_') if item_id else []
    if not parts:
        return item_id
    if len(parts) > 1:
        if parts[0] in ('bp', 'acc') and parts[1] == 'arm' and len(parts) > 2 and parts[2] in ('l', 'r'):
            return '_'.join(parts[:3])
        return '_'.join(parts[:2])
    return parts[0]

def replace_avatar_items_by_slot(existing_items, incoming_items):
    if not isinstance(existing_items, list):
        existing_items = []
    if not isinstance(incoming_items, list):
        incoming_items = [incoming_items]
    existing_slots = {it: _item_slot(it) for it in existing_items}
    out_items = [it for it in existing_items]
    for new_item in incoming_items:
        new_slot = _item_slot(new_item)
        out_items = [it for it in out_items if existing_slots.get(it) != new_slot]
        if new_item not in out_items:
            out_items.append(new_item)
        existing_slots = {it: _item_slot(it) for it in out_items}
    return out_items

def _is_accessory(item_id):
    if not item_id:
        return False
    s = str(item_id)
    return s.startswith('acc_') or s.startswith('animal_') or s.startswith('outfit_') or s.startswith('acc_fit')

def apply_items_to_avatar_fields(av_val, items):
    if not isinstance(av_val, dict):
        return av_val
    if not isinstance(items, list):
        try:
            items = list(items)
        except Exception:
            items = []
    av_val['items'] = items
    for it in items:
        if not isinstance(it, str):
            continue
        if it.startswith('bp_head'):
            av_val['head'] = it
        elif it.startswith('bp_eye'):
            av_val['eyeLeft'] = it
            av_val['eyeRight'] = it
        elif it.startswith('bp_torso'):
            av_val['torso'] = it
        elif it.startswith('bp_arm_l'):
            av_val['armLeft'] = it
        elif it.startswith('bp_arm_r'):
            av_val['armRight'] = it
        elif it.startswith('bp_butt'):
            av_val['butt'] = it
        elif it.startswith('bp_tail'):
            av_val['tail'] = it
    accessories = [it for it in items if _is_accessory(it)]
    av_val['accessories'] = accessories
    return av_val

def enforce_mop_hat_policy(avatar, is_mod):
    if not isinstance(avatar, dict):
        return avatar
    items = avatar.get('items') if isinstance(avatar.get('items'), list) else None
    if items is None:
        items = []
        for f in ('head', 'eyeLeft', 'eyeRight', 'torso', 'armLeft', 'armRight', 'butt', 'tail'):
            v = avatar.get(f)
            if v:
                items.append(v)
        accs = avatar.get('accessories', [])
        if isinstance(accs, list):
            for a in accs:
                if a and a not in items:
                    items.append(a)
    access = [a for a in items if _is_accessory(a)]
    if is_mod:
        if 'acc_head_mop' not in access:
            access.append('acc_head_mop')
        if 'acc_head_mop' not in items:
            items.append('acc_head_mop')
    else:
        access = [a for a in access if a != 'acc_head_mop']
        items = [a for a in items if a != 'acc_head_mop']
    items = replace_avatar_items_by_slot(items if isinstance(items, list) else [], items)
    avatar = apply_items_to_avatar_fields(avatar, items)
    avatar['accessories'] = [a for a in avatar.get('accessories', []) if a in access or _is_accessory(a)]
    return avatar

def enforce_dev_policy(avatar, is_dev):
    if not isinstance(avatar, dict):
        return avatar
    items = avatar.get('items') if isinstance(avatar.get('items'), list) else None
    if items is None:
        items = []
        for f in ('head', 'eyeLeft', 'eyeRight', 'torso', 'armLeft', 'armRight', 'butt', 'tail'):
            v = avatar.get(f)
            if v:
                items.append(v)
        accs = avatar.get('accessories', [])
        if isinstance(accs, list):
            for a in accs:
                if a and a not in items:
                    items.append(a)
    access = [a for a in items if _is_accessory(a)]
    if is_dev:
        if 'acc_ear_l_earring_banana' not in access:
            access.append('acc_ear_l_earring_banana')
        if 'acc_ear_l_earring_banana' not in items:
            items.append('acc_ear_l_earring_banana')
    else:
        access = [a for a in access if a != 'acc_ear_l_earring_banana']
        items = [a for a in items if a != 'acc_ear_l_earring_banana']
    items = replace_avatar_items_by_slot(items if isinstance(items, list) else [], items)
    avatar = apply_items_to_avatar_fields(avatar, items)
    avatar['accessories'] = [a for a in avatar.get('accessories', []) if a in access or _is_accessory(a)]
    return avatar

def _register_session(session_id, username):
    now = int(time.time())
    with _session_store_lock:
        old_sid = _user_active_sid.get(username)
        if old_sid:
            _session_store.pop(old_sid, None)
        _session_store[session_id] = {"origin": now, "username": username}
        _user_active_sid[username] = session_id

def _get_session(session_id):
    with _session_store_lock:
        return _session_store.get(session_id)

def _consume_nonce(nonce):
    now = time.time()
    with _used_nonces_lock:
        expired = [k for k, t in _used_nonces.items() if now - t > _NONCE_TTL]
        for k in expired:
            del _used_nonces[k]
        if nonce in _used_nonces:
            return False
        _used_nonces[nonce] = now
    return True

def _load_zip_from_url(url):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        result = {}
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            for name in zf.namelist():
                if name.endswith(".json"):
                    key = os.path.basename(name).replace(".json", "")
                    with zf.open(name) as f:
                        result[key] = json.load(f)
        print(f"[GameData] Loaded: {list(result.keys())}")
        return result
    except Exception as e:
        print(f"[GameData] Failed to load zip: {e}")
        return {}

def get_game_data(key):
    if not _game_data_cache:
        _game_data_cache.update(_load_zip_from_url(GAME_DATA_ZIP_URL))
    data = _game_data_cache.get(key, [])
    if not data:
        _game_data_cache.update(_load_zip_from_url(GAME_DATA_ZIP_URL))
        data = _game_data_cache.get(key, [])
    return data

def get_all_avatar_item_ids():
    return [item["id"] for item in get_game_data("econ_avatar_items")]

def get_all_research_node_ids():
    return [node["id"] for node in get_game_data("econ_research_nodes")]

try:
    _game_data_cache.update(_load_zip_from_url(GAME_DATA_ZIP_URL))
except Exception:
    pass

DATA_FILE = os.path.join(os.path.dirname(__file__), "save-data.json")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Save Error] {e}")

def get_user_data(username):
    db = load_data()
    return db.get(username, {})

def set_user_data(username, key, value):
    db = load_data()
    if username not in db:
        db[username] = {}
    db[username][key] = value
    save_data(db)

def set_user_data_bulk(username, updates):
    db = load_data()
    if username not in db:
        db[username] = {}
    db[username].update(updates)
    save_data(db)

def get_all_user_data(username):
    db = load_data()
    return db.get(username, {})

def _build_user_objects(username, udata):
    now = "2025-01-01T00:00:00Z"
    user_id = udata.get("user_id") or str(uuid.uuid4())

    saved_avatar = get_user_avatar(username)
    avatar_value = saved_avatar.get('value') if saved_avatar and 'value' in saved_avatar else '{}'

    inv_avatar_value = default_avatar_inventory()

    saved_stash = get_user_items(username, 'user_inventory', 'stash')
    stash_value = saved_stash.get('value') if saved_stash and 'value' in saved_stash else DEFAULT_STASH

    saved_loadout = get_user_items(username, 'user_inventory', 'gameplay_loadout')
    if saved_loadout and saved_loadout.get('value'):
        loadout_value = saved_loadout['value']
    else:
        generated = _generate_random_loadout()
        loadout_value = generated['objects'][0]['value']
        save_user_items(username, {
            'value': loadout_value,
            'update_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'version': secrets.token_hex(8)
        }, 'user_inventory', 'gameplay_loadout')

    return {"objects": [
        {"collection": "user_avatar", "key": "0", "user_id": user_id, "value": avatar_value, "version": "e897bbeb9a5d4364d73dee44c2d4e6e4", "permission_read": 2, "create_time": now, "update_time": now},
        {"collection": "user_inventory", "key": "avatar", "user_id": user_id, "value": inv_avatar_value, "version": "277a87beb4905dbe2333d5cd55a7e5be", "permission_read": 1, "create_time": now, "update_time": now},
        {"collection": "user_inventory", "key": "research", "user_id": user_id, "value": default_research_inventory(), "version": "58c1d1c4ade0e8e205939be8a07ce49b", "permission_read": 1, "create_time": now, "update_time": now},
        {"collection": "user_inventory", "key": "stash", "user_id": user_id, "value": stash_value, "version": "d1315c03b540bef68ce4742d46e77cc0", "permission_read": 1, "permission_write": 1, "create_time": now, "update_time": now},
        {"collection": "user_inventory", "key": "stash_upgrades", "user_id": user_id, "value": DEFAULT_STASH_UPGRADES, "version": "af1feb89bd8c849f5f16a4754577be04", "permission_read": 1, "create_time": now, "update_time": now},
        {"collection": "user_inventory", "key": "gameplay_loadout", "user_id": user_id, "value": loadout_value, "version": "3846efa925d304495efbfed41eaafe74", "permission_read": 1, "permission_write": 1, "create_time": now, "update_time": now},
        {"collection": "user_preferences", "key": "gameplay_items", "user_id": user_id, "value": _val(udata, "user_preferences", "gameplay_items", DEFAULT_GAMEPLAY_PREFS), "version": "fe9acf47fd31aeb3ea1aa209e6485ce3", "permission_read": 1, "permission_write": 1, "create_time": now, "update_time": now},
        {"collection": "user_preferences", "key": "common", "user_id": user_id, "value": _val(udata, "user_preferences", "common", DEFAULT_COMMON_PREFS), "version": "d56295314bb7a4c43e13da9c446a77a8", "permission_read": 1, "permission_write": 1, "create_time": now, "update_time": now},
    ]}

def get_wallet(username):
    d = get_user_data(username)
    return d.get("wallet", {
        "stashCols": 8, "stashRows": 8,
        "hardCurrency": 9_999_999,
        "softCurrency": 9_999_999,
        "researchPoints": 9_999_999,
    })

def save_wallet(username, wallet):
    set_user_data(username, "wallet", wallet)

def b64decode_json(obj):
    return json.loads(base64.urlsafe_b64decode(obj + '=' * (-len(obj) % 4)).decode())

def b64encode_json(obj):
    return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip('=')

def verify_meta_nonce(nonce, oculus_id):
    return True

def skidatoken(a, b, c):
    data = f"{a}|{b}|{c}"
    salt = os.urandom(16)
    digest = hashlib.sha256(salt + data.encode()).digest()
    token = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    mid = len(token) // 2
    return token[:mid] + "-" + token[mid:]

def ilowkeydontknowwhy():
    return str(int(time.time()) + 86400)

def _get_username_from_request():
    token = request.args.get("token", "") or request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]
    try:
        parts = token.split(".")
        if len(parts) == 3:
            payload = b64decode_json(parts[1])
            return payload.get("usn")
    except Exception:
        pass
    try:
        import jwt as pyjwt
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("usn")
    except Exception:
        pass
    return None

def _toast_auth():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = request.args.get('token', '')
    if not token:
        return None
    try:
        parts = token.split(".")
        if len(parts) == 3:
            payload = b64decode_json(parts[1])
            if time.time() > payload.get('exp', 0):
                return None
            username = payload.get('usn') or payload.get('username') or payload.get('user')
            if username:
                banned = get_banned_users()
                if str(username).strip().lower() in banned:
                    return None
            return username
    except Exception:
        pass
    try:
        import jwt as pyjwt
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get('usn') or payload.get('username') or payload.get('user')
        if username:
            banned = get_banned_users()
            if str(username).strip().lower() in banned:
                return None
        return username
    except Exception:
        return None

def track_player_join(username, ip="Unknown", room_code="None"):
    if not username:
        return
    join_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    message = f"""
✅ **Player Joined**

**Username:** `{username}`
**Photon Room Code:** `{room_code}`
**Time:** {join_time}
    """.strip()
    log_login(message)
    print(f"[Player Tracker] {username} joined room '{room_code}' from {ip}")

SERVER_SHUTDOWN = False
INT_MESSAGE = {"message": "<size=15><color=red>Rain.LOL on TOP !!!!!!!</color></size>"}

@app.before_request
def check_shutdown():
    if SERVER_SHUTDOWN:
        if request.path in ["/", "/photon/auth"]:
            return jsonify(INT_MESSAGE), 503
        blocked_paths = [
            "/3/v2/account/authenticate/custom",
            "/v2/account/authenticate/custom",
            "/nnnnaakamacloud.c/v2/account/authenticate/custom",
            "/3/v2/account",
            "/v2/account",
            "/v2/storage",
            "/3/v2/storage",
            "/v2/rpc/",
            "/3/v2/rpc/",
        ]
        if any(path in request.path for path in blocked_paths):
            return jsonify(INT_MESSAGE), 503

@app.before_request
def block_kick():
    _path = request.path.lower()
    _payload = request.args.get("payload", "").lower()
    _body = (request.get_data(as_text=True) or "").lower()
    _KICK_TERMS = ("kick", "rpc_kickplayer")
    if any(t in _path or t in _payload or t in _body for t in _KICK_TERMS):
        return jsonify({"error": "forbidden", "reason": "RPC_KickPlayer is disabled on this server"}), 403


@app.before_request
def log_storage_requests():
    if request.path in ["/v2/storage", "/3/v2/storage", "/nnnnaakamacloud.c/v2/storage"]:
        print(f"\n{'='*60}")
        print(f"[STORAGE REQUEST] {request.method} {request.path}")
        print(f"Headers: {dict(request.headers)}")
        print(f"Args: {dict(request.args)}")
        try:
            body = request.get_json(silent=True)
            if body:
                print(f"Body: {json.dumps(body, indent=2)[:1000]}")
            else:
                print(f"Body: {request.get_data(as_text=True)[:500]}")
        except:
            print(f"Body: {request.get_data(as_text=True)[:500]}")
        print(f"{'='*60}")

@app.before_request
def check_ip_ban():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if is_ip_banned(client_ip):
        server_log(f"[BLOCKED] Banned IP attempted access: {client_ip} - {request.method} {request.path}")
        return jsonify({'error': 'Your IP address is banned', 'status': 403}), 403

@app.before_request
def set_log_username():
    g.log_username = _toast_auth()

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    log_error(f"🚨 **Server Error**\n```{traceback.format_exc()[:1800]}```")
    return jsonify({"error": "internal server error"}), 500

DEFAULT_STASH_UPGRADES = '{"upgrades":["col_1","col_2","col_3","col_4","col_5","col_6","col_7","col_8","row_1","row_2","row_3","row_4","row_5","row_6","row_7","row_8","mtl_1","mtl_2","mtl_3","mtl_4","mtl_5","mtl_6","mtl_7","mtl_8"]}'
DEFAULT_STASH = '{"items":[]}'
DEFAULT_LOADOUT = '{"version":1}'
DEFAULT_GAMEPLAY_PREFS = '{"recents":[]}'
DEFAULT_COMMON_PREFS = '{"appearOffline":false}'

FALLBACK_AVATAR_ITEM_IDS = ["acc_ear_l_earring_banana","acc_face_cybersuit_helmet","acc_face_glasses_blue","acc_face_glasses_coloredvisor","acc_face_glasses_coolglasses","acc_face_glasses_geek","acc_face_glasses_heart","acc_face_glasses_holiday","acc_face_glasses_pink","acc_face_glasses_rayban","acc_face_glasses_round","acc_face_glasses_sunglasses","acc_face_goggles","acc_fit_animesuit","acc_fit_apocalypsesurvivor","acc_fit_arbordaydruid","acc_fit_bunnyoutfit","acc_fit_business_suit","acc_fit_cybersuit","acc_fit_hazmatsuit","acc_fit_kpop","acc_fit_leatherjacket","acc_fit_samurai","acc_fit_santa","acc_fit_spacesuit","acc_fit_viking","acc_head_banana_hat","acc_head_beanie","acc_head_beret","acc_head_cap","acc_head_catearscap","acc_head_clownhat","acc_head_cowboy_hat","acc_head_crown","acc_head_fedora_hat","acc_head_hardhat","acc_head_piratehat","acc_head_top_hat","animal_cat","animal_duck","animal_frog","animal_gorilla","animal_pug","animal_rabbit","animal_shark","animal_tiger","animal_trex","bp_arm_l_gorilla","bp_arm_r_gorilla","bp_butt_gorilla","bp_eye_gorilla","bp_head_gorilla","bp_tail_cat","bp_torso_gorilla","outfit_anime_fem_pink","outfit_bunny","outfit_hazmat_yellow","outfit_kpop","outfit_santa","outfit_viking"]

def default_avatar_inventory():
    items = get_all_avatar_item_ids()
    if not items:
        _game_data_cache.update(_load_zip_from_url(GAME_DATA_ZIP_URL))
        items = get_all_avatar_item_ids()
    return json.dumps({"items": items or FALLBACK_AVATAR_ITEM_IDS})

def default_research_inventory():
    nodes = get_all_research_node_ids()
    if not nodes:
        _game_data_cache.update(_load_zip_from_url(GAME_DATA_ZIP_URL))
        nodes = get_all_research_node_ids()
    return json.dumps({"nodes": nodes})

def _val(udata, col, key, default_fn):
    saved = udata.get(f"{col}:{key}")
    if saved is None:
        return default_fn() if callable(default_fn) else default_fn
    if col == "user_inventory" and key == "research":
        try:
            parsed = json.loads(saved) if isinstance(saved, str) else saved
            if not parsed.get("nodes"):
                return default_fn() if callable(default_fn) else default_fn
        except Exception:
            pass
    if isinstance(saved, str):
        return saved
    return json.dumps(saved)

def _build_storage_objects(username):
    udata = get_user_data(username)
    now = "2025-01-01T00:00:00Z"
    user_id = udata.get("user_id") or str(uuid.uuid4())
    set_user_data(username, "user_id", user_id)

    saved_avatar = get_user_avatar(username)
    avatar_value = saved_avatar.get('value') if saved_avatar and 'value' in saved_avatar else '{}'

    inv_avatar_value = default_avatar_inventory()

    saved_stash = get_user_items(username, 'user_inventory', 'stash')
    stash_value = saved_stash.get('value') if saved_stash and 'value' in saved_stash else DEFAULT_STASH

    saved_loadout = get_user_items(username, 'user_inventory', 'gameplay_loadout')
    if saved_loadout and saved_loadout.get('value'):
        loadout_value = saved_loadout['value']
    else:
        generated = _generate_random_loadout()
        loadout_value = generated['objects'][0]['value']
        save_user_items(username, {
            'value': loadout_value,
            'update_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'version': secrets.token_hex(8)
        }, 'user_inventory', 'gameplay_loadout')

    is_mod = str(username).strip().lower() in {m.strip().lower() for m in get_mod_users()} or username == MOD_USER
    is_dev = str(username).strip().lower() in {d.strip().lower() for d in get_dev_users()}

    if avatar_value and isinstance(avatar_value, str):
        try:
            av = json.loads(avatar_value)
            if isinstance(av, dict):
                av = enforce_mop_hat_policy(av, is_mod)
                av = enforce_dev_policy(av, is_dev)
                avatar_value = json.dumps(av)
        except Exception:
            pass

    return {"objects": [
        {"collection": "user_avatar", "key": "0", "user_id": user_id, "value": avatar_value, "version": "e897bbeb9a5d4364d73dee44c2d4e6e4", "permission_read": 2, "create_time": now, "update_time": now},
        {"collection": "user_inventory", "key": "avatar", "user_id": user_id, "value": inv_avatar_value, "version": "277a87beb4905dbe2333d5cd55a7e5be", "permission_read": 1, "create_time": now, "update_time": now},
        {"collection": "user_inventory", "key": "research", "user_id": user_id, "value": default_research_inventory(), "version": "58c1d1c4ade0e8e205939be8a07ce49b", "permission_read": 1, "create_time": now, "update_time": now},
        {"collection": "user_inventory", "key": "stash", "user_id": user_id, "value": stash_value, "version": "d1315c03b540bef68ce4742d46e77cc0", "permission_read": 1, "permission_write": 1, "create_time": now, "update_time": now},
        {"collection": "user_inventory", "key": "stash_upgrades", "user_id": user_id, "value": DEFAULT_STASH_UPGRADES, "version": "af1feb89bd8c849f5f16a4754577be04", "permission_read": 1, "create_time": now, "update_time": now},
        {"collection": "user_inventory", "key": "gameplay_loadout", "user_id": user_id, "value": loadout_value, "version": "3846efa925d304495efbfed41eaafe74", "permission_read": 1, "permission_write": 1, "create_time": now, "update_time": now},
        {"collection": "user_preferences", "key": "gameplay_items", "user_id": user_id, "value": _val(udata, "user_preferences", "gameplay_items", DEFAULT_GAMEPLAY_PREFS), "version": "fe9acf47fd31aeb3ea1aa209e6485ce3", "permission_read": 1, "permission_write": 1, "create_time": now, "update_time": now},
        {"collection": "user_preferences", "key": "common", "user_id": user_id, "value": _val(udata, "user_preferences", "common", DEFAULT_COMMON_PREFS), "version": "d56295314bb7a4c43e13da9c446a77a8", "permission_read": 1, "permission_write": 1, "create_time": now, "update_time": now},
    ]}

def _build_econ_objects(collection, data):
    now = "2025-05-28T16:03:59Z"
    return {"objects": [{
        "collection": collection,
        "key": e["id"],
        "user_id": "00000000-0000-0000-0000-000000000000",
        "value": json.dumps(e),
        "version": "5c8518bd84cdb43a4e057cb62ca8d5b1",
        "permission_read": 2,
        "create_time": now,
        "update_time": now,
    } for e in data]}

def _generate_random_loadout():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'econ_gameplay_items.json'), 'r') as f:
            data = json.load(f)
        item_ids = [item['id'] for item in data if 'id' in item]
    except Exception:
        item_ids = ['item_jetpack', 'item_flaregun', 'item_dynamite', 'item_tablet', 'item_flashlight_mega', 'item_plunger', 'item_crossbow', 'item_revolver', 'item_shotgun', 'item_pickaxe']
    children = []
    for _ in range(20):
        if random.random() < .7 and 'item_arena_pistol' in item_ids:
            selected_item = 'item_arena_pistol'
        else:
            selected_item = random.choice(item_ids)
        children.append({'itemID': selected_item, 'scaleModifier': 100, 'colorHue': random.randint(10, 111), 'colorSaturation': random.randint(10, 111)})
    payload = {'objects': [{'collection': 'user_inventory', 'key': 'gameplay_loadout', 'permission_read': 1, 'permission_write': 1, 'value': json.dumps({'version': 1, 'back': {'itemID': 'item_backpack_large_base', 'scaleModifier': 120, 'colorHue': 50, 'colorSaturation': 50, 'children': children}})}]}
    return payload

def BearerGeneration(username):
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    uid = "8c1acc32f2454fb9a9a76fb6dfbf572f" if username == "unitygame" else uuid.uuid4().hex
    tid = "f6ac88a5575546c2b2b7ca93d3e3f488" if username == "unitygame" else uuid.uuid4().hex
    sid = secrets.token_hex(16)
    _register_session(sid, username)
    payload = {
        "tid": tid, "uid": uid, "usn": username, "sid": sid,
        "vrs": {
            "authID": secrets.token_hex(16),
            "clientUserAgent": "MetaQuest 1.36.2.1622_828307",
            "loginType": "meta_quest",
        },
        "exp": now + 86400, "iat": now,
    }
    token = f"{b64encode_json(header)}.{b64encode_json(payload)}.{secrets.token_urlsafe(32)}"

    all_items = get_all_avatar_item_ids() or FALLBACK_AVATAR_ITEM_IDS
    save_user_items(username, {
        'value': json.dumps({"items": all_items}),
        'update_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'version': secrets.token_hex(8)
    }, 'user_inventory', 'avatar')
    set_user_data(username, "user_inventory:avatar", json.dumps({"items": all_items}))
    all_nodes = get_all_research_node_ids()
    if all_nodes:
        set_user_data(username, "user_inventory:research", json.dumps({"nodes": all_nodes}))

    return jsonify({"token": token, "refresh_token": token}), 200

def check_ban(username, oculus_id=None):
    if username in BANNED_USERNAMES or (oculus_id and oculus_id in BANNED_OCULUS_IDS):
        return True
    banned_file = get_banned_users()
    if str(username).strip().lower() in banned_file:
        return True
    return False

def check_whitelist(username):
    if not WHITELIST_ENABLED:
        return False
    return username not in WHITELISTED_USERNAMES

def _verify_attestation(body):
    attest_token = (
        body.get("attestationToken")
        or body.get("attesttoken")
        or request.headers.get("X-Attestation-Token")
    )
    if not attest_token:
        return None

    try:
        claims_b64 = attest_token.split(".")[1] if "." in attest_token else attest_token
        padding = 4 - len(claims_b64) % 4
        claims_json = json.loads(base64.urlsafe_b64decode(claims_b64 + "=" * padding).decode("utf-8"))
    except Exception:
        return None

    app_state = claims_json.get("app_state", {})
    device_state = claims_json.get("device_state", {})
    device_ban = claims_json.get("device_ban", {})

    if app_state.get("package_id") != EXPECTED_PACKAGE:
        return jsonify({"Message": "INVALID PACKAGE", "Code": "7"}), 403

    if device_state.get("VRIntegrity") != "Advanced":
        return jsonify({"Message": "UNTRUSTED DEVICE", "Code": "7"}), 403

    if app_state.get("app_integrity_state") != "Store":
        return jsonify({"Message": "SIDELOADED APK", "Code": "7"}), 403

    if device_ban.get("is_banned"):
        return jsonify({"Message": "DEVICE BANNED", "Code": "7"}), 403

    return None

@app.route("/", methods=["GET", "POST"])
@app.route("/photon/auth", methods=["GET", "POST"])
def photon_auth():
    return jsonify({"ResultCode": 1, "Message": "Authenticated"})

@app.route("/nnnnaakamacloud.c/", methods=["GET", "POST"])
def root_nnnn():
    return jsonify({"token": "b"}), 200

@app.route("/Halloween/authenticEate/Redo/Sigma", methods=["GET", "POST"])
def test_auth():
    return jsonify({
        "Authenticated": "true", "ResultCode": 1,
        "UserId": secrets.token_hex(16), "SessionID": secrets.token_hex(16),
        "Message": "Authenticated successfully",
    })

@app.route("/3/v2/account/authenticate/custom", methods=["POST", "GET"])
@app.route("/v2/account/authenticate/custom", methods=["POST", "GET"])
@app.route("/nnnnaakamacloud.c/v2/account/authenticate/custom", methods=["POST", "GET"])
def authenticate_custom():
    body = request.get_json(silent=True) or {}
    username = request.args.get("username", "") or body.get("username", "")
    if not username:
        return jsonify({"error": "missing_username"}), 400
    username = username.rstrip("& \t\n\r")
    nonce = body.get("nonce") or request.args.get("nonce", "")
    oculus_id = (body.get("oculusId") or body.get("platformUserID") or request.args.get("oculusId", ""))
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "Unknown"

    if _is_rate_limited(f"auth:{client_ip}", max_requests=5, window_seconds=60):
        return _rate_limit_response()

    if check_ban(username, oculus_id):
        log_ban(f"🚫 **Banned user attempted login**\n**Username:** `{username}`\n**IP:** `{client_ip}`")
        return jsonify({"message": BAN_MESSAGE}), 401

    if check_whitelist(username):
        return jsonify(WHITELIST_MESSAGE), 403

    attest_result = _verify_attestation(body)
    if attest_result is not None:
        return attest_result

    flask_session['username'] = username

    if username:
        track_player_join(username, client_ip, "None (Auth only)")

    stored_oid = get_user_data(username).get("oculus_id") if username else None
    if oculus_id:
        if not nonce:
            return jsonify({"error": "nonce required with oculusId"}), 401
        if not _consume_nonce(nonce):
            return jsonify({"error": "invalid or expired nonce"}), 401
        if not verify_meta_nonce(nonce, oculus_id):
            return jsonify({"message": BAN_MESSAGE}), 401
        if stored_oid is None:
            set_user_data(username, "oculus_id", oculus_id)
        elif stored_oid != oculus_id:
            return jsonify({"message": BAN_MESSAGE}), 401
    else:
        if stored_oid is not None:
            return jsonify({"error": "oculusId required for this account"}), 401

    return BearerGeneration(username)

@app.route("/v2/account/authenticate/device", methods=["POST"])
def authenticate_device():
    body = request.get_json(silent=True) or {}
    device_id = body.get("id")
    if not device_id:
        return jsonify({"error": "missing device id"}), 400
    return BearerGeneration(device_id)

@app.route("/3/v2/rpc/photon.joinroom", methods=["POST"])
@app.route("/v2/rpc/photon.joinroom", methods=["POST"])
@app.route("/nnnnaakamacloud.c/v2/rpc/photon.joinroom", methods=["POST"])
def photon_join_room():
    username = _get_username_from_request()
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "Unknown"
    try:
        data = request.get_json(silent=True) or {}
        room_code = data.get("roomCode") or data.get("roomName") or data.get("code") or "Unknown"
    except Exception:
        room_code = "Unknown"
    if username:
        track_player_join(username, client_ip, room_code)
        return jsonify({"payload": json.dumps({"success": True, "room": room_code})}), 200
    return jsonify({"payload": json.dumps({"success": False})}), 400

@app.route("/3/v2/account/session/refresh", methods=["POST", "GET"])
@app.route("/v2/account/session/refresh", methods=["POST", "GET"])
@app.route("/nnnnaakamacloud.c/v2/account/session/refresh", methods=["POST"])
def session_refresh():
    now = int(time.time())
    token = request.args.get("token", "") or request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]
    try:
        parts = token.split(".")
        payload = b64decode_json(parts[1])
        sid = payload.get("sid", "")
        session = _get_session(sid) if sid else None
        if not session:
            return jsonify({"error": "session not found, please re-authenticate"}), 401
        session_age = now - session["origin"]
        if session_age >= MAX_SESSION_LIFETIME:
            with _session_store_lock:
                _session_store.pop(sid, None)
            return jsonify({"error": "session expired, please re-authenticate"}), 401
        remaining = MAX_SESSION_LIFETIME - session_age
        new_exp = now + min(TOKEN_TTL, remaining)
        payload["exp"] = new_exp
        new_token = f"{parts[0]}.{b64encode_json(payload)}.{secrets.token_urlsafe(32)}"
        return jsonify({"token": new_token, "refresh_token": new_token})
    except Exception:
        return jsonify({"error": "invalid token"}), 403

@app.route("/3/v2/account/link/device", methods=["POST", "GET"])
@app.route("/v2/account/link/device", methods=["POST"])
@app.route("/nnnnaakamacloud.c/v2/account/link/device", methods=["POST", "GET"])
def link_device():
    return jsonify({
        "id": uuid.uuid4().hex, "user_id": secrets.token_hex(16), "linked": "true",
        "create_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }), 200

@app.route("/api/v1/preauth", methods=["POST"])
def fghhfghfghfghfghfgfgh():
    return jsonify({"attestID":"f28d7890-481b-4f90-a08f-287314e8be02","attestNonce":"4sWoVMCRma5Q9bLMmxksMJkHG5pgdG_k","time":1756899975,"updateType":"None"})

SPECIAL_USERS = {
    "unitygame": {"id": "8c1acc32f2454fb9a9a76fb6dfbf572f", "username": "<color=purple>Exploding_Car</color>", "display_name": "<color=purple>Exploding_Car</color>", "meta": {"isDeveloper": True}, "wallet": {"hardCurrency": 99999999999, "softCurrency": 99999999999, "researchPoints": 9999999999}},
    "skibb.ok": {"username": "<color=yellow>Skibb.Gay</color>", "display_name": "<color=yellow>Skibb.Gay</color>", "meta": {"isDeveloper": True}, "wallet": {"hardCurrency": 99999999999, "softCurrency": 99999999999, "researchPoints": 99999999999}},
    "Omelette180": {"username": "<color=purple>COOL PERSON</color>:Omelette", "display_name": "<color=purple>COOL PERSON</color>Omelette180", "meta": {"isDeveloper": True}, "wallet": {"hardCurrency": 1000000, "softCurrency": 1000000, "researchPoints": 1000000}},
    "sergiovr": {"username": "<color=red>SKIBIDI RIZZ</color>", "display_name": "<color=red>SKIBIDI RIZZ</color>", "meta": {"isDeveloper": True}, "wallet": {"hardCurrency": 1000000, "softCurrency": 1000000, "researchPoints": 1000000}},
    "FakeXera": {"username": "<color=purple>Fake Xera</color>", "display_name": "<color=purple>Fake Xera</color>", "meta": {"isDeveloper": True}, "wallet": {"hardCurrency": 1000000, "softCurrency": 1000000, "researchPoints": 1000000}},
    "GunyahJohn": {"username": "<color=green>Gunyah</color>", "display_name": "<color=green>Gunyah</color>", "meta": {"isDeveloper": True}, "wallet": {"hardCurrency": 99999999999, "softCurrency": 99999999999, "researchPoints": 99999999999}},
    "SD_WatchOD": {"username": "<color=blue>Watch</color>", "display_name": "<color=blue>Watch</color>", "meta": {"isDeveloper": True}, "wallet": {"hardCurrency": 1000000, "softCurrency": 1000000, "researchPoints": 1000000}},
    "harmonypatch": {"username": "<color=purple>Harmony</color>", "display_name": "<color=purple>Harmony</color>", "meta": {"isDeveloper": True}, "wallet": {"hardCurrency": 1000000, "softCurrency": 1000000, "researchPoints": 1000000}},
    "EvanBlokEnder": {"username": "<color=yellow>N5 ⋆</color>", "display_name": "<color=red>N5</color>", "meta": {"isDeveloper": True}, "wallet": {"hardCurrency": 99999999999, "softCurrency": 99999999999, "researchPoints": 99999999999}},
    "christian.886502.2010": {"username": "<size=50><color=pink>Christian</color></size>", "display_name": "<color=pink>Christian</color>", "meta": {"isDeveloper": True}, "wallet": {"hardCurrency": 99999999999, "softCurrency": 99999999999, "researchPoints": 99999999999}},
    "Pump.2HP": {"username": "<color=red>SKIDDER</color>", "display_name": "<color=red>SKIDDER</color>", "meta": {"isDeveloper": False}, "wallet": {"hardCurrency": 0, "softCurrency": 0, "researchPoints": 0}},
    "Rainn_67": {"username": "<color=red>Rain ⋆</color>", "display_name": "<color=red>Rain</color>", "meta": {"isDeveloper": True}, "wallet": {"hardCurrency": 99999999999, "softCurrency": 99999999999, "researchPoints": 99999999999}},
}

@app.route("/3/v2/account", methods=["POST", "GET"])
@app.route("/v2/account", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/account", methods=["GET", "POST", "PUT"])
def account():
    if request.method == "PUT":
        response = jsonify({})
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Content-Type'] = 'application/json'
        return response

    token = request.args.get("token", "") or request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]
    try:
        payload = b64decode_json(token.split(".")[1])
        username = payload["usn"]
    except Exception:
        username = None

    if not username:
        client_ip = _get_client_ip()
        user_info, banned = _db_get_user(client_ip)
        if banned or user_info is None:
            return jsonify({"error": "banned"}), 401
        username = user_info.get('username', 'unknown')
        custom_id = user_info.get('custom_id', _gen_custom_id())
    else:
        if check_ban(username):
            return jsonify({"message": BAN_MESSAGE}), 401
        custom_id = get_user_data(username).get("custom_id") or secrets.token_hex(8)
        set_user_data(username, "custom_id", custom_id)

    if username in SPECIAL_USERS:
        sp = SPECIAL_USERS[username]
        uid = sp.get("id", uuid.uuid4().hex)
        wallet = dict(sp["wallet"])
        wallet.update({"stashCols": 8, "stashRows": 8})
        saved = get_user_data(username).get("wallet", {})
        wallet.update(saved)
        return jsonify({
            "user": {"id": uid, "username": sp["username"], "display_name": sp["display_name"],
                     "lang_tag": "en", "metadata": sp["meta"], "edge_count": 240,
                     "create_time": "2024-08-24T04:20:56Z", "update_time": "2025-07-25T18:41:17Z"},
            "wallet": wallet, "custom_id": custom_id,
        })

    color_entry = get_user_color(username)
    display_username = format_display_username(username, color_entry) if color_entry else username
    user_currency = get_user_currency(username)
    wallet = {
        "stashCols": 8, "stashRows": 8,
        "hardCurrency": user_currency.get('cc', 1000000),
        "softCurrency": user_currency.get('nuts', 1000000),
        "researchPoints": user_currency.get('rp', 1000000),
    }
    return jsonify({
        "user": {"id": uuid.uuid4().hex, "username": display_username, "display_name": display_username,
                 "lang_tag": "en", "metadata": {"isDeveloper": True}, "edge_count": 240,
                 "create_time": "2024-08-24T04:20:56Z", "update_time": "2025-07-25T18:41:17Z"},
        "wallet": wallet, "custom_id": custom_id,
    })

@app.route("/v2/user", methods=["POST", "GET"])
@app.route("/nnnnaakamacloud.c/v2/user", methods=["POST", "GET"])
def get_user():
    uid = request.args.get("ids")
    username = _get_username_from_request()
    if not username:
        return jsonify({"error": "invalid token"}), 403
    if check_ban(username):
        return jsonify({"message": BAN_MESSAGE}), 401
    return jsonify({"username": username, "id": uid})

@app.route("/v2/friends", methods=["GET", "POST"])
@app.route("/nnnnaakamacloud.c/v2/friends", methods=["GET", "POST"])
def friends():
    return jsonify({"friends": [{
        "user": {
            "id": "8c1acc32f2454fb9a9a76fb6dfbf572f",
            "username": "<color=yellow>OWNER</color>: N5",
            "display_name": "<color=yellow>OWNER</color>: N5",
            "lang_tag": "en",
            "metadata": '{"IsDeveloper": true}',
            "create_time": "2024-10-19T10:33:56Z",
            "update_time": "2025-07-23T17:58:40Z",
        },
        "state": 1, "update_time": "2025-02-20T13:46:53Z",
        "metadata": '{"IsDeveloper": true}',
    }],
    "cursor": "M_-DAwEBDmVkZ2VMaXN0Q3Vyc29yAf-EAAECAQVTdGF0ZQEEAAEIUG9zaXRpb24BBAAAAA3_hAL4MIT4gPadsnQA"})

@app.route("/v2/storage/econ_mining_ores", methods=["GET", "POST", "PUT"])
@app.route("/3/v2/storage/econ_mining_ores", methods=["GET", "POST", "PUT"])
def econ_mining_ores():
    return jsonify(_build_econ_objects("econ_mining_ores", get_game_data("econ_mining_ores")))


@app.route("/3/v2/storage", methods=["GET", "POST", "PUT"])
@app.route("/v2/storage", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/storage", methods=["GET", "POST", "PUT"])
def storage():
    print("\n" + "="*80)
    print("[STORAGE] === REQUEST START ===")
    print(f"[STORAGE] Method: {request.method}")
    print(f"[STORAGE] Path: {request.path}")

    token = request.args.get("token", "") or request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]

    try:
        payload = b64decode_json(token.split(".")[1])
        username = payload.get("usn", "unknown")
    except Exception as e:
        username = _toast_auth() or "unknown"

    if check_ban(username):
        return jsonify({"message": BAN_MESSAGE}), 401

    target_user = request.args.get('user', username) or request.args.get('username', username)
    is_mod = str(username).strip().lower() in {m.strip().lower() for m in get_mod_users()} or username == MOD_USER
    is_dev = str(username).strip().lower() in {d.strip().lower() for d in get_dev_users()}

    if request.method == "POST":
        raw_body = request.get_data(as_text=True)
        print(f"[STORAGE] Raw body: {raw_body[:500]}")

        try:
            body = request.get_json(force=True, silent=False)
        except Exception as e:
            print(f"[STORAGE] JSON parse error: {e}")
            body = {}

        object_ids = body.get("object_ids", []) if body else []
        print(f"[STORAGE] object_ids: {object_ids}")

        if object_ids:
            results = []

            for obj_id in object_ids:
                collection = obj_id.get("collection", "")
                key = obj_id.get("key", "")
                user_id = obj_id.get("user_id", target_user)

                print(f"[STORAGE] collection: '{collection}', key: '{key}'")

                if collection.startswith("econ_"):
                    econ_data = get_game_data(collection)
                    print(f"[STORAGE] econ_data type: {type(econ_data)}")
                    print(f"[STORAGE] econ_data length: {len(econ_data) if econ_data else 0}")

                    # DEBUG: Print the actual data to see structure
                    if econ_data:
                        print(f"[STORAGE] econ_data content: {json.dumps(econ_data)[:500]}")

                    if econ_data and len(econ_data) > 0:
                        # Check if it's a list or dict
                        if isinstance(econ_data, dict):
                            # If it's a dict with items
                            items_list = econ_data.get("items", [])
                            if items_list:
                                for item in items_list:
                                    item_id = item.get("id") or item.get("ItemId") or item.get("itemID") or "unknown"
                                    results.append({
                                        "collection": collection,
                                        "key": item_id,
                                        "user_id": "00000000-0000-0000-0000-000000000000",
                                        "value": json.dumps(item),
                                        "version": "5c8518bd84cdb43a4e057cb62ca8d5b1",
                                        "permission_read": 2,
                                        "create_time": "2025-05-28T16:03:59Z",
                                        "update_time": "2025-05-28T16:03:59Z"
                                    })
                            else:
                                # Maybe it's a single config object
                                results.append({
                                    "collection": collection,
                                    "key": "config",
                                    "user_id": "00000000-0000-0000-0000-000000000000",
                                    "value": json.dumps(econ_data),
                                    "version": "5c8518bd84cdb43a4e057cb62ca8d5b1",
                                    "permission_read": 2,
                                    "create_time": "2025-05-28T16:03:59Z",
                                    "update_time": "2025-05-28T16:03:59Z"
                                })
                        else:
                            # It's a list
                            if key == "config":
                                for item in econ_data:
                                    item_id = item.get("id") or item.get("ItemId") or item.get("itemID") or "unknown"
                                    results.append({
                                        "collection": collection,
                                        "key": item_id,
                                        "user_id": "00000000-0000-0000-0000-000000000000",
                                        "value": json.dumps(item),
                                        "version": "5c8518bd84cdb43a4e057cb62ca8d5b1",
                                        "permission_read": 2,
                                        "create_time": "2025-05-28T16:03:59Z",
                                        "update_time": "2025-05-28T16:03:59Z"
                                    })
                            else:
                                found = False
                                for item in econ_data:
                                    item_id = item.get("id") or item.get("ItemId") or item.get("itemID") or item.get("ID")
                                    if item_id == key:
                                        results.append({
                                            "collection": collection,
                                            "key": key,
                                            "user_id": "00000000-0000-0000-0000-000000000000",
                                            "value": json.dumps(item),
                                            "version": "5c8518bd84cdb43a4e057cb62ca8d5b1",
                                            "permission_read": 2,
                                            "create_time": "2025-05-28T16:03:59Z",
                                            "update_time": "2025-05-28T16:03:59Z"
                                        })
                                        found = True
                                        break
                                if not found:
                                    results.append({
                                        "collection": collection,
                                        "key": key,
                                        "user_id": "00000000-0000-0000-0000-000000000000",
                                        "value": "{}",
                                        "version": secrets.token_hex(16),
                                        "permission_read": 1,
                                        "create_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                                        "update_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                                    })
                    else:
                        results.append({
                            "collection": collection,
                            "key": key,
                            "user_id": "00000000-0000-0000-0000-000000000000",
                            "value": "{}",
                            "version": secrets.token_hex(16),
                            "permission_read": 1,
                            "create_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                            "update_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                        })
                else:
                    # User collections
                    if collection == "user_avatar":
                        saved = get_user_avatar(user_id)
                        if saved and saved.get('value'):
                            results.append({
                                "collection": collection,
                                "key": key,
                                "user_id": user_id,
                                "value": saved['value'],
                                "version": saved.get('version', secrets.token_hex(16)),
                                "permission_read": 2,
                                "create_time": saved.get('create_time', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())),
                                "update_time": saved.get('update_time', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
                            })
                        else:
                            results.append({
                                "collection": collection,
                                "key": key,
                                "user_id": user_id,
                                "value": "{}",
                                "version": secrets.token_hex(16),
                                "permission_read": 1,
                                "create_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                                "update_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                            })
                    elif collection == "user_inventory":
                        saved = get_user_items(user_id, collection, key)
                        if saved and saved.get('value'):
                            results.append({
                                "collection": collection,
                                "key": key,
                                "user_id": user_id,
                                "value": saved['value'],
                                "version": saved.get('version', secrets.token_hex(16)),
                                "permission_read": 1,
                                "permission_write": 1,
                                "create_time": saved.get('create_time', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())),
                                "update_time": saved.get('update_time', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
                            })
                        else:
                            results.append({
                                "collection": collection,
                                "key": key,
                                "user_id": user_id,
                                "value": "{}",
                                "version": secrets.token_hex(16),
                                "permission_read": 1,
                                "permission_write": 1,
                                "create_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                                "update_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                            })
                    elif collection == "user_preferences":
                        saved = get_user_items(user_id, collection, key)
                        if saved and saved.get('value'):
                            results.append({
                                "collection": collection,
                                "key": key,
                                "user_id": user_id,
                                "value": saved['value'],
                                "version": saved.get('version', secrets.token_hex(16)),
                                "permission_read": 1,
                                "permission_write": 1,
                                "create_time": saved.get('create_time', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())),
                                "update_time": saved.get('update_time', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
                            })
                        else:
                            results.append({
                                "collection": collection,
                                "key": key,
                                "user_id": user_id,
                                "value": "{}",
                                "version": secrets.token_hex(16),
                                "permission_read": 1,
                                "permission_write": 1,
                                "create_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                                "update_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                            })
                    else:
                        results.append({
                            "collection": collection,
                            "key": key,
                            "user_id": user_id,
                            "value": "{}",
                            "version": secrets.token_hex(16),
                            "permission_read": 1,
                            "create_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                            "update_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                        })

            response_data = {"objects": results}
            print(f"[STORAGE] Returning {len(results)} objects")
        else:
            # Write operations
            objects = body.get("objects", []) if body else []
            if objects:
                updates = {}
                for obj in objects:
                    col = obj.get("collection", "")
                    key = obj.get("key", "")
                    val = obj.get("value", "")
                    if isinstance(val, (dict, list)):
                        val = json.dumps(val)

                    if col == 'user_avatar' and username:
                        try:
                            av = json.loads(val) if isinstance(val, str) else val
                            if isinstance(av, dict):
                                items = av.get('items') if isinstance(av.get('items'), list) else []
                                if not items:
                                    for fld in ('head', 'eyeLeft', 'eyeRight', 'torso', 'armLeft', 'armRight', 'butt', 'tail'):
                                        v = av.get(fld)
                                        if v:
                                            items.append(v)
                                    accs = av.get('accessories', [])
                                    if isinstance(accs, list):
                                        for a in accs:
                                            if a and a not in items:
                                                items.append(a)
                                items = replace_avatar_items_by_slot([], items)
                                av = apply_items_to_avatar_fields(av, items)
                                av = enforce_mop_hat_policy(av, is_mod)
                                av = enforce_dev_policy(av, is_dev)
                                save_user_avatar(username, {
                                    'value': json.dumps(av),
                                    'update_time': obj.get('update_time', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())),
                                    'version': obj.get('version', secrets.token_hex(8))
                                })
                        except Exception as e:
                            print(f"[STORAGE] Avatar update error: {e}")

                    if col == 'user_inventory' and key == 'stash' and username:
                        save_user_items(username, {
                            'value': val,
                            'update_time': obj.get('update_time', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())),
                            'version': obj.get('version', secrets.token_hex(8))
                        }, 'user_inventory', 'stash')

                    if col == 'user_inventory' and key == 'gameplay_loadout' and username:
                        save_user_items(username, {
                            'value': val,
                            'update_time': obj.get('update_time', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())),
                            'version': obj.get('version', secrets.token_hex(8))
                        }, 'user_inventory', 'gameplay_loadout')

                    if col == 'user_inventory' and key == 'avatar' and username:
                        save_user_items(username, {
                            'value': val,
                            'update_time': obj.get('update_time', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())),
                            'version': obj.get('version', secrets.token_hex(8))
                        }, 'user_inventory', 'avatar')

                    set_user_data_bulk(username, updates)

                response_data = {"acks": [
                    {"collection": o.get("collection"), "key": o.get("key"), "version": secrets.token_hex(16)}
                    for o in objects
                ]}
            else:
                response_data = _build_storage_objects(target_user)
    else:
        response_data = _build_storage_objects(target_user)

    response = jsonify(response_data)
    print(f"[STORAGE] Response objects: {len(response_data.get('objects', []))}")
    print("="*80 + "\n")
    return response, 200

@app.route("/3/v2/storage/econ_avatar_items", methods=["GET", "POST", "PUT"])
@app.route("/v2/storage/econ_avatar_items", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/storage/econ_avatar_items", methods=["GET", "POST", "PUT"])
def econ_avatar_items():
    username = _toast_auth()
    econ_data = get_game_data("econ_avatar_items")
    mod_list = get_mod_users()
    clean_mods = {m.strip().lower() for m in mod_list}
    is_mod = bool(username and username.strip().lower() in clean_mods) or username == MOD_USER
    filtered = []
    for item in econ_data:
        item_id = item.get('id')
        if item_id == 'acc_head_mop' and not is_mod:
            continue
        item = dict(item)
        item['unlocked'] = True
        filtered.append(item)
    return jsonify(_build_econ_objects("econ_avatar_items", filtered))

@app.route("/3/v2/storage/econ_gameplay_items", methods=["GET", "POST", "PUT"])
@app.route("/v2/storage/econ_gameplay_items", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/storage/econ_gameplay_items", methods=["GET", "POST", "PUT"])
def econ_gameplay_items():
    return jsonify(_build_econ_objects("econ_gameplay_items", get_game_data("econ_gameplay_items")))

@app.route("/3/v2/storage/econ_research_nodes", methods=["GET", "POST", "PUT"])
@app.route("/v2/storage/econ_research_nodes", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/storage/econ_research_nodes", methods=["GET", "POST", "PUT"])
def econ_research_nodes():
    return jsonify(_build_econ_objects("econ_research_nodes", get_game_data("econ_research_nodes")))

@app.route("/3/v2/storage/econ_products", methods=["GET", "POST", "PUT"])
@app.route("/v2/storage/econ_products", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/storage/econ_products", methods=["GET", "POST", "PUT"])
def econ_products():
    return jsonify(_build_econ_objects("econ_products", get_game_data("econ_products")))

@app.route("/v2/storage/econ_stash_upgrades", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/storage/econ_stash_upgrades", methods=["GET", "POST", "PUT"])
def econ_stash_upgrades():
    return jsonify(_build_econ_objects("econ_stash_upgrades", get_game_data("econ_stash_upgrades")))

@app.route("/v2/storage/econ_loot_table_bindings", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud/v2/storage/econ_loot_table_bindings", methods=["GET", "POST", "PUT"])
def econ_loot_table_bindings():
    return jsonify(_build_econ_objects("econ_loot_table_bindings", get_game_data("econ_loot_table_bindings")))

@app.route("/v2/storage/econ_loot_table", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/storage/econ_loot_table", methods=["GET", "POST", "PUT"])
def econ_loot_table():
    return jsonify(_build_econ_objects("econ_loot_table", get_game_data("econ_loot_table")))

@app.route("/v2/storage/econ_crafting_materials", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/storage/econ_crafting_materials", methods=["GET", "POST", "PUT"])
def econ_crafting_materials():
    return jsonify(_build_econ_objects("econ_crafting_materials", get_game_data("econ_crafting_materials")))

@app.route("/v2/rpc/mining.balance", methods=["POST", "GET"])
@app.route("/nnnnaakamacloud.c/v2/rpc/mining.balance", methods=["POST", "GET"])
def mining_balance():
    username = _get_username_from_request() or _toast_auth()
    if check_ban(username):
        return jsonify({"message": BAN_MESSAGE}), 401
    if username in SPECIAL_USERS:
        sp_wallet = SPECIAL_USERS[username]["wallet"]
        return jsonify({"payload": json.dumps({
            "hardCurrency": sp_wallet.get("hardCurrency", 99999999999),
            "researchPoints": sp_wallet.get("researchPoints", 99999999999),
        })})
    user_currency = get_user_currency(username) if username else {}
    return jsonify({"payload": json.dumps({
        "hardCurrency": user_currency.get('cc', 30000),
        "researchPoints": user_currency.get('rp', 40000),
    })})

@app.route("/3/v2/rpc/updateWalletSoftCurrency", methods=["POST", "GET"])
@app.route("/v2/rpc/updateWalletSoftCurrency", methods=["POST", "GET"])
def update_wallet_soft():
    username = _get_username_from_request() or _toast_auth()
    if check_ban(username):
        return jsonify({"message": BAN_MESSAGE}), 401
    if username:
        if _is_rate_limited(f"wallet:{username}", max_requests=10, window_seconds=60):
            return _rate_limit_response()
        data = request.get_json(silent=True) or {}
        amount = data.get("amount", 0)
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            amount = 0
        amount = max(-10000, min(10000, amount))
        user_currency = get_user_currency(username)
        new_nuts = max(0, user_currency.get('nuts', 20000000) + amount)
        update_user_currency(username, nuts=new_nuts)
    return jsonify({"Payload": "{\"ok\"}"})

@app.route("/3/v2/rpc/research.unlock", methods=["POST"])
@app.route("/v2/rpc/research.unlock", methods=["POST"])
@app.route("/nnnnaakamacloud.c/v2/rpc/research.unlock", methods=["POST"])
def research_unlock():
    username = _get_username_from_request() or _toast_auth()
    if check_ban(username):
        return jsonify({"message": BAN_MESSAGE}), 401
    if username:
        update_user_currency(username, rp=418291, nuts=418291, cc=418291)
    return {"payload": "{\"succeeded\":true,\"wallet\":{\"softCurrency\":418291,\"hardCurrency\":418291,\"researchPoints\":418291}}"}

@app.route("/v2/rpc/research.item", methods=["POST", "GET"])
def research_item():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"succeeded": False, "errorCode": "Unknown"})})
    all_nodes = get_all_research_node_ids() or []
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "wallet": {"softCurrency": cur.get("nuts", 9999999), "hardCurrency": cur.get("cc", 9999999), "researchPoints": cur.get("rp", 9999999)},
        "inventoryResearchNodes": all_nodes,
    })})

@app.route("/v2/rpc/research.skill", methods=["POST", "GET"])
def research_skill():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"succeeded": False, "errorCode": "Unknown"})})
    all_nodes = get_all_research_node_ids() or []
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "wallet": {"softCurrency": cur.get("nuts", 9999999), "hardCurrency": cur.get("cc", 9999999), "researchPoints": cur.get("rp", 9999999)},
        "inventoryResearchNodes": all_nodes,
    })})

@app.route("/3/v2/rpc/promo.redeem", methods=["POST", "GET"])
@app.route("/v2/rpc/promo.redeem", methods=["POST", "GET"])
def promo_redeem():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"error": "invalid token"}), 403
    if check_ban(username):
        return jsonify({"message": BAN_MESSAGE}), 401

    try:
        data = request.get_json(force=True, silent=True) or {}
        if isinstance(data, str):
            data = json.loads(data)
        raw_code = str(data.get("code", "")).strip()
        code = raw_code.lower()
    except Exception:
        code = ""
        raw_code = ""

    server_log(f"[promo.redeem] user={username} code={raw_code}")

    if code == "everything":
        all_items = get_all_avatar_item_ids() or FALLBACK_AVATAR_ITEM_IDS
        save_user_items(username, {
            'value': json.dumps({"items": all_items}),
            'update_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'version': secrets.token_hex(8)
        }, 'user_inventory', 'avatar')
        set_user_data(username, "user_inventory:avatar", json.dumps({"items": all_items}))
        update_user_currency(username, rp=9999999, nuts=9999999, cc=9999999)
        return jsonify({"payload": json.dumps({
            "stashCols": 8, "stashRows": 8, "succeeded": True,
            "wallet": {"softCurrency": 9999999, "hardCurrency": 9999999, "researchPoints": 9999999},
            "inventoryAvatarItems": all_items,
        })})

    if code.startswith('userban'):
        mod_list = get_mod_users()
        clean_mods = {m.strip().lower() for m in mod_list}
        is_mod_user = username.strip().lower() in clean_mods or username == MOD_USER
        if not is_mod_user:
            return jsonify({"payload": json.dumps({"status": "error", "message": "Only mods can use this promo"})}), 403
        target_username = code.replace('userban', '', 1).strip().lower()
        if not target_username:
            return jsonify({"payload": json.dumps({"status": "error", "message": "No target user specified"})}), 400
        banned = get_banned_users()
        if target_username not in banned:
            banned.add(target_username)
            save_banned_users(banned)
            server_log(f"[promo.redeem] User {target_username} banned by {username}")
        return jsonify({"payload": json.dumps({
            "status": "success",
            "message": f"User {target_username} banned by {username}",
            "banned_user": target_username
        })})

    if 'loadout' in code:
        is_allowed = is_user_allowed_loadout(username)
        user_currency = get_user_currency(username)
        if is_allowed:
            remove_user_from_loadout_allowlist(username)
            new_nuts = max(user_currency.get('nuts', 20000000) - 1, 0)
            update_user_currency(username, nuts=new_nuts)
            return jsonify({"payload": json.dumps({"status": "success", "message": "Loadout access disabled. Deducted 1 nut.", "new_balance": new_nuts})})
        else:
            add_user_to_loadout_allowlist(username)
            new_nuts = user_currency.get('nuts', 20000000) + 1
            update_user_currency(username, nuts=new_nuts)
            return jsonify({"payload": json.dumps({"status": "success", "message": "Loadout access enabled. Granted 1 nut.", "new_balance": new_nuts})})

    return jsonify({"payload": json.dumps({"succeeded": False, "error": "Invalid code"})}), 400

@app.route("/3/v2/rpc/avatar.update", methods=["POST", "GET"])
@app.route("/v2/rpc/avatar.update", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/rpc/avatar.update", methods=["POST"])
def avatar_update():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    if check_ban(username):
        return jsonify({"message": BAN_MESSAGE}), 401

    is_mod = str(username).strip().lower() in {m.strip().lower() for m in get_mod_users()} or username == MOD_USER
    is_dev = str(username).strip().lower() in {d.strip().lower() for d in get_dev_users()}

    body = request.get_json(silent=True, force=True)
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except Exception:
            pass

    if not body:
        return jsonify({"payload": "{\"succeeded\":true,\"errorCode\":\"\"}"})

    if isinstance(body, dict):
        avatar_keys = {'primaryColor', 'head', 'torso', 'accessories', 'butt', 'armLeft', 'armRight', 'eyeLeft', 'eyeRight'}
        if 'objects' in body and isinstance(body.get('objects'), list):
            objects = body['objects']
        elif avatar_keys & set(body.keys()):
            objects = [{'collection': 'user_avatar', 'key': '0', 'value': json.dumps(body)}]
        else:
            objects = body.get('objects', [])
    elif isinstance(body, list):
        objects = body
    else:
        objects = []

    for incoming_obj in objects:
        if isinstance(incoming_obj, str):
            try:
                incoming_obj = json.loads(incoming_obj)
            except Exception:
                continue
        if not isinstance(incoming_obj, dict):
            continue
        if incoming_obj.get('collection') == 'user_avatar' and 'value' in incoming_obj:
            try:
                av = json.loads(incoming_obj['value']) if isinstance(incoming_obj['value'], str) else incoming_obj['value']
                if isinstance(av, dict):
                    items = av.get('items') if isinstance(av.get('items'), list) else []
                    if not items:
                        for fld in ('head', 'eyeLeft', 'eyeRight', 'torso', 'armLeft', 'armRight', 'butt', 'tail'):
                            v = av.get(fld)
                            if v:
                                items.append(v)
                        accs = av.get('accessories', [])
                        if isinstance(accs, list):
                            for a in accs:
                                if a and a not in items:
                                    items.append(a)
                    items = replace_avatar_items_by_slot([], items)
                    av = apply_items_to_avatar_fields(av, items)
                    av = enforce_mop_hat_policy(av, is_mod)
                    av = enforce_dev_policy(av, is_dev)
                    save_user_avatar(username, {
                        'value': json.dumps(av),
                        'update_time': incoming_obj.get('update_time', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())),
                        'version': incoming_obj.get('version', secrets.token_hex(8))
                    })
            except Exception:
                pass

    saved_avatar = get_user_avatar(username)
    avatar_value = saved_avatar.get('value') if saved_avatar and 'value' in saved_avatar else ''
    return jsonify({"payload": "{\"succeeded\":true,\"errorCode\":\"\"}", "objects": [{"collection": "user_avatar", "key": "0", "value": avatar_value}]})

@app.route("/3/v2/rpc/purchase.avatarItems", methods=["POST", "GET"])
@app.route("/v2/rpc/purchase.avatarItems", methods=["POST", "GET"])
@app.route("/nnnnaakamacloud.c/v2/rpc/purchase.avatarItems", methods=["POST", "GET"])
def purchase_avatar_items():
    username = _toast_auth() or _get_username_from_request()
    if check_ban(username):
        return jsonify({"message": BAN_MESSAGE}), 401
    if username:
        all_items = get_all_avatar_item_ids() or FALLBACK_AVATAR_ITEM_IDS
        save_user_items(username, {
            'value': json.dumps({"items": all_items}),
            'update_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'version': secrets.token_hex(8)
        }, 'user_inventory', 'avatar')
        set_user_data(username, "user_inventory:avatar", json.dumps({"items": all_items}))
    return jsonify({"payload": ""})

@app.route("/3/v2/rpc/purchase.gameplayItems", methods=["POST", "GET"])
@app.route("/v2/rpc/purchase.gameplayItems", methods=["POST", "GET"])
@app.route("/nnnnaakamacloud.c/v2/rpc/purchase.gameplayItems", methods=["POST", "GET"])
def purchase_gameplay_items():
    username = _get_username_from_request() or _toast_auth()
    if check_ban(username):
        return jsonify({"message": BAN_MESSAGE}), 401
    if username:
        all_nodes = get_all_research_node_ids()
        if all_nodes:
            set_user_data(username, "user_inventory:research", json.dumps({"nodes": all_nodes}))
    return jsonify({"payload": ""})

@app.route("/3/v2/rpc/user.getActiveSanctions", methods=["GET"])
@app.route("/v2/rpc/user.getActiveSanctions", methods=["GET"])
@app.route("/nnnnaakamacloud.c/v2/rpc/user.getActiveSanctions", methods=["GET"])
def get_sanctions():
    return {"payload": "[]"}

@app.route("/3/v2/rpc/attest.start", methods=["POST"])
@app.route("/v2/rpc/attest.start", methods=["POST"])
@app.route("/nnnnaakamacloud.c/v2/rpc/attest.start", methods=["POST"])
def attest_start():
    body = request.get_json(silent=True) or {}
    attest_result = _verify_attestation(body)
    if attest_result is not None:
        return attest_result
    return jsonify({"payload": json.dumps({"status": "success", "attestResult": "Valid", "message": "Attestation validated"})})

@app.route("/3/v2/rpc/clientBootstrap", methods=["GET", "POST"])
@app.route("/v2/rpc/clientBootstrap", methods=["GET", "POST"])
@app.route("/nnnnaakamacloud.c/v2/rpc/clientBootstrap", methods=["GET", "POST"])
def client_bootstrap():
    payload = {
        "updateType": "None", "attestResult": "Valid",
        "attestTokenExpiresAt": 1820877961,
        "photonAppID": "",
        "photonVoiceAppID": "",
        "metadataHash": "3225b4ed43082cec01c79acd8b1c09ea335f77870663342a5dededf6f4979f66",
        "termsAcceptanceNeeded": [], "dailyMissionDateKey": "",
        "dailyMissions": None, "dailyMissionResetTime": 0,
        "serverTimeUnix": int(time.time()),
        "gameDataURL": GAME_DATA_ZIP_URL,
    }
    return json.dumps({"payload": json.dumps(payload)}), 200, {"Content-Type": "application/json"}

@app.route("/3/v2/rpc/purchase.list", methods=["GET"])
@app.route("/v2/rpc/purchase.list", methods=["GET"])
@app.route("/nnnnaakamacloud.c/v2/rpc/purchase.list", methods=["GET"])
def purchase_list():
    return {"payload": "{\"purchases\":[{\"user_id\":\"3560fe2e-015c-4d2b-b2a6-6eb9f8d6a236\",\"product_id\":\"KPOP_GOLD\",\"transaction_id\":\"716802304855579\",\"store\":3,\"purchase_time\":{\"seconds\":1754458259},\"create_time\":{\"seconds\":1754458305,\"nanos\":154543000},\"update_time\":{\"seconds\":1754458305,\"nanos\":154543000},\"refund_time\":{},\"provider_response\":\"{\\\"success\\\": true, \\\"grant_time\\\": 1754458259}\",\"environment\":2}]}"}

@app.route("/3/v2/rpc/playertracker", methods=["POST"])
@app.route("/v2/rpc/playertracker", methods=["POST"])
@app.route("/nnnnaakamacloud.c/v2/rpc/playertracker", methods=["POST"])
def player_tracker():
    username = _get_username_from_request() or _toast_auth()
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "Unknown"
    if username and _is_rate_limited(f"tracker:{username}", max_requests=20, window_seconds=60):
        return jsonify({"payload": json.dumps({"success": False, "error": "rate limited"})}), 429
    try:
        data = request.get_json(silent=True) or {}
        room_code = data.get("roomCode") or data.get("roomName") or "None"
    except Exception:
        room_code = "None"
    if username:
        track_player_join(username, client_ip, room_code)
        return jsonify({"payload": json.dumps({"success": True})}), 200
    return jsonify({"payload": json.dumps({"success": False})}), 400

@app.route("/v2/leaderboard/<leaderboard_id>", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/leaderboard/<leaderboard_id>", methods=["GET", "POST", "PUT"])
def leaderboard(leaderboard_id):
    username = _toast_auth() or _get_username_from_request()
    if request.method in ("POST", "PUT"):
        body = request.get_json(silent=True) or {}
        score = body.get("score", 0)
        metadata = body.get("metadata", {})
        if username:
            update_leaderboard_score(leaderboard_id, username, score, metadata)
    entries = get_leaderboard(leaderboard_id)
    formatted = []
    for i, entry in enumerate(entries):
        formatted.append({
            "rank": i + 1,
            "score": entry.get("score", 0),
            "username": entry.get("username", ""),
            "metadata": entry.get("metadata", {}),
            "update_time": entry.get("update_time", 0),
        })
    return jsonify({"payload": json.dumps({
        "leaderboardId": leaderboard_id,
        "entries": formatted,
        "status": "success"
    })})

@app.route("/v2/leaderboard/<leaderboard_id>/owner/<owner_id>", methods=["GET", "POST", "PUT"])
@app.route("/nnnnaakamacloud.c/v2/leaderboard/<leaderboard_id>/owner/<owner_id>", methods=["GET", "POST", "PUT"])
def leaderboard_owner(leaderboard_id, owner_id):
    entries = get_leaderboard(leaderboard_id)
    user_entry = next((e for e in entries if e.get("username", "").lower() == owner_id.lower()), None)
    rank = next((i + 1 for i, e in enumerate(entries) if e.get("username", "").lower() == owner_id.lower()), None)
    return jsonify({"payload": json.dumps({
        "leaderboardId": leaderboard_id,
        "ownerId": owner_id,
        "rank": rank,
        "entry": user_entry,
        "status": "success"
    })})

@app.route("/v2/rpc/leaderboard.submit", methods=["POST"])
@app.route("/nnnnaakamacloud.c/v2/rpc/leaderboard.submit", methods=["POST"])
def leaderboard_submit():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    leaderboard_id = body.get("leaderboardId", "global")
    score = body.get("score", 0)
    metadata = body.get("metadata", {})
    update_leaderboard_score(leaderboard_id, username, score, metadata)
    return jsonify({"payload": json.dumps({"success": True})})

@app.route("/v2/account/profile/<target_username>", methods=["GET", "POST"])
def get_user_profile(target_username):
    target_username = str(target_username).strip()
    color_entry = get_user_color(target_username)
    display_username = format_display_username(target_username, color_entry) if color_entry else target_username
    saved_avatar = get_user_avatar(target_username)
    avatar_value = saved_avatar.get('value') if saved_avatar and 'value' in saved_avatar else ''
    user_currency = get_user_currency(target_username)
    return jsonify({
        'user': {
            'id': secrets.token_hex(16),
            'username': display_username,
            'lang_tag': 'en',
            'metadata': json.dumps({'isDeveloper': False}),
            'edge_count': 4,
            'create_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'update_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        },
        'wallet': json.dumps({
            "stashCols": 8, "stashRows": 8,
            "hardCurrency": user_currency.get('cc', 20000000),
            "softCurrency": user_currency.get('nuts', 20000000),
            "researchPoints": user_currency.get('rp', 20000000)
        }),
        'avatar': avatar_value,
        'custom_id': secrets.token_hex(16)
    })

@app.route("/v2/account/color", methods=["POST"])
def set_account_color():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Missing payload"}), 400
    target_username = (data.get("username") or "").strip()
    color = data.get("color")
    display = data.get("display")
    if not target_username or not color:
        return jsonify({"error": "missing username or color"}), 400
    auth_user = _toast_auth()
    mod_list = {m.strip().lower() for m in get_mod_users()}
    if not (auth_user and (auth_user.strip().lower() in mod_list or auth_user == MOD_USER)):
        return jsonify({"error": "Not allowed"}), 403
    set_user_color(target_username, color, display)
    return jsonify({"result": "ok"})

@app.route("/v2/account/color/<target_username>", methods=["DELETE"])
def delete_account_color(target_username):
    auth_user = _toast_auth()
    mod_list = {m.strip().lower() for m in get_mod_users()}
    if not (auth_user and (auth_user.strip().lower() in mod_list or auth_user == MOD_USER)):
        return jsonify({"error": "Not allowed"}), 403
    remove_user_color(target_username)
    return jsonify({"result": "ok"})

@app.route("/loadout", methods=["GET", "POST"])
def loadout_editor():
    session_user = flask_session.get("username")
    if request.method == "GET":
        if session_user and not is_user_allowed_loadout(session_user):
            return '''<html><body style="font-family:Arial,sans-serif;background:#111;color:#fff;padding:30px;">
            <h2>Loadout Access Denied</h2>
            <p>Your account is not enrolled for the Loadout feature. To enroll, enter the promo code <strong>loadout</strong> in-game.</p>
            </body></html>'''
        return '''<!DOCTYPE html><html><head><title>Loadout Editor</title>
        <style>body{font-family:Arial,sans-serif;max-width:600px;margin:50px auto;padding:20px;background:#1a1a1a;color:#fff}
        .container{background:#2a2a2a;padding:30px;border-radius:10px}h1{color:#00ff88;text-align:center}
        label{display:block;margin-top:15px;font-weight:bold}input,textarea{width:100%;padding:10px;margin-top:5px;border:1px solid #444;background:#1a1a1a;color:#fff;border-radius:5px;box-sizing:border-box}
        button{background:#00ff88;color:#000;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;font-weight:bold;margin-top:20px;width:100%;font-size:16px}</style></head>
        <body><div class="container"><h1>🎒 Loadout Editor</h1>
        <form method="POST" enctype="multipart/form-data">
        <label>Username:</label><input type="text" name="username" required placeholder="Enter your username">
        <label>Upload Loadout JSON:</label><input type="file" name="jsonfile" accept=".json">
        <label>Or paste JSON:</label><textarea name="jsontext" rows="10" placeholder="Paste your loadout JSON here..."></textarea>
        <button type="submit">Upload Loadout</button></form></div></body></html>'''
    elif request.method == "POST":
        try:
            submit_username = session_user or request.form.get("username", "").strip()
            if not submit_username:
                return jsonify({"error": "Username is required"}), 400
            if not is_user_allowed_loadout(submit_username):
                return jsonify({"error": "not_allowed", "message": "Redeem the loadout promo first."}), 403
            json_data = None
            if "jsonfile" in request.files:
                file = request.files["jsonfile"]
                if file.filename:
                    json_data = json.load(file.stream)
            if json_data is None and request.form.get("jsontext"):
                json_data = json.loads(request.form.get("jsontext"))
            if not json_data:
                return jsonify({"error": "No JSON provided"}), 400
            if isinstance(json_data, dict) and "value" in json_data:
                item_data = {
                    "value": json_data.get("value"),
                    "update_time": json_data.get("update_time", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                    "version": json_data.get("version", secrets.token_hex(8))
                }
            else:
                item_data = {
                    "value": json.dumps(json_data) if isinstance(json_data, dict) else json_data,
                    "update_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "version": secrets.token_hex(8)
                }
            key = "stash" if (isinstance(json_data, dict) and "items" in json_data) else "gameplay_loadout"
            save_user_items(submit_username, item_data, "user_inventory", key)
            server_log(f"Loadout uploaded for user {submit_username}: key={key}")
            return f"<html><body style='background:#111;color:#fff;font-family:Arial;text-align:center;padding:50px'><h2 style='color:#00ff88'>✓ Loadout uploaded successfully for {submit_username}!</h2><a href='/loadout' style='color:#00ff88'>← Upload another</a></body></html>", 200
        except json.JSONDecodeError as e:
            return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400
        except Exception as e:
            return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/auth", methods=["GET", "POST"])
def photon_auth_endpoint():
    auth_token = request.args.get("auth_token")
    fake_user_id = secrets.token_hex(16)
    fake_session_id = secrets.token_hex(12)
    return jsonify({"ResultCode": 1, "Message": "Authenticated", "UserId": fake_user_id, "SessionID": fake_session_id, "Authenticated": True}), 200

ADMIN_SECRET = "heheheha"

def _admin_auth():
    return request.headers.get("Authorization") == ADMIN_SECRET

@app.route("/banned", methods=["GET"])
def read_banned():
    if not _admin_auth():
        return jsonify({"error": "forbidden"}), 403
    return jsonify(sorted(list(get_banned_users())))

@app.route("/ban", methods=["POST"])
def ban_user():
    if not _admin_auth():
        return jsonify({"error": "forbidden"}), 403
    username = request.json.get("username")
    if not username:
        return jsonify({"error": "missing username"}), 400
    banned = get_banned_users()
    if username.lower() not in banned:
        banned.add(username.lower())
        save_banned_users(banned)
        server_log(f"User banned: {username}")
    return jsonify({"ok": True})

@app.route("/unban", methods=["POST"])
def unban_user():
    if not _admin_auth():
        return jsonify({"error": "forbidden"}), 403
    username = request.json.get("username")
    if not username:
        return jsonify({"error": "missing username"}), 400
    banned = get_banned_users()
    if username.lower() in banned:
        banned.discard(username.lower())
        save_banned_users(banned)
        server_log(f"User unbanned: {username}")
    return jsonify({"ok": True})

@app.route("/test")
def test():
    return "server ok"

@app.route("/debug", methods=["GET", "POST", "PUT"])
def debug():
    method = request.method
    url = request.url
    headers = dict(request.headers)
    body = request.get_data(as_text=True)
    return jsonify({"method": method, "url": url, "headers": headers, "body": body}), 200

@app.route("/debug_headers")
def debug_headers():
    return jsonify(dict(request.headers))

@app.route("/v2/rpc/bulkuserdatafetch", methods=["GET", "POST"])
def bulkuserdatafetch():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    user_color = get_user_color(username)
    user_avatar = get_user_avatar(username)
    user_currency = get_user_currency(username)
    return jsonify({
        "status": "success",
        "user": {
            "username": username,
            "color": user_color,
            "avatar": user_avatar.get("value") if user_avatar else "",
            "currency": user_currency
        }
    }), 200

@app.route("/v2/user/status", methods=["GET", "POST"])
def get_user_status():
    username = request.args.get("username") or (request.get_json(force=True, silent=True) or {}).get("username")
    if not username:
        return jsonify({"error": "Missing username parameter"}), 400
    sessions = {}
    try:
        sessions_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_sessions.json")
        if os.path.exists(sessions_path):
            with open(sessions_path, "r", encoding="utf-8") as f:
                sessions = json.load(f)
    except Exception:
        pass
    session_data = sessions.get(str(username).strip().lower())
    if not session_data:
        return jsonify({"username": username, "online": False, "lobby_id": None, "last_seen": None}), 200
    return jsonify({
        "username": session_data.get("username"),
        "online": session_data.get("online", False),
        "lobby_id": session_data.get("lobby_id"),
        "last_seen": session_data.get("last_seen")
    }), 200

@app.route("/ws", methods=["GET"])
def handle_ws():
    token = request.args.get("token")
    if token:
        try:
            parts = token.split(".")
            if len(parts) == 3:
                payload = parts[1] + "=" * (-len(parts[1]) % 4)
                decoded = base64.urlsafe_b64decode(payload).decode("utf-8")
                return jsonify({"status": "success", "decoded": json.loads(decoded)}), 200
            return jsonify({"status": "error", "message": "Invalid token format"}), 400
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
    return jsonify({"status": "error", "message": "No token provided"}), 400

@app.route("/v2/account/authenticate/steam", methods=["POST", "GET"])
def authenticate_steam():
    body = request.get_json(silent=True) or {}
    vars_ = body.get("vars", {})
    device_id = vars_.get("deviceID", "") or body.get("id", "") or request.args.get("id", "")
    username = request.args.get("username", "") or body.get("username", f"Player{secrets.token_hex(3).upper()}")
    if not username:
        username = f"Player{secrets.token_hex(3).upper()}"
    flask_session['username'] = username
    return BearerGeneration(username)

@app.route("/v2/account/authenticate/email", methods=["POST", "GET"])
def authenticate_email():
    body = request.get_json(silent=True) or {}
    email = body.get("email", "") or request.args.get("email", "")
    username = request.args.get("username", "") or body.get("username", f"Player{secrets.token_hex(3).upper()}")
    if not username:
        username = f"Player{secrets.token_hex(3).upper()}"
    flask_session['username'] = username
    return BearerGeneration(username)

@app.route("/v2/session/logout", methods=["POST"])
def session_logout():
    flask_session.clear()
    return jsonify({})

@app.route("/v2/account/unlink/device", methods=["POST"])
def unlink_device():
    return jsonify({})

@app.route("/v2/account/delete", methods=["POST", "DELETE"])
def delete_account():
    return jsonify({})

@app.route("/v2/user", methods=["GET"])
@app.route("/v2/users", methods=["GET"])
def get_users():
    return jsonify({"users": []})

@app.route("/v2/rpc/user.getFeatureFlags", methods=["GET", "POST"])
def feature_flags():
    return jsonify({"payload": json.dumps({
        "enableDailyMissions": True,
        "uniqueObjects": True,
        "voiceModService": "",
        "goopLoadoutSaving": True,
        "metaCameraEnabled": True,
    })})

@app.route("/v2/rpc/user.getVRPresence", methods=["GET", "POST"])
def presence_get_current():
    return jsonify({"payload": json.dumps({
        "presence": {"roomCode": "", "gameMode": 0, "appearOffline": False, "clientVersion": "", "photonVersion": ""},
        "errorCode": 0,
    })})

@app.route("/v2/storage", methods=["GET"])
def storage_get():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"error": "unauthorized"}), 401
    udata = get_all_user_data(username)
    objects = _build_user_objects(username, udata).get("objects", [])
    return jsonify({"objects": objects})

@app.route("/v2/storage", methods=["PUT"])
def storage_write_bulk():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"error": "unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    objects = body.get("objects", [])
    acks = []
    for obj in objects:
        coll = obj.get("collection", "")
        key = obj.get("key", "")
        value = obj.get("value", "{}")
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        ver = secrets.token_hex(8)
        save_user_items(username, {
            "value": value,
            "update_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "version": ver
        }, coll, key)
        acks.append({"collection": coll, "key": key, "version": ver})
    return jsonify({"acks": acks})

@app.route("/v2/storage", methods=["DELETE"])
def storage_delete():
    return jsonify({})

@app.route("/v2/storage/<collection>", methods=["GET"])
def storage_get_collection(collection):
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"error": "unauthorized"}), 401
    item = get_user_items(username, collection, collection)
    if item:
        return jsonify({"objects": [item]})
    return jsonify({"objects": []})

@app.route("/v2/storage/<collection>/<uid_param>", methods=["GET"])
def storage_list_user(collection, uid_param):
    item = get_user_items(uid_param, collection, collection)
    if item:
        return jsonify({"objects": [item]})
    return jsonify({"objects": []})

@app.route("/v2/rpc/GetBulkUserData", methods=["GET", "POST"])
@app.route("/v2/rpc/getBulkUserData", methods=["GET", "POST"])
def get_bulk_user_data():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": "{}"})
    udata = get_all_user_data(username)
    objs = _build_user_objects(username, udata).get("objects", [])

    def _read(coll, key, default):
        for o in objs:
            if o.get("collection") == coll and o.get("key") == key:
                try:
                    return json.loads(o["value"])
                except Exception:
                    return default
        return default

    result = {
        "avatar": _read("user_avatar", "0", {}),
        "avatarInventory": _read("user_inventory", "avatar", {"items": []}),
        "researchInventory": _read("user_inventory", "research", {"nodes": []}),
        "stash": _read("user_inventory", "stash", {"items": [], "materials": [], "stashPos": 0, "version": 1}),
        "upgradesInventory": _read("user_inventory", "upgrades", {"upgrades": []}),
        "loadout": _read("user_inventory", "gameplay_loadout", {"version": 1}),
        "loadoutTemplates": _read("user_inventory", "loadout_templates", []),
        "blueprints": _read("user_inventory", "blueprints", []),
        "gameplayItemPreferences": _read("user_preferences", "gameplay_items", {"recents": [], "favorites": []}),
        "preferences": _read("user_preferences", "settings", {}),
        "questSystemProgress": {"version": 1, "completed": []},
        "skillsPreferences": _read("user_preferences", "skills", {"disabledSkills": []}),
        "fishingInventory": _read("user_inventory", "fishing", {"baitSystemUnlocked": False, "rods": [], "fish": {}, "baits": {}}),
    }
    return jsonify({"payload": json.dumps(result)})

@app.route("/v2/rpc/avatar.getAvatars", methods=["POST", "GET"])
@app.route("/v2/rpc/avatar.get", methods=["POST", "GET"])
def avatar_get_avatars():
    body = request.get_json(silent=True) or {}
    payload_raw = body.get("payload", body)
    if isinstance(payload_raw, str):
        try:
            payload_raw = json.loads(payload_raw)
        except Exception:
            payload_raw = {}
    user_ids = payload_raw.get("userIDs", [])
    result_ids, result_avatars = [], []
    for uid in user_ids:
        av = get_user_avatar(uid)
        if av:
            result_ids.append(uid)
            try:
                result_avatars.append(json.loads(av["value"]) if isinstance(av.get("value"), str) else av)
            except Exception:
                result_avatars.append({})
    return jsonify({"payload": json.dumps({"userIDs": result_ids, "avatars": result_avatars})})

@app.route("/v2/rpc/mining.collect", methods=["POST", "GET"])
def mining_collect():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"succeeded": False, "errorCode": "Unknown"})})
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "balance": {"hardCurrency": float(cur.get("cc", 9999999)), "researchPoints": float(cur.get("rp", 9999999))},
        "wallet": {"softCurrency": cur.get("nuts", 9999999), "hardCurrency": cur.get("cc", 9999999), "researchPoints": cur.get("rp", 9999999)},
    })})

@app.route("/v2/rpc/mining.sell", methods=["POST", "GET"])
def mining_sell():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"succeeded": False, "errorCode": "Unknown"})})
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "wallet": {"softCurrency": cur.get("nuts", 9999999), "hardCurrency": cur.get("cc", 9999999), "researchPoints": cur.get("rp", 9999999)},
    })})

@app.route("/v2/rpc/store.buy", methods=["POST", "GET"])
def store_buy():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"succeeded": False, "errorCode": "Unknown"})})
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "wallet": {"softCurrency": cur.get("nuts", 9999999), "hardCurrency": cur.get("cc", 9999999), "researchPoints": cur.get("rp", 9999999)},
    })})

@app.route("/v2/rpc/store.buyAvatar", methods=["POST", "GET"])
def store_buy_avatar():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"succeeded": False, "errorCode": "Unknown"})})
    cur = get_user_currency(username)
    all_items = get_all_avatar_item_ids() or FALLBACK_AVATAR_ITEM_IDS
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "wallet": {"softCurrency": cur.get("nuts", 9999999), "hardCurrency": cur.get("cc", 9999999), "researchPoints": cur.get("rp", 9999999)},
        "inventoryAvatarItems": all_items,
    })})

@app.route("/v2/rpc/wallet.update", methods=["POST", "GET"])
def wallet_update():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"succeeded": False, "errorCode": "Unknown"})})
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({
        "softCurrency": cur.get("nuts", 9999999),
        "hardCurrency": cur.get("cc", 9999999),
        "researchPoints": cur.get("rp", 9999999),
    })})

@app.route("/v2/rpc/updateWalletSoftCurrency", methods=["POST", "GET"])
@app.route("/v2/rpc/updateWalletHardCurrency", methods=["POST", "GET"])
@app.route("/v2/rpc/updateWalletResearchPoints", methods=["POST", "GET"])
def update_wallet_currency():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": "{}"})
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({
        "softCurrency": cur.get("nuts", 9999999),
        "hardCurrency": cur.get("cc", 9999999),
        "researchPoints": cur.get("rp", 9999999),
    })})

@app.route("/v2/rpc/nuts.getWallet", methods=["GET", "POST"])
def nuts_get_wallet():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"success": False, "balance": 0})})
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({"success": True, "balance": cur.get("nuts", 9999999)})})

@app.route("/v2/rpc/fishing.getWallet", methods=["GET", "POST"])
def fish_get_wallet():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"success": False, "balance": 0})})
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({"success": True, "balance": cur.get("fish", 9999999)})})

@app.route("/v2/rpc/fishing.updateBalance", methods=["POST", "GET"])
def fish_update_wallet():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"success": False, "balance": 0})})
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({"success": True, "balance": cur.get("fish", 9999999)})})

@app.route("/v2/rpc/fishing.saveInventory", methods=["POST", "GET"])
def fish_save_inventory():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": "{}"})
    body = request.get_json(silent=True) or {}
    payload_raw = body.get("payload", body)
    if isinstance(payload_raw, str):
        try:
            payload_raw = json.loads(payload_raw)
        except Exception:
            payload_raw = {}
    save_user_items(username, {
        "value": json.dumps(payload_raw),
        "update_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": secrets.token_hex(8)
    }, "user_inventory", "fishing")
    return jsonify({"payload": "{}"})

@app.route("/v2/rpc/purchase.researchPoints", methods=["POST", "GET"])
def purchase_research_points():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"succeeded": False, "errorCode": "Unknown"})})
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "wallet": {"softCurrency": cur.get("nuts", 9999999), "hardCurrency": cur.get("cc", 9999999), "researchPoints": cur.get("rp", 9999999)},
    })})

@app.route("/v2/rpc/purchase.upgrade", methods=["POST", "GET"])
@app.route("/v2/rpc/stash.upgrade", methods=["POST", "GET"])
@app.route("/v2/rpc/purchase.stashUpgrade", methods=["POST", "GET"])
def purchase_upgrade():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": json.dumps({"succeeded": False, "errorCode": "Unknown"})})
    cur = get_user_currency(username)
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "stashCols": 8, "stashRows": 8,
        "wallet": {"softCurrency": cur.get("nuts", 9999999), "hardCurrency": cur.get("cc", 9999999), "researchPoints": cur.get("rp", 9999999)},
        "inventoryUpgrades": [],
    })})

@app.route("/v2/rpc/quest.complete", methods=["POST", "GET"])
def quests_complete():
    return jsonify({"payload": json.dumps({"version": 1, "completed": []})})

@app.route("/v2/rpc/dailyMission.schedule", methods=["GET", "POST"])
def daily_missions_get_schedule():
    from datetime import timedelta
    now = int(time.time())
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return jsonify({"payload": json.dumps({
        "dailyMissionDateKey": today,
        "dailyMissions": ["daily_reward", "daily_sell_items", "daily_kill_monsters"],
        "dailyMissionResetTime": int(tomorrow.timestamp()),
        "currentTime": now,
    })})

@app.route("/v2/rpc/dailyMission.getData", methods=["POST", "GET"])
def daily_missions_get_data():
    body = request.get_json(silent=True) or {}
    payload_raw = body.get("payload", body)
    if isinstance(payload_raw, str):
        try:
            payload_raw = json.loads(payload_raw)
        except Exception:
            payload_raw = {}
    mission_ids = payload_raw.get("missionIDs", [])
    missions = [{
        "id": mid,
        "name": mid.replace("_", " ").title(),
        "description": f"Complete the {mid} mission",
        "rewardHard": 50,
        "rewardResearchPoints": 5,
        "taskType": "DailyReward",
        "args": [],
    } for mid in mission_ids]
    return jsonify({"payload": json.dumps({"missions": missions})})

@app.route("/v2/rpc/dailyMission.progress", methods=["POST", "GET"])
def daily_missions_get_progress():
    return jsonify({"payload": json.dumps({"progress": []})})

@app.route("/v2/rpc/dailyMission.reportProgress", methods=["POST", "GET"])
def daily_missions_report_progress():
    return jsonify({"payload": json.dumps({"succeeded": True, "errorCode": "None"})})

@app.route("/v2/rpc/dailyMission.collect", methods=["POST", "GET"])
def daily_missions_collect_reward():
    username = _toast_auth() or _get_username_from_request()
    cur = get_user_currency(username) if username else {}
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "wallet": {"softCurrency": cur.get("nuts", 9999999), "hardCurrency": cur.get("cc", 9999999), "researchPoints": cur.get("rp", 9999999)},
        "rewardHardCurrency": 50,
        "rewardResearchPoints": 5,
    })})

@app.route("/v2/rpc/scavengerHunt.progress", methods=["POST", "GET"])
def scavenger_hunt_get_progress():
    return jsonify({"payload": json.dumps({"itemIDs": [], "completed": False, "collected": False})})

@app.route("/v2/rpc/scavengerHunt.reportProgress", methods=["POST", "GET"])
@app.route("/v2/rpc/scavengerHunt.report", methods=["POST", "GET"])
def scavenger_hunt_report_progress():
    username = _toast_auth() or _get_username_from_request()
    cur = get_user_currency(username) if username else {}
    return jsonify({"payload": json.dumps({
        "succeeded": True, "completed": False, "errorCode": "None",
        "wallet": {"softCurrency": cur.get("nuts", 9999999), "hardCurrency": cur.get("cc", 9999999), "researchPoints": cur.get("rp", 9999999)},
        "rewardHardCurrency": 0,
    })})

@app.route("/v2/rpc/scavengerHunt.collect", methods=["POST", "GET"])
def scavenger_hunt_collect_reward():
    username = _toast_auth() or _get_username_from_request()
    cur = get_user_currency(username) if username else {}
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "wallet": {"softCurrency": cur.get("nuts", 9999999), "hardCurrency": cur.get("cc", 9999999), "researchPoints": cur.get("rp", 9999999)},
        "rewardHardCurrency": 100,
        "rewardResearchPoints": 10,
    })})

@app.route("/v2/rpc/privateRooms.get", methods=["POST", "GET"])
def private_room_get():
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "privateRoom": {"code": "", "expiresAt": 0, "owner": "", "members": [], "settings": {}},
        "bannedUsers": [],
    })})

@app.route("/v2/rpc/privateRooms.purchase", methods=["POST", "GET"])
def private_room_purchase():
    body = request.get_json(silent=True) or {}
    payload_raw = body.get("payload", body)
    if isinstance(payload_raw, str):
        try:
            payload_raw = json.loads(payload_raw)
        except Exception:
            payload_raw = {}
    room_code = payload_raw.get("roomCode", secrets.token_hex(4).upper())
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "privateRoom": {"code": room_code, "expiresAt": int(time.time()) + 2592000, "owner": "", "members": [], "settings": {}},
        "bannedUsers": [],
    })})

@app.route("/v2/rpc/privateRooms.update", methods=["POST", "GET"])
@app.route("/v2/rpc/privateRooms.addMember", methods=["POST", "GET"])
@app.route("/v2/rpc/privateRooms.removeMember", methods=["POST", "GET"])
@app.route("/v2/rpc/privateRooms.kickUser", methods=["POST", "GET"])
@app.route("/v2/rpc/privateRooms.banUser", methods=["POST", "GET"])
def private_room_ops():
    return jsonify({"payload": json.dumps({
        "succeeded": True, "errorCode": "None",
        "privateRoom": {"code": "", "expiresAt": 0, "owner": "", "members": [], "settings": {}},
        "bannedUsers": [],
    })})

@app.route("/v2/rpc/report.user", methods=["POST", "GET"])
def report_user():
    return jsonify({"payload": "{}"})

@app.route("/v2/rpc/room.ban", methods=["POST", "GET"])
def room_ban_user():
    return jsonify({"payload": "{}"})

@app.route("/v2/rpc/mobile.getPairingCode", methods=["GET", "POST"])
def mobile_get_pairing_code():
    now = int(time.time())
    return jsonify({"payload": json.dumps({"pairingCode": secrets.token_hex(4).upper(), "expiresAt": now + 300, "errorCode": 0})})

@app.route("/v2/rpc/mobile.startLinkDevice", methods=["POST", "GET"])
def mobile_start_link():
    now = int(time.time())
    return jsonify({"payload": json.dumps({"verificationCode": secrets.token_hex(3).upper(), "expiresAt": now + 300})})

@app.route("/v2/rpc/mobile.confirmLinkDevice", methods=["POST", "GET"])
def mobile_confirm_link():
    return jsonify({"payload": json.dumps({})})

@app.route("/v2/rpc/mobile.finishLinkDevice", methods=["POST", "GET"])
def mobile_finish_link():
    username = _toast_auth() or _get_username_from_request()
    now = int(time.time())
    return jsonify({"payload": json.dumps({
        "deviceID": secrets.token_hex(8),
        "secret": secrets.token_hex(16),
        "password": secrets.token_hex(16),
        "expiresAt": now + 31536000,
        "userID": username or "",
        "username": username or "",
    })})

@app.route("/v2/rpc/mobile.abortLinkDevice", methods=["POST", "GET"])
def mobile_abort_link():
    return jsonify({"payload": json.dumps({"errorCode": 0})})

@app.route("/v2/friend", methods=["GET"])
@app.route("/v2/friends", methods=["GET"])
def list_friends():
    return jsonify({"friends": [], "cursor": ""})

@app.route("/v2/friend", methods=["POST"])
def add_friends():
    return jsonify({})

@app.route("/v2/friend", methods=["DELETE"])
@app.route("/v2/friend/block", methods=["POST"])
def manage_friends():
    return jsonify({})

@app.route("/v2/notification", methods=["GET"])
def list_notifications():
    return jsonify({"notifications": [], "cacheable_cursor": ""})

@app.route("/v2/notification", methods=["DELETE"])
def delete_notifications():
    return jsonify({})

@app.route("/v2/rpc/purchase.validate", methods=["POST", "GET"])
@app.route("/v2/rpc/purchase.metaQuest", methods=["POST", "GET"])
@app.route("/v2/rpc/purchase.validateMetaQuest", methods=["POST", "GET"])
def purchase_validate():
    username = _toast_auth() or _get_username_from_request()
    body = request.get_json(silent=True) or {}
    payload_raw = body.get("payload", body)
    if isinstance(payload_raw, str):
        try:
            payload_raw = json.loads(payload_raw)
        except Exception:
            payload_raw = {}
    transaction_id = (payload_raw.get("id") or payload_raw.get("transactionId") or payload_raw.get("ID") or secrets.token_hex(8))
    return jsonify({"payload": json.dumps({"valid": True, "newPurchase": True, "id": transaction_id})})

@app.route("/v2/rpc/AntiCheatCheck", methods=["POST"])
def anti_cheat_check():
    return jsonify({"payload": json.dumps({})})

@app.route("/v2/rpc/attest.check", methods=["POST"])
def attest_check():
    now = int(time.time())
    return jsonify({"payload": json.dumps({"isValid": True, "expiresAt": now + 36000})})

@app.route("/v2/rpc/preferences.get", methods=["GET", "POST"])
def preferences_get():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": "{}"})
    item = get_user_items(username, "user_preferences", "settings")
    val = item.get("value", "{}") if item else "{}"
    return jsonify({"payload": val})

@app.route("/v2/rpc/preferences.set", methods=["POST", "GET"])
def preferences_set():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": "{}"})
    body = request.get_json(silent=True) or {}
    payload_raw = body.get("payload", body)
    if isinstance(payload_raw, str):
        try:
            payload_raw = json.loads(payload_raw)
        except Exception:
            payload_raw = {}
    save_user_items(username, {
        "value": json.dumps(payload_raw),
        "update_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": secrets.token_hex(8)
    }, "user_preferences", "settings")
    return jsonify({"payload": "{}"})

@app.route("/v2/rpc/preferences.getGameplayItems", methods=["GET", "POST"])
def preferences_get_gameplay_items():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": "{}"})
    item = get_user_items(username, "user_preferences", "gameplay_items")
    val = item.get("value", json.dumps({"recents": [], "favorites": []})) if item else json.dumps({"recents": [], "favorites": []})
    return jsonify({"payload": val})

@app.route("/v2/rpc/preferences.setGameplayItems", methods=["POST", "GET"])
def preferences_set_gameplay_items():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": "{}"})
    body = request.get_json(silent=True) or {}
    payload_raw = body.get("payload", body)
    if isinstance(payload_raw, str):
        try:
            payload_raw = json.loads(payload_raw)
        except Exception:
            payload_raw = {}
    save_user_items(username, {
        "value": json.dumps(payload_raw),
        "update_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": secrets.token_hex(8)
    }, "user_preferences", "gameplay_items")
    return jsonify({"payload": "{}"})

@app.route("/v2/rpc/preferences.getSkills", methods=["GET", "POST"])
def preferences_get_skills():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": "{}"})
    item = get_user_items(username, "user_preferences", "skills")
    val = item.get("value", json.dumps({"disabledSkills": []})) if item else json.dumps({"disabledSkills": []})
    return jsonify({"payload": val})

@app.route("/v2/rpc/preferences.setSkills", methods=["POST", "GET"])
def preferences_set_skills():
    username = _toast_auth() or _get_username_from_request()
    if not username:
        return jsonify({"payload": "{}"})
    body = request.get_json(silent=True) or {}
    payload_raw = body.get("payload", body)
    if isinstance(payload_raw, str):
        try:
            payload_raw = json.loads(payload_raw)
        except Exception:
            payload_raw = {}
    save_user_items(username, {
        "value": json.dumps(payload_raw),
        "update_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": secrets.token_hex(8)
    }, "user_preferences", "skills")
    return jsonify({"payload": "{}"})

@app.route("/game-data-prod.zip", methods=["GET"])
def game_data_prod():
    game_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game-data-prod.zip")
    if os.path.exists(game_data_path):
        return send_file(game_data_path, mimetype="application/zip")
    return jsonify({"error": "not found"}), 404

@app.route("/v2/rpc/<path:rpc_id>", methods=["GET", "POST"])
def rpc_catchall(rpc_id):
    server_log(f"[RPC] Unhandled: {rpc_id} body={request.get_data(as_text=True)[:300]}")
    return jsonify({"payload": "{}"})

@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Not Found", "path": request.path, "status": 404}), 404

if __name__ == "__main__":
    print("Animal Company Server Started on port 7080")
    app.run(host="0.0.0.0", port=7080)
