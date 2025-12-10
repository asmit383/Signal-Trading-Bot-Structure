import imaplib
import time
import email
import re
from binance.client import Client
from binance.exceptions import BinanceAPIException


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
            print("Closed SHORT position.")
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

    # Check for an exit signal first: if a standalone "0" is present, exit regardless of any other signals.
    if re.search(r'(?<!\d)0(?!\d)', body):
        signal = 0
        print("📶 Found exit signal '0' in alert.")
    else:
        # Otherwise, look for a LONG (1) or SHORT (-1) signal.
        signal_match = re.search(r'(?<!\d)(-1|1)(?!\d)', body)
        if not signal_match:
            print("❌ No valid signal found.")
            return
        signal = int(signal_match.group(1))
        print(f"📶 Extracted Signal: {signal}")

    position_size = get_futures_position()

    if signal == 1:
        print("✅ Executing LONG order (Signal: 1).")
        if position_size != 0:
            close_position(position_size)
        try:
            client.futures_create_order(symbol='BTCUSDT', side='BUY', type='MARKET', quantity=0.002)
            print("✅ New LONG position opened.")
        except BinanceAPIException as e:
            print(f"❌ Order error: {e}")

    elif signal == -1:
        print("✅ Executing SHORT order (Signal: -1).")
        if position_size != 0:
            close_position(position_size)
        try:
            client.futures_create_order(symbol='BTCUSDT', side='SELL', type='MARKET', quantity=0.002)
            print("✅ New SHORT position opened.")
        except BinanceAPIException as e:
            print(f"❌ Order error: {e}")

    elif signal == 0:
        print("✅ Executing EXIT order (Signal: 0).")
        if position_size != 0:
            close_position(position_size)
            print("✅ Trade exited.")
    else:
        print(f"❌ Unexpected signal value: {signal}")
def check_email():
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login('', '')
        mail.select('inbox')  # Ensure inbox is selected

        # Search for UNSEEN emails from TradingView
        status, messages = mail.search(None, '(UNSEEN FROM "noreply@tradingview.com")')
        if status != "OK" or not messages[0]:
            mail.close()
            mail.logout()
            return

        for email_id_bytes in messages[0].split():
            email_id = email_id_bytes.decode('utf-8')

            status, data = mail.fetch(email_id, '(RFC822)')
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            
            subject = msg.get('Subject', '').lower()
            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if 'attachment' in content_disposition:
                        continue  # Skip attachments
                    if content_type == 'text/plain':
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                            break  # Prefer text/plain
                        except:
                            body = "Unable to decode body"
                    elif content_type == 'text/html' and not body:
                        try:
                            html_content = part.get_payload(decode=True).decode('utf-8', errors='replace')
                            # Remove HTML tags using regex
                            body = re.sub(r'<[^>]+>', '', html_content)
                        except:
                            body = "Unable to decode HTML body"
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                except:
                    body = "Unable to decode body"

            # Log raw content for debugging
            print(f"\n📧 New Email - Subject: {subject}")
            print(f"📝 Body Preview: {body[:100]}...")

            # Combine subject and body content for processing
            combined_content = f"{subject} {body}".lower()
            process_alert(combined_content)

            # Mark email for deletion
            mail.store(email_id, '+FLAGS', '\\Deleted')

        # Permanently delete marked emails
        mail.expunge()
        mail.close()
        mail.logout()

    except Exception as e:
        print(f"⚠️ Email error: {str(e)}")


if __name__ == "__main__":
    get_futures_balance()
    
    


    
    
        
    
    while True:
        check_email()
        time.sleep(10)
        