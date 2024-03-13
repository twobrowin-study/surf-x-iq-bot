from telegram import Bot, InlineKeyboardMarkup
from telegram.ext import Application

from typing import Coroutine, Any

from spreadsheetbot.sheets.abstract import AbstractSheetAdapter

def _get_send_to_all_uids_coroutines(self, selector, app: Application, message: str, parse_mode: str, 
    send_photo: str = None, reply_markup: InlineKeyboardMarkup = None
) -> list[Coroutine[Any, Any, Any]]:
    bot: Bot = app.bot
    if send_photo not in [None, '']:
        return [
            bot.send_photo(
                chat_id=row[self.uid_col],
                message_thread_id=row['thread_id'] if 'thread_id' in row else None,
                photo=send_photo,
                caption=message,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            for _,row in self.as_df.loc[selector].iterrows()
        ]
    return [
        bot.send_message(
            chat_id=row[self.uid_col],
            message_thread_id=row['thread_id'] if 'thread_id' in row else None,
            text=message,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
        for _,row in self.as_df.loc[selector].iterrows()
    ]
AbstractSheetAdapter._get_send_to_all_uids_coroutines = _get_send_to_all_uids_coroutines