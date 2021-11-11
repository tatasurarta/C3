import asyncio
import os
import shutil
import signal
import time
from datetime import datetime
from sys import executable

import psutil
import pytz
from pyrogram import idle
from telegram import ParseMode, InlineKeyboardMarkup
from telegram.ext import CommandHandler
from telegraph import Telegraph
from wserver import start_server_async

from bot import (
    OWNER_ID,
    AUTHORIZED_CHATS,
    IGNORE_PENDING_REQUESTS,
    IMAGE_URL,
    IS_VPS,
    PORT,
    nox,
    alive,
    app,
    bot,
    botStartTime,
    dispatcher,
    updater,
    web,
    telegraph_token,
)
from bot.helper.ext_utils import fs_utils
from bot.helper.telegram_helper import button_build
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import *

from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from .modules.rssfeeds import rss_init
from .modules import (
    authorize,
    cancel_mirror,
    clone,
    count,
    delete,
    eval,
    list,
    mediainfo,
    mirror,
    mirror_status,
    reboot,
    rssfeeds,
    shell,
    speedtest,
    search,
    torrent_search,
    usage,
    watch,
    leech_settings,
)

now = datetime.now(pytz.timezone("Asia/Jakarta"))


def stats(update, context):
    currentTime = get_readable_time(time.time() - botStartTime)
    current = now.strftime("%Y/%m/%d %I:%M:%S %p")
    total, used, free = shutil.disk_usage(".")
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    stats = (
        f"<b>👴🏻 𝐖𝐚𝐤𝐭𝐮 𝐀𝐤𝐭𝐢𝐟 𝐁𝐨𝐭 ⌚️:</b> <code>{currentTime}</code>\n"
        f"<b>💾 𝐓𝐨𝐭𝐚𝐥 𝐑𝐮𝐚𝐧𝐠 𝐃𝐢𝐬𝐤 💾:</b> <code>{total}</code>\n"
        f"<b>⌛️ 𝐓𝐞𝐫𝐩𝐚𝐤𝐚𝐢 ⌛️:</b> <code>{used}</code> "
        f"<b>🔋 𝐊𝐨𝐬𝐨𝐧𝐠 🔋:</b> <code>{free}</code>\n\n"
        f"<b>🔺 𝐔𝐧𝐠𝐠𝐚𝐡𝐚𝐧:</b> <code>{sent}</code>\n"
        f"<b>🔻 𝐔𝐧𝐝𝐮𝐡𝐚𝐧:</b> <code>{recv}</code>\n\n"
        f"<b>🖥️ 𝐂𝐏𝐔:</b> <code>{cpuUsage}%</code> "
        f"<b>🧭 𝐑𝐀𝐌:</b> <code>{memory}%</code> "
        f"<b>🖫 𝐒𝐒𝐃:</b> <code>{disk}%</code>"
    )
    update.effective_message.reply_photo(
        IMAGE_URL, stats, parse_mode=ParseMode.HTML
    )  # noqa: E501


def start(update, context):
    buttons = button_build.ButtonMaker()
    buttons.buildbutton("👨🏼‍✈️ 𝐏𝐞𝐦𝐢𝐥𝐢𝐤 🙈", "https://www.instagram.com/mimi.peri")
    buttons.buildbutton("🐊 𝐂𝐫𝐮𝐬𝐡 👩🏻", "https://www.instagram.com/zar4leola")
    reply_markup = InlineKeyboardMarkup(buttons.build_menu(2))
    if (
            CustomFilters.authorized_user(update)
            or CustomFilters.authorized_chat(update)
            or update.message.chat.type == "private"
    ):
        start_string = f"""
Bot ini dapat mencerminkan semua tautan Anda ke Google Drive!
Tipe /{BotCommands.HelpCommand} untuk mendapatkan daftar perintah yang tersedia
"""
        sendMarkup(start_string, context.bot, update, reply_markup)
    else:
        sendMarkup(
            "𝐔𝐩𝐬! 𝐓𝐢𝐝𝐚𝐤 𝐌𝐞𝐦𝐢𝐥𝐢𝐤𝐢 𝐎𝐭𝐨𝐫𝐢𝐬𝐚𝐬𝐢 𝐑𝐞𝐬𝐦𝐢.\n𝐓𝐨𝐥𝐨𝐧𝐠 𝐁𝐮𝐚𝐭 𝐒𝐞𝐧𝐝𝐢𝐫𝐢 <b>𝐌𝐢𝐫𝐫𝐨𝐫 𝐁𝐨𝐭 𝐧𝐲𝐚</b> 𝐘𝐚𝐧𝐠 𝐒𝐚𝐛𝐚𝐫 𝐲𝐚 𝐁𝐨𝐬.",  # noqa: E501
            context.bot,
            update,
            reply_markup,
        )


def restart(update, context):
    restart_message = sendMessage(
        "𝐌𝐞𝐦𝐮𝐥𝐚𝐢 𝐮𝐥𝐚𝐧𝐠, 𝐇𝐚𝐫𝐚𝐩 𝐭𝐮𝐧𝐠𝐠𝐮!", context.bot, update
    )  # noqa: E501
    # Save restart message object in order to reply to it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    fs_utils.clean_all()
    alive.kill()
    process = psutil.Process(web.pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()
    nox.kill()
    os.execl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = sendMessage("Mulai Ping", context.bot, update)
    end_time = int(round(time.time() * 1000))
    editMessage(f"{end_time - start_time} ms", reply)


def log(update, context):
    sendLogFile(context.bot, update)


help_string_telegraph = f'''<br>
<b>/{BotCommands.HelpCommand}</b>: Untuk mendapatkan pesan ini
<br><br>
<b>/{BotCommands.MirrorCommand}</b> [download_url][magnet_link]: Mulai mirroring tautan ke Google Drive.
<br><br>
<b>/{BotCommands.ZipMirrorCommand}</b> [download_url][magnet_link]: Mulai mirroring dan unggah yang diarsipkan (.zip) versi unduhan
<br><br>
<b>/{BotCommands.UnzipMirrorCommand}</b> [download_url][magnet_link]: Mulai mirroring dan file yang diunduh adalah arsip, mengekstraknya ke Google Drive
<br><br>
<b>/{BotCommands.QbMirrorCommand}</b> [magnet_link]: Mulai mirroring menggunakan qBittorrent, Gunakan /{BotCommands.QbMirrorCommand} s untuk memilih file sebelum mengunduh
<br><br>
<b>/{BotCommands.QbZipMirrorCommand}</b> [magnet_link]: Mulai mirroring menggunakan qBittorrent dan unggah versi unduhan (.zip) yang diarsipkan
<br><br>
<b>/{BotCommands.QbUnzipMirrorCommand}</b> [magnet_link]: Mulai mirroring menggunakan qBittorrent dan jika file yang diunduh adalah arsip apa pun, ekstrak ke Google Drive
<br><br>
<b>/{BotCommands.LeechCommand}</b> [download_url][magnet_link]: Mulai leeching ke Telegram, Gunakan <b>/{BotCommands.LeechCommand} s</b> untuk memilih file sebelum leeching
<br><br>
<b>/{BotCommands.ZipLeechCommand}</b> [download_url][magnet_link]: Mulai leeching ke Telegram dan unggah sebagai (.zip)
<br><br>
<b>/{BotCommands.UnzipLeechCommand}</b> [download_url][magnet_link]: Mulai leeching ke Telegram dan jika file yang diunduh adalah arsip apa pun, ekstrak ke Telegram
<br><br>
<b>/{BotCommands.QbLeechCommand}</b> [magnet_link]: Mulai leeching ke Telegram Menggunakan Qbittorrent, Gunakan <b>/{BotCommands.QbLeechCommand} s</b> untuk memilih file sebelum leeching
<br><br>
<b>/{BotCommands.QbZipLeechCommand}</b> [magnet_link]: Mulai leeching ke Telegram Menggunakan Qbittorrent dan unggah sebagai (.zip)
<br><br>
<b>/{BotCommands.QbUnzipLeechCommand}</b> [magnet_link]: Mulai leeching ke Telegram Menggunakan Qbittorrent dan jika file yang diunduh adalah arsip apa pun, ekstrak ke Telegram
<br><br>
<b>/{BotCommands.CloneCommand}</b> [drive_url]: Salin file/folder ke Google Drive
<br><br>
<b>/{BotCommands.CountCommand}</b> [drive_url]: Hitung file/folder dari Google Drive Links
<br><br>
<b>/{BotCommands.DeleteCommand}</b> [drive_url]: Hapus file dari Google Drive (Hanya Pemilik & Sudo)
<br><br>
<b>/{BotCommands.WatchCommand}</b> [youtube-dl/yt-dlp supported link]: Cermin melalui yt-dlp/youtube-dl. Ketik /{BotCommands.WatchCommand} atau ketik /tolong
<br><br>
<b>/{BotCommands.ZipWatchCommand}</b> [youtube-dl/yt-dlp supported link]: Cermin melalui youtube-dl atau yt-dlp dan zip sebelum mengunggah
<br><br>
<b>/{BotCommands.LeechWatchCommand}</b> [youtube-dl/yt-dlp supported link]: Leech melalui youtube-dl/yt-dlp
<br><br>
<b>/{BotCommands.LeechZipWatchCommand}</b> [youtube-dl/yt-dlp supported link]: Leech melalui youtube-dl/yt-dlp dan zip sebelum mengunggah
<br><br>
<b>/{BotCommands.LeechSetCommand}</b> Pengaruran Leech
<br><br>
<b>/{BotCommands.SetThumbCommand}</b>: Balas foto untuk mengaturnya sebagai Thumbnail
<br><br>
<b>/{BotCommands.CancelMirror}</b>: Balas pesan di mana unduhan dimulai dan unduhan itu akan dibatalkan
<br><br>
<b>/{BotCommands.CancelAllCommand}</b>: Batalkan semua tugas yang sedang berjalan
<br><br>
<b>/{BotCommands.ListCommand}</b> [search term]: Mencari istilah pencarian di Google Drive, Jika ditemukan balasan dengan tautan
<br><br>
<b>/{BotCommands.SearchCommand}</b> [query]: Cari torrent dengan plugin pencarian qbittorrent yang diinstal
<br><br>
<b>/{BotCommands.StatusCommand}</b>: Menunjukkan status semua unduhan
<br><br>
<b>/{BotCommands.StatsCommand}</b>: Tampilkan Statistik Mesin The Bot diselenggarakan
'''
help = Telegraph(access_token=telegraph_token).create_page(
    title='Perintah Rumah Awan',
    author_name='Rumah Awan',
    author_url='https://t.me/awanmirror3bot',
    html_content=help_string_telegraph,
)["path"]

help_string = f'''
/{BotCommands.PingCommand}: Periksa berapa lama waktu yang dibutuhkan untuk melakukan Ping Bot

/{BotCommands.AuthorizeCommand}: Otorisasi obrolan atau pengguna untuk menggunakan BOT (hanya dapat dipanggil oleh pemilik & sudo bot)

/{BotCommands.UnAuthorizeCommand}: Tidak sah obrolan atau pengguna untuk menggunakan BOT (hanya dapat dipanggil oleh pemilik & sudo bot)

/{BotCommands.AuthorizedUsersCommand}: Tampilkan pengguna yang berwenang (hanya pemilik & sudo)

/{BotCommands.AddSudoCommand}: Tambahkan pengguna sudo (hanya pemilik)

/{BotCommands.RmSudoCommand}: Hapus pengguna sudo (hanya pemilik)

/{BotCommands.RestartCommand}: Mulai ulang bot.

/{BotCommands.LogCommand}: Dapatkan file log bot.Berguna untuk mendapatkan laporan kecelakaan

/{BotCommands.UsageCommand}: Untuk melihat statistik Heroku Dyno (hanya pemilik & sudo)

/{BotCommands.SpeedCommand}: Periksa kecepatan internet tuan rumah

/{BotCommands.MediaInfoCommand}: Dapatkan info terperinci tentang Media Jawab (hanya untuk file telegram)

/{BotCommands.ShellCommand}: Run commands in Shell (Only Owner)

/{BotCommands.ExecHelpCommand}: Get help for Executor module (Only Owner)

/{BotCommands.RssHelpCommand}:  Get help for RSS feeds module

/{BotCommands.TsHelpCommand}: Get help for Torrent search module
'''


def bot_help(update, context):
    button = button_build.ButtonMaker()
    button.buildbutton("Perintah lainnya", f"https://telegra.ph/{help}")
    reply_markup = InlineKeyboardMarkup(button.build_menu(1))
    sendMarkup(help_string, context.bot, update, reply_markup)


'''
botcmds = [
    (f"{BotCommands.HelpCommand}", "Dapatkan bantuan terperinci"),
    (f"{BotCommands.MirrorCommand}", "Mulai mirroring"),
    (f"{BotCommands.UnzipMirrorCommand}", "Ekstrak file"),
    (f"{BotCommands.ZipMirrorCommand}", "Mulai mirroring dan unggah sebagai .zip"),
    (f"{BotCommands.CloneCommand}", "Salin file/folder ke Drive"),
    (f"{BotCommands.CountCommand}", "Hitung file/folder dari link Drive"),
    (f"{BotCommands.DeleteCommand}", "Hapus file dari drive"),
    (f'{BotCommands.QbMirrorCommand}','Mulai Mencerminkan menggunakan qBittorrent'),
    (f'{BotCommands.QbZipMirrorCommand}','Mulai mirroring dan unggah sebagai .zip menggunakan qb'),
    (f'{BotCommands.QbUnzipMirrorCommand}','Ekstrak file melalui qBitorrent'),
    (f"{BotCommands.WatchCommand}", "Mirror video/audio menggunakan YouTube-DL"),
    (f'{BotCommands.ZipWatchCommand}','Cerminkan tautan daftar putar Youtube sebagai .zip'),
    (f"{BotCommands.CancelMirror}", "Batalkan tugas"),
    (f"{BotCommands.CancelAllCommand}", "Batalkan semua tugas"),
    (f"{BotCommands.ListCommand}", "Mencari file dalam drive"),
    (f"{BotCommands.StatusCommand}", "Dapatkan pesan status cermin"),
    (f"{BotCommands.StatsCommand}", "Statistik Penggunaan Bot."),
    (f"{BotCommands.PingCommand}", "berlomba cepat koneksi."),
    (f"{BotCommands.RestartCommand}", "Mulai ulang bot. [hanya owner/sudo]"),
    (f"{BotCommands.LogCommand}", "Dapatkan Log Bot [hanya owner/sudo]"),
    (
        f"{BotCommands.MediaInfoCommand}",
        "Dapatkan info detail tentang media yang dibalas",
    ),
]
'''


def main():
    current = now_asia.strftime(format)
    fs_utils.start_cleanup()
    if IS_VPS:
        asyncio.get_event_loop().run_until_complete(start_server_async(PORT))
    # Check if the bot is restarting
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text(f'𝐁𝐞𝐫𝐡𝐚𝐬𝐢𝐥 𝐦𝐞𝐦𝐮𝐥𝐚𝐢 𝐮𝐥𝐚𝐧𝐠, 𝐒𝐞𝐦𝐮𝐚 𝐓𝐮𝐠𝐚𝐬 𝐃𝐢𝐛𝐚𝐭𝐚𝐥𝐤𝐚𝐧! 𝑷𝒂𝒅𝒂 {current}', chat_id, msg_id)
        os.remove(".restartmsg")
    elif OWNER_ID:
        try:
            text = f'Bot Sudah Hidup Lagi! 𝑷𝒂𝒅𝒂 {current}'
            bot.sendMessage(chat_id=OWNER_ID, text=text, parse_mode=ParseMode.HTML)
            if AUTHORIZED_CHATS:
                for i in AUTHORIZED_CHATS:
                    bot.sendMessage(chat_id=i, text=text, parse_mode=ParseMode.HTML)
        except Exception as e:
            LOGGER.warning(e)
    # bot.set_my_commands(botcmds)
    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    ping_handler = CommandHandler(
        BotCommands.PingCommand,
        ping,
        filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
        run_async=True,
    )
    restart_handler = CommandHandler(
        BotCommands.RestartCommand,
        restart,
        filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
        run_async=True,
    )
    help_handler = CommandHandler(
        BotCommands.HelpCommand,
        bot_help,
        filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
        run_async=True,
    )
    stats_handler = CommandHandler(
        BotCommands.StatsCommand,
        stats,
        filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
        run_async=True,
    )
    log_handler = CommandHandler(
        BotCommands.LogCommand,
        log,
        filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
        run_async=True,
    )
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("Bot Started!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)
    rss_init()


app.start()
main()
idle()
