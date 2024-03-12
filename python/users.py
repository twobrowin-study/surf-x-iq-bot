from datetime import datetime
from telegram import (
    Update
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from spreadsheetbot.sheets.i18n import I18n
from spreadsheetbot.sheets.settings import Settings
from spreadsheetbot.sheets.registration import Registration
from spreadsheetbot.sheets.groups import Groups
from spreadsheetbot.sheets.report import Report
from spreadsheetbot.sheets.keyboard import Keyboard

from spreadsheetbot.basic.log import Log

from spreadsheetbot.sheets.users import UsersAdapterClass

from survey import Survey

async def proceed_registration_handler(self: UsersAdapterClass, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user    = self.get(update.effective_chat.id)
    state   = user.state
    save_as = user[Settings.user_document_name_field]
    registration_curr = Registration.get(state)
    registration_next = Registration.get_next(state)

    last_main_state    = (state == Registration.last_main_state)
    first_survey_state = (state == Registration.first_survey_state)
    last_survey_state  = (state == Registration.last_survey_state)

    state_val, save_to = self._prepare_state_to_save(update.message, registration_curr.document_link)
    if state_val == None:
        await update.message.reply_markdown(registration_curr.question, reply_markup=registration_curr.reply_keyboard)
        return

    if last_main_state:
        await update.message.reply_markdown(Settings.registration_complete, reply_markup=Keyboard.reply_keyboard)
    elif last_survey_state:
        await update.message.reply_markdown(Settings.survey_complete, reply_markup=Keyboard.reply_keyboard)
    else:
        await update.message.reply_markdown(registration_next.question, reply_markup=registration_next.reply_keyboard)

    update_vals = {state: state_val}
    if last_main_state:
        update_vals['is_active'] = I18n.yes

    if first_survey_state:
        update_vals['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_vals['chat_id']  = user['chat_id']
        update_vals['username'] = user['username']
        update_vals[Settings.survey_name_column] = user[Settings.survey_name_column]
    
    if not registration_curr.is_survey_question:
        await self._batch_update_or_create_record(update.effective_chat.id, save_to=save_to, save_as=save_as, app=context.application,
            state = '' if last_main_state else registration_next.state,
            **update_vals
        )
    else:
        await self._update_record(update.effective_chat.id, 'state', '' if last_survey_state else registration_next.state)
        await Survey._batch_update_or_create_record(update.effective_chat.id, save_to=save_to, save_as=save_as, app=context.application,
            first_state=first_survey_state,
            **update_vals
        )

    count = self.active_user_count()
    if last_main_state and self.should_send_report(count):
        Groups.send_to_all_admin_groups(
            context.application,
            Report.currently_active_users_template.format(count=count),
            ParseMode.MARKDOWN
        )
    
    if last_survey_state:
        Log.info(f"Starting update of whole df {Report.name} to send after last survey state")
        Report.whole_mutex = True
        await Report._update_df()
        Report.whole_mutex = False

        Log.info(f"Updated whole df {Report.name} to send after last survey state")
        await Report._post_update()

        Log.info(f"Sending {Report.name} to all admins after last survey state")
        Groups.send_to_all_admin_groups(
            context.application,
            Report.markdown,
            ParseMode.MARKDOWN
        )
UsersAdapterClass.proceed_registration_handler = proceed_registration_handler