import imaplib
import time
import email
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Binance API Setup
client = Client(api_key='',api_secret='')

def get_futures_balance():
    try:
        balances = client.futures_account_balance()
        for asset in balances:
            if asset['asset'] == 'USDT':
                print(f"💰 Futures USDT Balance: {asset['balance']}")
                return float(asset['balance'])
    except BinanceAPIException as e:
        print(f" Error fetching futures balance: {e}")
        return None

def set_leverage():
    try:
        client.futures_change_leverage(symbol='BTCUSDT', leverage=20)
        print(" Leverage set to 20x")
    except BinanceAPIException as e:
        print(f" Error setting leverage: {e}")

def get_futures_position():
    try:
        positions = client.futures_position_information()
        for position in positions:
            if position["symbol"] == "BTCUSDT":
                return float(position["positionAmt"])
        return 0
    except BinanceAPIException as e:
        print(f" Error fetching position: {e}")
        return 0

def close_position(position_size):
    try:
        if position_size > 0:
            client.futures_create_order(symbol='BTCUSDT', side='SELL', type='MARKET', quantity=abs(position_size))
            print("Closed LONG position.")
        elif position_size < 0:
            client.futures_create_order(symbol='BTCUSDT', side='BUY', type='MARKET', quantity=abs(position_size))
            print(" Closed SHORT position.")
    except BinanceAPIException as e:
        print(f" Error closing position: {e}")

def process_alert(body):
    body = body.strip().lower()
    print(f"🚨 Processing Alert Content: '{body}'")
    
    if not body:
        print("❌ Empty alert received")
        return

    position_size = get_futures_position()

    if 'buy' in body:
        print("✅ Executing Buy order.")
        if position_size != 0:
            close_position(position_size)
        client.futures_create_order(symbol='BTCUSDT', side='BUY', type='MARKET', quantity=0.001)
        print("✅ New LONG position opened.")

    elif 'sell' in body:
        print("✅ Executing Sell order.")
        if position_size != 0:
            close_position(position_size)
        client.futures_create_order(symbol='BTCUSDT', side='SELL', type='MARKET', quantity=0.001)
        print("✅ New SHORT position opened.")

    elif 'exit' in body:
        if position_size != 0:
            close_position(position_size)
            print("✅ Trade exited.")

    
    

def check_email():
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login('', '')
        mail.select('inbox')

        # Search for UNSEEN emails from TradingView
        status, messages = mail.search(None, '(UNSEEN FROM "noreply@tradingview.com")')
        if status != "OK" or not messages[0]:
            print(" No new TradingView alerts found.")
            mail.close()
            mail.logout()
            return

        for email_id in messages[0].split():
            # Mark email as read before processing to prevent repeats
            mail.store(email_id, '+FLAGS', '\Seen')
            
            status, data = mail.fetch(email_id, '(RFC822)')
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Extract text from multipart emails
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = msg.get_payload(decode=True).decode()

            if body:
                process_alert(body)
            else:
                print("❌ No text body found in email")

        mail.close()
        mail.logout()

    except Exception as e:
        print(f"⚠️ Email error: {str(e)}")

if __name__ == "__main__":
    get_futures_balance()
    set_leverage()
    while True:
        check_email()
        time.sleep(10)