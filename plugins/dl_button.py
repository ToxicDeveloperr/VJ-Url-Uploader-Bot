# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import asyncio
import aiohttp
import json
import math
import os
import shutil
import time
from datetime import datetime
# the secret configuration specific things
from config import Config
# the Strings used for this "thing"
from translation import Translation
from plugins.custom_thumbnail import *
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from helper_funcs.display_progress import progress_for_pyrogram, humanbytes, TimeFormatter
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
# https://stackoverflow.com/a/37631799/4723940
from PIL import Image


async def ddl_call_back(bot, update):
    logger.info(update)
    cb_data = update.data
    tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("=")
    thumb_image_path = Config.TECH_VJ_DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + ".jpg"

    youtube_dl_url = update.message.reply_to_message.text
    custom_file_name = os.path.basename(youtube_dl_url)

    if "|" in youtube_dl_url:
        url_parts = youtube_dl_url.split("|")
        if len(url_parts) == 2:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
        else:
            for entity in update.message.reply_to_message.entities:
                if entity.type == "text_link":
                    youtube_dl_url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    youtube_dl_url = youtube_dl_url[o:o + l]

        if youtube_dl_url is not None:
            youtube_dl_url = youtube_dl_url.strip()
        if custom_file_name is not None:
            custom_file_name = custom_file_name.strip()
        logger.info(youtube_dl_url)
        logger.info(custom_file_name)
    else:
        for entity in update.message.reply_to_message.entities:
            if entity.type == "text_link":
                youtube_dl_url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                youtube_dl_url = youtube_dl_url[o:o + l]

    # Safely get bot's own user object and mention
    user = await bot.get_me()
    mention = getattr(user, "mention", None)
    if not mention:
        mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    description = Translation.TECH_VJ_CUSTOM_CAPTION_UL_FILE.format(mention)

    start = datetime.now()

    await bot.edit_message_text(
        text=Translation.DOWNLOAD_START,
        chat_id=update.message.chat.id,
        message_id=update.message.id
    )

    tmp_dir = os.path.join(Config.TECH_VJ_DOWNLOAD_LOCATION, str(update.from_user.id))
    os.makedirs(tmp_dir, exist_ok=True)
    download_directory = os.path.join(tmp_dir, custom_file_name)

    command_to_exec = []

    async with aiohttp.ClientSession() as session:
        c_time = time.time()
        try:
            await download_coroutine(
                bot, session, youtube_dl_url, download_directory,
                update.message.chat.id, update.message.id, c_time
            )
        except asyncio.TimeoutError:
            await bot.edit_message_text(
                text=Translation.TECH_VJ_SLOW_URL_DECED,
                chat_id=update.message.chat.id,
                message_id=update.message.id
            )
            return False
        except Exception as e:
            logger.error(f"Download error: {e}")
            await bot.edit_message_text(
                text=f"Download failed: {e}",
                chat_id=update.message.chat.id,
                message_id=update.message.id
            )
            return False

    if os.path.exists(download_directory):
        end_one = datetime.now()
        await bot.edit_message_text(
            text=Translation.UPLOAD_START,
            chat_id=update.message.chat.id,
            message_id=update.message.id
        )

        try:
            file_size = os.stat(download_directory).st_size
        except FileNotFoundError:
            download_directory = os.path.splitext(download_directory)[0] + ".mkv"
            file_size = os.stat(download_directory).st_size

        if file_size > Config.TECH_VJ_TG_MAX_FILE_SIZE:
            await bot.edit_message_text(
                chat_id=update.message.chat.id,
                text=Translation.TECH_VJ_RCHD_TG_API_LIMIT,
                message_id=update.message.id
            )
        else:
            start_time = time.time()
            try:
                if tg_send_type == "audio":
                    duration = await Mdata03(download_directory)
                    thumb_image_path = await Gthumb01(bot, update)
                    await bot.send_audio(
                        chat_id=update.message.chat.id,
                        audio=download_directory,
                        caption=description,
                        duration=duration,
                        thumb=thumb_image_path,
                        reply_to_message_id=update.message.reply_to_message.id,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            Translation.TECH_VJ_UPLOAD_START,
                            update.message,
                            start_time
                        )
                    )
                elif tg_send_type == "file":
                    thumb_image_path = await Gthumb01(bot, update)
                    await bot.send_document(
                        chat_id=update.message.chat.id,
                        document=download_directory,
                        thumb=thumb_image_path,
                        caption=description,
                        reply_to_message_id=update.message.reply_to_message.id,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            Translation.TECH_VJ_UPLOAD_START,
                            update.message,
                            start_time
                        )
                    )
                elif tg_send_type == "vm":
                    width, duration = await Mdata02(download_directory)
                    thumb_image_path = await Gthumb02(bot, update, duration, download_directory)
                    await bot.send_video_note(
                        chat_id=update.message.chat.id,
                        video_note=download_directory,
                        duration=duration,
                        length=width,
                        thumb=thumb_image_path,
                        reply_to_message_id=update.message.reply_to_message.id,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            Translation.TECH_VJ_UPLOAD_START,
                            update.message,
                            start_time
                        )
                    )
                elif tg_send_type == "video":
                    width, height, duration = await Mdata01(download_directory)
                    thumb_image_path = await Gthumb02(bot, update, duration, download_directory)
                    await bot.send_video(
                        chat_id=update.message.chat.id,
                        video=download_directory,
                        caption=description,
                        duration=duration,
                        width=width,
                        height=height,
                        supports_streaming=True,
                        thumb=thumb_image_path,
                        reply_to_message_id=update.message.reply_to_message.id,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            Translation.TECH_VJ_UPLOAD_START,
                            update.message,
                            start_time
                        )
                    )
                else:
                    logger.info("Unknown send type encountered")

            except Exception as e:
                logger.error(f"Sending file error: {e}")
                await update.reply_text(f"Uploading failed: {e}")

            finally:
                end_two = datetime.now()
                try:
                    os.remove(download_directory)
                    if thumb_image_path and os.path.exists(thumb_image_path):
                        os.remove(thumb_image_path)
                except Exception:
                    pass

                time_taken_for_download = (end_one - start).seconds
                time_taken_for_upload = (end_two - end_one).seconds
                await bot.edit_message_text(
                    text=Translation.TECH_VJ_AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(
                        time_taken_for_download, time_taken_for_upload),
                    chat_id=update.message.chat.id,
                    message_id=update.message.id,
                    disable_web_page_preview=True
                )
    else:
        await bot.edit_message_text(
            text=Translation.TECH_VJ_NO_VOID_FORMAT_FOUND.format("Incorrect Link"),
            chat_id=update.message.chat.id,
            message_id=update.message.id,
            disable_web_page_preview=True
        )



async def download_coroutine(bot, session, url, file_name, chat_id, message_id, start):
    downloaded = 0
    display_message = ""
    async with session.get(url, timeout=Config.TECH_VJ_PROCESS_MAX_TIMEOUT) as response:
        total_length = int(response.headers.get("Content-Length", 0))
        content_type = response.headers.get("Content-Type", "")
        if "text" in content_type.lower() and total_length < 500:
            return await response.release()
        await bot.edit_message_text(
            chat_id,
            message_id,
            text=f"Initiating Download\nURL: {url}\nFile Size: {humanbytes(total_length)}"
        )
        with open(file_name, "wb") as f_handle:
            while True:
                chunk = await response.content.read(Config.TECH_VJ_CHUNK_SIZE)
                if not chunk:
                    break
                f_handle.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                diff = now - start
                if diff > 0 and (diff % 5 < 0.6 or downloaded >= total_length):
                    try:
                        percentage = downloaded * 100 / total_length if total_length else 0
                        speed = downloaded / diff if diff > 0 else 0
                        elapsed_time = round(diff)
                        time_to_completion = round((total_length - downloaded) / speed) if speed > 0 else 0
                        estimated_total_time = elapsed_time + time_to_completion
                        current_message = (
                            f"**Download Status**\nURL: {url}\nFile Size: {humanbytes(total_length)}\n"
                            f"Downloaded: {humanbytes(downloaded)}\nETA: {TimeFormatter(estimated_total_time)}"
                        )
                        if current_message != display_message:
                            await bot.edit_message_text(chat_id, message_id, text=current_message)
                            display_message = current_message
                    except Exception as e:
                        logger.info(f"Error updating message: {e}")
        return await response.release()

