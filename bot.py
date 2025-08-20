import os
import json
import logging
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.helpers import escape_markdown

# Logging
logging.basicConfig(level=logging.INFO)

# Replace with your actual bot token
BOT_TOKEN = "8470784613:AAEfoqhoaLc3Ix78g59EXLFWDJ-PiN82gBQ"

# 👇 نئے تبدیلیاں یہاں شروع ہوتی ہیں 👇
# Channels to force subscription. Replace with your actual channel usernames.
CHANNELS_TO_JOIN = ["@kami_broken5", "@only_possible_worlds", "@ik804EmanOfficial"]

# 👆 اپنے چینلز کے usernames یہاں لکھیں، جیسے "@MyOfficialChannel"

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command. It now shows the channels to join.
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Kami_Broken 🚀", url=f"https://t.me/{CHANNELS_TO_JOIN[0][1:]}")],
        [InlineKeyboardButton("Impossible - World 🌎", url=f"https://t.me/{CHANNELS_TO_JOIN[1][1:]}")],
        [InlineKeyboardButton("Queen 👑", url=f"https://t.me/{CHANNELS_TO_JOIN[2][1:]}")],
        [InlineKeyboardButton("✅ I have joined", callback_data="check_membership")]
    ])
    
    caption_text = (
        "🔍 SIM Detail Bot\n\n"
        "This bot helps you retrieve SIM owner information using a secure API.\n\n"
        "**‼️ Please join our channels to use the bot. 👇**"
    )
    
    try:
        with open("logo.png", "rb") as img:
            await update.message.reply_photo(
                photo=img,
                caption=caption_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    except (FileNotFoundError, IOError) as e:
        logging.error(f"❌ Error loading logo.png: {e}")
        await update.message.reply_text(
            text=caption_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the 'I have joined' button and checks user's membership.
    """
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    all_joined = True

    for channel in CHANNELS_TO_JOIN:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                all_joined = False
                break
        except Exception as e:
            logging.error(f"Error checking membership for {channel}: {e}")
            all_joined = False
            break

    if all_joined:
        # If joined, show the original menu
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔎 Check SIM Detail", callback_data="show_options")]
        ])
        await query.message.reply_text(
            text="✅ Thank you for joining! You can now use the bot.",
            reply_markup=keyboard
        )
    else:
        # If not joined, prompt again
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Channel 1 🚀", url=f"https://t.me/{CHANNELS_TO_JOIN[0][1:]}")],
            [InlineKeyboardButton("Channel 2 💬", url=f"https://t.me/{CHANNELS_TO_JOIN[1][1:]}")],
            [InlineKeyboardButton("✅ I have joined", callback_data="check_membership")]
        ])
        await query.message.reply_text(
            text="❌ You must join both channels to use this bot. Please join and try again.",
            reply_markup=keyboard
        )

# 👇 باقی کوڈ وہی ہے جس میں کوئی تبدیلی نہیں ہے 👇

# Callback to show API options
async def show_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback for the "Check SIM Detail" button,
    presenting the user with two API options.
    """
    query = update.callback_query
    if query:
        await query.answer()
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ API 1", callback_data="check_sim_api1")],
            [InlineKeyboardButton("✅ API 2", callback_data="check_sim_api2")]
        ])
        await query.message.edit_reply_markup(reply_markup=keyboard)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="📱 Please select an API to check the SIM detail with."
        )

# Callback to initiate the API check
async def handle_api_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the user's API selection and prompts them for a phone number.
    It stores the selected API in a temporary user_data dictionary.
    """
    query = update.callback_query
    if query:
        await query.answer()
        selected_api = query.data
        context.user_data['selected_api'] = selected_api
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Please enter the phone number you want to check."
        )

# Handle the phone number input
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles a user's text message (assumed to be a phone number).
    It fetches SIM data from the selected API and sends the result as text.
    """
    phone = update.message.text.strip()
    if phone.startswith("0"):
        phone = phone[1:]

    selected_api = context.user_data.get('selected_api')
    if not selected_api:
        await update.message.reply_text("Please select an API first by clicking on 'Check SIM Detail'.")
        return

    api_url = ""
    # Define the API URLs
    if selected_api == "check_sim_api1":
        api_url = f"https://api.impossible-world.xyz/api/data?phone={phone}"
    elif selected_api == "check_sim_api2":
        api_url = f"https://api.impossible-world.xyz/api/alldata?number={phone}"

    if not api_url:
        await update.message.reply_text("An error occurred. Please try again.")
        return

    try:
        async with aiohttp.ClientSession() as session:
            await update.message.reply_text("🔎 Fetching data... Please wait.")
            async with session.get(api_url) as resp:
                raw_data = await resp.text()
                if resp.status == 200:
                    try:
                        data = json.loads(raw_data)
                        
                        records = []
                        if selected_api == "check_sim_api1":
                            # API 1 now returns a dict with a "records" key
                            if isinstance(data, dict) and "records" in data:
                                records = data["records"]
                            else:
                                records = [data] if isinstance(data, dict) else []
                        elif selected_api == "check_sim_api2":
                            # API 2 returns a list directly
                            records = data if isinstance(data, list) else [data]

                        if records and len(records) > 0:
                            text_blocks = []
                            for record in records:
                                name = escape_markdown(record.get("Name", "Not Available"), version=2)
                                mobile = escape_markdown(record.get("Mobile", "Not Available"), version=2)
                                cnic = escape_markdown(record.get("CNIC", "Not Available"), version=2)
                                address = escape_markdown(record.get("Address", "Not Available"), version=2)

                                block = (
                                    "━━━━━━━━━━━━━━━\n"
                                    f"👤 *Name:* {name}\n"
                                    f"📱 *Mobile:* {mobile}\n"
                                    f"🆔 *CNIC:* {cnic}\n"
                                    f"🏠 *Address:* {address}\n"
                                    "━━━━━━━━━━━━━━━"
                                )
                                text_blocks.append(block)

                            final_text = "👿👿👿👿\n\n" + "\n".join(text_blocks)
                            
                            keyboard = InlineKeyboardMarkup([
                                [InlineKeyboardButton("🔎 Check Another Number Detail", callback_data="show_options")]
                            ])
                            await update.message.reply_text(
                                final_text,
                                parse_mode="MarkdownV2",
                                reply_markup=keyboard
                            )
                        else:
                            await update.message.reply_text("No records found.")
                    except json.JSONDecodeError:
                        logging.error(f"API invalid JSON response: {raw_data}")
                        await update.message.reply_text(f"❌ API returned an invalid response:\n\n{raw_data}")
                else:
                    await update.message.reply_text(
                        f"❌ API failed (status {resp.status}):\n\n{raw_data}"
                    )
    except aiohttp.ClientError as e:
        logging.error(f"API request error: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ An error occurred while fetching data: {e}")

# Run the bot
def main():
    """
    Main function to set up and run the bot.
    """
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers for commands and messages
    app.add_handler(CommandHandler("start", start))
    # 👇 نیا handler شامل کریں
    app.add_handler(CallbackQueryHandler(check_membership, pattern="^check_membership$"))
    # 👇 باقی handlers وہی ہیں
    app.add_handler(CallbackQueryHandler(show_options, pattern="^show_options$"))
    app.add_handler(CallbackQueryHandler(handle_api_selection, pattern="^check_sim_api(1|2)$"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_number))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
