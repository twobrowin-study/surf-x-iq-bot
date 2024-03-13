from spreadsheetbot.sheets.report import ReportAdapterClass

ReportAdapterClass.default_process_df_update = ReportAdapterClass._process_df_update
async def _process_df_update(self: ReportAdapterClass):
    await self.default_process_df_update()

    self.markdown = "\n\n".join([
        f"{row.title}: `{row.value}`"
        for _,row in self.as_df.iterrows()
    ])
ReportAdapterClass._process_df_update = _process_df_update