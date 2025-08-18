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

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command. It now shows the button to choose the API.
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 Check SIM Detail", callback_data="show_options")]
    ])
    
    try:
        with open("logo.png", "rb") as img:
            await update.message.reply_photo(
                photo=img,
                caption="🔍 SIM Detail Bot\n\nThis bot helps you retrieve SIM owner information using a secure API.\n\nOnly for personal and research use.",
                reply_markup=keyboard
            )
    except (FileNotFoundError, IOError) as e:
        logging.error(f"❌ Error loading logo.png: {e}")
        await update.message.reply_text(
            text="🔍 SIM Detail Bot\n\nThis bot helps you retrieve SIM owner information using a secure API.\n\nOnly for personal and research use.",
            reply_markup=keyboard
        )

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
            [InlineKeyboardButton("✅ API 1 (Single Record)", callback_data="check_sim_api1")],
            [InlineKeyboardButton("✅ API 2 (Multiple Records)", callback_data="check_sim_api2")]
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
    if selected_api == "check_sim_api1":
        api_url = f"https://api.impossible-world.xyz/api/data?phone={phone}"
    elif selected_api == "check_sim_api2":
        api_url = f"https://api.impossible-world.xyz/api/alldata?number={phone}"

    if not api_url:
        await update.message.reply_text("An error occurred. Please try again.")
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                raw_data = await resp.text()
                if resp.status == 200:
                    try:
                        records = json.loads(raw_data)
                        
                        # API 1 returns a single JSON object, API 2 returns a list
                        # Convert single object to a list for consistent handling
                        if isinstance(records, dict):
                            records = [records]
                        
                        if isinstance(records, list) and len(records) > 0:
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

                            final_text = "*𝙆𝘼𝙈𝙄 𝙭 𝙉𝙊𝙏𝙃𝙄𝙉𝙂 𝘿𝙖𝙩𝙖𝙗𝙖𝙨𝙚*\n\n" + "\n".join(text_blocks)
                            
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
    app.add_handler(CallbackQueryHandler(show_options, pattern="^show_options$"))
    app.add_handler(CallbackQueryHandler(handle_api_selection, pattern="^check_sim_api(1|2)$"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_number))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
