#port to userbot by @MoveAngel

import asyncio
import os
import time
import zipfile

from telethon import events
from userbot.events import register
from userbot import bot, CMD_HELP, TMP_DOWNLOAD_DIRECTORY
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeVideo
from userbot.modules.upload_download import humanbytes, progress, time_formatter
import time
from datetime import datetime
from pySmartDL import SmartDL
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from zipfile import ZipFile



extracted = TMP_DOWNLOAD_DIRECTORY + "extracted/"
thumb_image_path = TMP_DOWNLOAD_DIRECTORY + "/thumb_image.jpg"
if not os.path.isdir(extracted):
    os.makedirs(extracted)


@register(outgoing=True, pattern=r".unzip (.*)")
async def extract(zarchiver):
    if zarchiver.fwd_from:
        return
    mone = await zarchiver.edit("Processing ...")
    if not os.path.isdir(TMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TMP_DOWNLOAD_DIRECTORY)
    if zarchiver.reply_to_msg_id:
        start = datetime.now()
        reply_message = await zarchiver.get_reply_message()
        try:
            c_time = time.time()
            downloaded_file_name = await bot.download_media(
                reply_message,
                TMP_DOWNLOAD_DIRECTORY,
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(d, t, mone, c_time, "trying to download")
                )
            )
        except Exception as e:  # pylint:disable=C0103,W0703
            await mone.edit(str(e))
        else:
            end = datetime.now()
            ms = (end - start).seconds
            await mone.edit("Stored the zip to `{}` in {} seconds.".format(downloaded_file_name, ms))

        with zipfile.ZipFile(downloaded_file_name, 'r') as zip_ref:
            zip_ref.extractall(extracted)
        filename = sorted(get_lst_of_files(extracted, []))
        #filename = filename + "/"
        await zarchiver.edit("Unzipping now")
        # r=root, d=directories, f = files
        for single_file in filename:
            if os.path.exists(single_file):
                # https://stackoverflow.com/a/678242/4723940
                caption_rts = os.path.basename(single_file)
                force_document = True
                supports_streaming = False
                document_attributes = []
                if single_file.endswith((".mp4", ".mp3", ".flac", ".webm")):
                    metadata = extractMetadata(createParser(single_file))
                    duration = 0
                    width = 0
                    height = 0
                    if metadata.has("duration"):
                        duration = metadata.get('duration').seconds
                    if os.path.exists(thumb_image_path):
                        metadata = extractMetadata(createParser(thumb_image_path))
                        if metadata.has("width"):
                            width = metadata.get("width")
                        if metadata.has("height"):
                            height = metadata.get("height")
                    document_attributes = [
                        DocumentAttributeVideo(
                            duration=duration,
                            w=width,
                            h=height,
                            round_message=False,
                            supports_streaming=True
                        )
                    ]
                try:
                    await bot.send_file(
                        zarchiver.chat_id,
                        single_file,
                        caption=f"UnZipped `{caption_rts}`",
                        force_document=force_document,
                        supports_streaming=supports_streaming,
                        allow_cache=False,
                        reply_to=zarchiver.message.id,
                        attributes=document_attributes,
                        # progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                        #     progress(d, t, event, c_time, "trying to upload")
                        # )
                    )
                except Exception as e:
                    await bot.send_message(
                        zarchiver.chat_id,
                        "{} caused `{}`".format(caption_rts, str(e)),
                        reply_to=zarchiver.message.id
                    )
                    # some media were having some issues
                    continue
                os.remove(single_file)
        os.remove(downloaded_file_name)



def get_lst_of_files(input_directory, output_lst):
    filesinfolder = os.listdir(input_directory)
    for file_name in filesinfolder:
        current_file_name = os.path.join(input_directory, file_name)
        if os.path.isdir(current_file_name):
            return get_lst_of_files(current_file_name, output_lst)
        output_lst.append(current_file_name)
    return output_lst

CMD_HELP.update({
        "unzip": 
        ".unzip \
          \nUsage: Unzip ur file or something.\n"
    })