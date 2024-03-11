import pandas as pd

from spreadsheetbot.sheets.registration import RegistrationAdapterClass

from spreadsheetbot.sheets.i18n import I18n

async def _get_df(self: RegistrationAdapterClass) -> pd.DataFrame:
    df = pd.DataFrame(await self.wks.get_all_records())
    df = df.drop(index = 0, axis = 0)
    df = df.loc[
        (df.state != "") &
        (df.question != "") &
        (df.is_main_question.isin(I18n.yes_no + [I18n.survey]))
    ]
    df['is_survey_question'] = df.is_main_question.apply(lambda x: x == I18n.survey)
    df.is_main_question = df.is_main_question.apply(lambda x: x == I18n.yes)
    return df
RegistrationAdapterClass._get_df = _get_df

async def _process_df_update(self: RegistrationAdapterClass):
    main_selector = self.as_df.is_main_question == True
    survey_selector = self.as_df.is_survey_question == True
    
    self.first = self._get(main_selector)
    
    self.states = self.as_df.state.values
    self.main_states   = self.as_df.loc[main_selector].state.values
    self.survey_states = self.as_df.loc[survey_selector].state.values

    self.last_state         = self.states[-1]
    self.last_main_state    = self.main_states[-1]
    self.last_survey_state  = self.survey_states[-1]
    self.first_survey_state = self.survey_states[0]

    self.is_document_state = lambda state: self.get(state).document_link not in ["", None]
RegistrationAdapterClass._process_df_update = _process_df_update