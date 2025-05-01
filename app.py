from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.json_format import MessageToJson
import like_pb2
import like_count_pb2
import uid_generator_pb2
from google.protobuf.message import DecodeError
import binascii
import aiohttp
import asyncio
import json
import requests
import time
from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
import os
from datetime import datetime, timedelta
import re

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Now, securely get the bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")


COOLDOWN_FILE = "cooldown.json"

def load_cooldowns():
    if os.path.exists(COOLDOWN_FILE):
        with open(COOLDOWN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cooldowns(data):
    with open(COOLDOWN_FILE, "w") as f:
        json.dump(data, f)

def is_on_cooldown(uid):
    cooldowns = load_cooldowns()
    now = datetime.now()
    if uid in cooldowns:
        last_time = datetime.fromisoformat(cooldowns[uid])
        if now - last_time < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last_time)
            return True, str(remaining).split('.')[0]  # HH:MM:SS
    return False, None

def update_cooldown(uid):
    cooldowns = load_cooldowns()
    cooldowns[uid] = datetime.now().isoformat()
    save_cooldowns(cooldowns)

async def jwt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Inform user about the usage and directly start fetching JWT tokens
    await update.message.reply_text("Fetching JWT tokens...")

    # Load accounts from backup.json
    with open("backup.json", "r") as f:
        accounts = json.load(f)

    # Initialize an empty list to store the results
    results = []

    # Loop through each account and fetch JWT token
    for account in accounts:
        uid = account.get("uid")
        password = account.get("password")

        if not uid or not password:
            print("Missing uid or password, skipping...")
            continue

        url = f"https://jwt-by-zeus.vercel.app/gen_jwt?uid={uid}&password={password}"
        try:
            response = requests.get(url)
            if response.ok:
                # Use regex to extract the token value between '\"token\":\"' and '\",\"uid\"'
                match = re.search(r'\"token\":\"(.*?)\",\"uid\"', response.text.strip())

                if match:
                    # Extracted token
                    token = match.group(1)
                    results.append({"token": token})
                    print(f"[{uid}] JWT: {token}")
                else:
                    print(f"[{uid}] Token not found in response.")
            else:
                print(f"[{uid}] Failed: {response.status_code}")
        except Exception as e:
            print(f"[{uid}] Error: {e}")

    # Save the results to token_ind.json in the requested format
    with open("token_ind.json", "w") as f:
        json.dump(results, f, indent=4)

    # Notify user of successful operation
    await update.message.reply_text("JWT tokens generated and saved as token_ind.json.")





def load_tokens():
    try:
        with open("token_ind.json", "r") as f:
            tokens = json.load(f)
        # Ensure the file contains a list of tokens
        if isinstance(tokens, list):
            return tokens
        else:
            print("Loaded data is not in list format.")
            return []
    except Exception as e:
        print(f"Error loading tokens: {e}")
        return []


def encrypt_message(plaintext):
    try:
        key = b'Yg&tc%DEuh6%Zc^8'
        iv = b'6oyZDr22E3ychjM%'
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_message = pad(plaintext, AES.block_size)
        encrypted_message = cipher.encrypt(padded_message)
        return binascii.hexlify(encrypted_message).decode('utf-8')
    except Exception as e:
        print(f"Error encrypting message: {e}")
        return None


def create_protobuf_message(user_id):
    try:
        message = like_pb2.like()
        message.uid = int(user_id)
        message.region = "IND"
        return message.SerializeToString()
    except Exception as e:
        print(f"Error creating protobuf message: {e}")
        return None


async def send_request(encrypted_uid, token, url):
    try:
        edata = bytes.fromhex(encrypted_uid)
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; Redmi Note 8 Pro Build/RP1A.200720.011)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Authorization': f"Bearer {token}",
            'Content-Type': "application/x-www-form-urlencoded",
            'Expect': "100-continue",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': "OB48"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=edata, headers=headers) as response:
                return await response.text()
    except Exception as e:
        print(f"Error sending request: {e}")
        return None


async def send_multiple_requests(uid, url):
    protobuf_message = create_protobuf_message(uid)
    if protobuf_message is None:
        return None
    encrypted_uid = encrypt_message(protobuf_message)
    if encrypted_uid is None:
        return None
    tokens = load_tokens()
    if tokens is None:
        return None
    tasks = []
    for token_entry in tokens:
        token = token_entry["token"]
        tasks.append(send_request(encrypted_uid, token, url))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results





def create_protobuf(uid):
    try:
        message = uid_generator_pb2.uid_generator()
        message.saturn_ = int(uid)
        message.garena = 1
        return message.SerializeToString()
    except Exception as e:
        print(f"Error creating uid protobuf: {e}")
        return None


def enc(uid):
    protobuf_data = create_protobuf(uid)
    if protobuf_data is None:
        return None
    return encrypt_message(protobuf_data)


def make_request(encrypt, token):
    try:
        url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
        edata = bytes.fromhex(encrypt)
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; Redmi Note 8 Pro Build/RP1A.200720.011)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Authorization': f"Bearer {token}",
            'Content-Type': "application/x-www-form-urlencoded",
            'Expect': "100-continue",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': "OB48"
        }
        response = requests.post(url, data=edata, headers=headers, verify=False)
        binary = response.content
        return decode_protobuf(binary)
    except Exception as e:
        print(f"Error in make_request: {e}")
        return None


def decode_protobuf(binary):
    try:
        items = like_count_pb2.Info()
        items.ParseFromString(binary)
        return items
    except DecodeError as e:
        print(f"Protobuf decode error: {e}")
        return None



async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /like <player_id>")
        return

    player_id = context.args[0].strip()
    if not player_id.isdigit():
        await update.message.reply_text("Invalid player ID. Please enter a number.")
        return

    # Check for cooldown
    on_cooldown, remaining = is_on_cooldown(player_id)
    if on_cooldown:
        await update.message.reply_text(f"This player is on cooldown. Try again in {remaining}.")
        return

    await update.message.reply_text("Fetching data...")

    token = load_tokens()[0]["token"]
    encrypted = enc(player_id)
    if encrypted is None:
        await update.message.reply_text("Encryption failed.")
        return

    before = make_request(encrypted, token)
    if before is None:
        await update.message.reply_text("Failed to get player data before like.")
        return

    before_likes = int(json.loads(MessageToJson(before)).get("AccountInfo", {}).get("Likes", 0))

    start_time = time.time()
    url = "https://client.ind.freefiremobile.com/LikeProfile"
    await send_multiple_requests(player_id, url)
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    after = make_request(encrypted, token)
    if after is None:
        await update.message.reply_text("Failed to get player data after like.")
        return

    after_json = json.loads(MessageToJson(after))
    after_likes = int(after_json.get("AccountInfo", {}).get("Likes", 0))
    name = after_json.get("AccountInfo", {}).get("PlayerNickname", "Unknown")
    like_given = after_likes - before_likes

    await update.message.reply_text(
        f"Player: {name}\nUID: {player_id}\nLikes Given: {like_given}\nBefore: {before_likes} -> After: {after_likes}\nTime Taken: {time_taken} seconds"
    )

    # Save cooldown
    update_cooldown(player_id)
    
async def view_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /view <player_id>")
        return

    player_id = context.args[0].strip()
    if not player_id.isdigit():
        await update.message.reply_text("Invalid player ID. Please enter a number.")
        return

    await update.message.reply_text("Fetching data...")

    token = load_tokens()[0]["token"]
    encrypted = enc(player_id)
    if encrypted is None:
        await update.message.reply_text("Encryption failed.")
        return

    before = make_request(encrypted, token)
    if before is None:
        await update.message.reply_text("Failed to get player data before like.")
        return

    # Convert protobuf to JSON and print the full "before" data
    before_json = json.loads(MessageToJson(before))
    await update.message.reply_text(f"Full Account Info (Before):\n```{json.dumps(before_json, indent=2)}```", parse_mode='Markdown')

    before_likes = int(before_json.get("AccountInfo", {}).get("Likes", 0))

    after = make_request(encrypted, token)
    if after is None:
        await update.message.reply_text("Failed to get player data after like.")
        return

    after_json = json.loads(MessageToJson(after))
    account_info = after_json.get("AccountInfo", {})

    name = account_info.get("PlayerNickname", "Unknown")

    await update.message.reply_text(
        f"Player: {name}\n"
        f"UID: {player_id}\n"
        f"Likes: {before_likes}"
    )









async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Send a player ID to start sending likes!\n"
        "Usage: /like <player_id>\n"
        "Usage: /view <player_id>\n"
           "Usage: /jwt_up Update Token\n"
    )
    await update.message.reply_text(message)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("like", like_command))
    app.add_handler(CommandHandler("view", view_command))
    app.add_handler(CommandHandler("jwt_up", jwt_command))
    app.run_polling()



if __name__ == "__main__":
    main()
