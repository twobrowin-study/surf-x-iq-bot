import asyncio
import pandas as pd
from telegram import Document
from telegram.ext import Application

from spreadsheetbot.sheets.abstract import AbstractSheetAdapter

from spreadsheetbot.sheets.i18n import I18n
from spreadsheetbot.sheets.settings import Settings

from spreadsheetbot.basic.drive import SaveToDrive
from spreadsheetbot.basic.log import Log

class SurveyAdapterClass(AbstractSheetAdapter):
    def __init__(self) -> None:
        super().__init__('survey', 'survey', initialize_as_df=True)
        self.wks_row_pad = 2
        self.wks_col_pad = 1
        self.uid_col     = 'chat_id'

        self.wks_row = lambda uid: self.as_df.loc[self.selector(uid)].index.values[-1] + self.wks_row_pad
    
    async def _pre_async_init(self):
        self.sheet_name = I18n.survey
        self.update_sleep_time = Settings.survey_update_time
        self.retry_sleep_time  = Settings.retry_time
    
    async def _get_df(self) -> pd.DataFrame:
        df = pd.DataFrame(await self.wks.get_all_records())
        df.chat_id = df.chat_id.apply(str)
        return df

    async def _batch_update_or_create_record(self, uid: str|int, save_to = None, save_as = None, app: Application = None, raw: bool = True, first_state: bool = False, **record_params):
        exists = self.exists(uid) if not first_state else False
        record_action = 'update' if exists else 'create'
        collumns = record_params.keys()
        
        Log.info(f"Prepeared to batch update {record_action} record in {self.name} with {self.uid_col} {uid} and {collumns} collumns")
        while self.whole_mutex:
            Log.info(f"Halted to batch update {record_action} record in {self.name} with {self.uid_col} {uid} and {collumns} collumns with whole mutex")
            await asyncio.sleep(self.retry_sleep_time)
        self.mutex.append(uid)

        get_file = None
        for key,val in record_params.items():
            if type(val) in [list, tuple]:
                record_params[key] = val[-1].to_json()
                get_file = val[-1].get_file
            if type(val) == Document:
                record_params[key] = val.to_json()
                get_file = val.get_file
        
        if not exists:
            record_params[self.uid_col] = str(uid)
            tmp_df = pd.DataFrame(record_params, columns=self.as_df.columns, index=[0]).fillna('')
            if self.as_df.empty:
                self.as_df = tmp_df
            else:
                self.as_df = pd.concat([self.as_df, tmp_df], ignore_index=True)
        else:
            for key, value in record_params.items():
                self.as_df.loc[self.selector(uid), key] = value
        
        wks_row = self.wks_row(uid)
        wks_update = self._prepare_batch_update([
            (wks_row, self.wks_col(key), value)
            for key, value in record_params.items()
        ])
        
        await self.wks.batch_update(wks_update, raw)
        if get_file != None and save_to != None and save_as != None and app != None:
            app.create_task(
                SaveToDrive(self.agc.gc.auth.token, save_to, save_as, get_file),
                self._create_update_context('Save to drive', save_to=save_to, save_as=save_as)
            )
        
        del self.mutex[self.mutex.index(uid)]
        Log.info(f"Done batch update {record_action} record in {self.name} with {self.uid_col} {uid} and {collumns} collumns")
        Log.debug(f"Current mutext at {self.name} is {self.mutex}")


Survey = SurveyAdapterClass()