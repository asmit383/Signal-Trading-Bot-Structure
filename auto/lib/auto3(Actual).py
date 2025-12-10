import imaplib
import time
import email
import re
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Binance API Setup
client = Client(
    api_key='',
    api_secret=''
)

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
def close_position(position_size):
    try:
        if position_size > 0:  # Close Long
            client.futures_create_order(symbol='BTCUSDT', side='SELL', type='MARKET', quantity=abs(position_size))
            print("Closed LONG position.")
        elif position_size < 0:  # Close Short
            client.futures_create_order(symbol='BTCUSDT', side='BUY', type='MARKET', quantity=abs(position_size))
            print(" Closed SHORT position.")
    except BinanceAPIException as e:
        print(f" Error closing position: {e}") 
    
def get_futures_position():
    try:
        positions = client.futures_position_information()
        for position in positions:
            if position["symbol"] == "BTCUSDT":
                return float(position["positionAmt"])  # Positive = Long, Negative = Short, 0 = No position
        return 0
    except BinanceAPIException as e:
        print(f" Error fetching position: {e}")
        return 0

def process_alert(body):
    body = body.strip().lower()
    print(f"🚨 Processing Alert Content: '{body}'")
    
    if not body:
        print("❌ Empty alert received")
        return

    # Use precise pattern matching
    buy_signal = re.search(r'\b(buy|long)\b', body)
    sell_signal = re.search(r'\b(sell|short)\b', body)
    exit_signal = re.search(r'\b(exit|close)\b', body)

    position_size = get_futures_position()

    if buy_signal:
        print("✅ Executing Buy order.")
        if position_size != 0:
            close_position(position_size)
        try:
            client.futures_create_order(symbol='BTCUSDT', side='BUY', type='MARKET', quantity=0.001)
            print("✅ New LONG position opened.")
        except BinanceAPIException as e:
            print(f"❌ Order error: {e}")

    elif sell_signal:
        print("✅ Executing Sell order.")
        if position_size != 0:
            close_position(position_size)
        try:
            client.futures_create_order(symbol='BTCUSDT', side='SELL', type='MARKET', quantity=0.001)
            print("✅ New SHORT position opened.")
        except BinanceAPIException as e:
            print(f"❌ Order error: {e}")

    elif exit_signal:
        if position_size != 0:
            close_position(position_size)
            print("✅ Trade exited.")

def check_email():
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login('', '')
        mail.select('inbox', readonly=False)  # Ensure we can modify flags

        # Search for UNSEEN emails
        status, messages = mail.search(None, '(UNSEEN FROM "noreply@tradingview.com")')
        if status != "OK" or not messages[0]:
            print(" No new TradingView alerts found.")
            mail.close()
            mail.logout()
            return

        for email_id in messages[0].split():
            # First mark as seen to prevent reprocessing
            mail.store(email_id, '+FLAGS', '(\Seen)')
            
            status, data = mail.fetch(email_id, '(RFC822)')
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Check subject first
            subject = msg.get('Subject', '').lower()
            body = ""
            
            # Try to get both subject and body content
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        except:
                            body = "Unable to decode body"
                        break
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                except:
                    body = "Unable to decode body"

            # Log raw content for debugging
            print(f"\n📧 New Email - Subject: {subject}")
            print(f"📝 Body Preview: {body[:100]}...")

            # Process combined content
            combined_content = f"{subject} {body}".lower()
            process_alert(combined_content)

        mail.close()
        mail.logout()

    except Exception as e:
        print(f"⚠️ Email error: {str(e)}")

if __name__ == "__main__":
    get_futures_balance()
    
    while True:
        
        check_email()
        time.sleep(10)
        
        