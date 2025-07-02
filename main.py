import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from web3 import Web3
import asyncio
import os

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
RECEIVER_ADDRESS = os.getenv("RECEIVER_ADDRESS")
CELO_RPC = 'https://forno.celo.org'
G_CONTRACT = '0xE4C4cF3cB472F1417924C73Ff98fB7059A93D692'  # G$ contract on Celo
web3 = Web3(Web3.HTTPProvider(CELO_RPC))

logging.basicConfig(level=logging.INFO)

# --- HELPER FUNCTION ---
def check_payment(user_address: str, min_amount: float = 1.0) -> bool:
    contract = web3.eth.contract(address=Web3.to_checksum_address(G_CONTRACT), abi=[
        {"constant": True, "inputs": [{"name": "","type": "address"}], "name": "balanceOf", "outputs": [{"name": "","type": "uint256"}], "type": "function"}
    ])
    balance = contract.functions.balanceOf(Web3.to_checksum_address(user_address)).call()
    return balance / (10 ** 18) >= min_amount

# --- COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to GoodMarket Bot!\n\nTo purchase a product, use /buy.\nTo set your wallet, use /wallet [your_wallet_address]"
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("✅ I Paid", callback_data='check_payment')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🛒 Please send *10 G$* to the following wallet address:\n`{RECEIVER_ADDRESS}`\n\nAfter sending, click the button below to confirm.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_wallet = context.user_data.get("wallet")
    if not user_wallet:
        await query.edit_message_text("❗ Please set your wallet address first using /wallet [your_wallet_address].")
        return

    await query.edit_message_text("🔍 Checking payment on Celo blockchain...")

    try:
        if check_payment(user_wallet):
            await query.message.reply_text("✅ Payment confirmed! Thank you for your order. Wait 5–10 minutes for delivery.")
        else:
            await query.message.reply_text("❌ Payment not found. Please try again or contact support.")
    except Exception as e:
        await query.message.reply_text(f"⚠️ Error checking payment: {str(e)}")

async def save_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❗ Usage: /wallet [your_wallet_address]")
        return

    context.user_data['wallet'] = context.args[0]
    await update.message.reply_text("✅ Wallet address saved. Now you can proceed with /buy.")

# --- MAIN FUNCTION ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wallet", save_wallet))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CallbackQueryHandler(button_handler))
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
