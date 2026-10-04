*** Variables ***
${CREATE_FORM_XPATH}           //form[.//button[normalize-space()='Save & View Audio Product']]
${MAXI_SINGLE_OPTION}          xpath=//*[not(self::option) and normalize-space()='(Maxi-) Single']
${NEXT_BUTTON}                 xpath=(//button[normalize-space()='Next' and not(@disabled)])[last()]

${EAN_INPUT}                   xpath=${CREATE_FORM_XPATH}//input[@name='eanUpc']
${GENERATE_EAN_BUTTON}         xpath=${CREATE_FORM_XPATH}//a[@data-tippy-content='Generate EAN']
${COVER_FILE_INPUT}            xpath=${CREATE_FORM_XPATH}//input[@type='file' and contains(@accept, 'image')]
${TITLE_INPUT}                 xpath=${CREATE_FORM_XPATH}//input[@name='title']
${LANGUAGE_SELECT}             xpath=${CREATE_FORM_XPATH}//select[@name='language']
${GENRE_INPUT}                 xpath=${CREATE_FORM_XPATH}//input[@name='genre']
${LABEL_SELECT}                xpath=${CREATE_FORM_XPATH}//select[@name='label']
${AJAX_EXACT_OPTION}           xpath=//table[contains(@class, 'vc-js-ajax-result-list')]//td[normalize-space()="__VALUE__"]

${SALES_START_DATE}            xpath=${CREATE_FORM_XPATH}//input[@name='salesStartDate']
${SALES_END_DATE}              xpath=${CREATE_FORM_XPATH}//input[@name='salesEndDate']
${DATEPICKER}                  xpath=//*[@id='ui-datepicker-div']
${PRICE_CODE_SELECT}           xpath=${CREATE_FORM_XPATH}//select[@name='pricecode']
${PRICE_CODE_ITUNES_SELECT}    xpath=${CREATE_FORM_XPATH}//select[@name='pricecodeItunes']

${C_LINE_YEAR}                 xpath=${CREATE_FORM_XPATH}//input[@name='c_line_year']
${P_LINE_YEAR}                 xpath=${CREATE_FORM_XPATH}//input[@name='p_line_year']
${C_LINE_TEXT}                 xpath=${CREATE_FORM_XPATH}//input[@name='c_line_text']
${P_LINE_TEXT}                 xpath=${CREATE_FORM_XPATH}//input[@name='p_line_text']

${CONTRIBUTOR_NAME_INPUT}      xpath=${CREATE_FORM_XPATH}//input[@name='newArtist']
${CONTRIBUTOR_ROLES_SELECT}    xpath=(${CREATE_FORM_XPATH}//select[@name='cce_roles[][]'])[last()]
${ADD_CONTRIBUTOR_BUTTON}      xpath=${CREATE_FORM_XPATH}//button[contains(@class, 'dmb-js-cce__add-btn')]

${ADD_TRACKS_BUTTON}           xpath=//*[self::button or self::a][normalize-space()='Add Tracks']
${TRACK_FILE_INPUT}            xpath=//input[@type='file' and not(contains(@accept,'image'))]
${GENERATE_ALL_ISRCS}          xpath=//a[@data-tippy-content='Generate all ISRCs']

${WORLDWIDE_OPTION}            xpath=//label[contains(normalize-space(.), 'Worldwide')]
${ALL_PLATFORMS_BUTTON}        xpath=//a[@title='Add all to right side']
${ASSIGNED_PLATFORMS}          xpath=//select[contains(concat(' ', normalize-space(@class), ' '), ' assigned ')]/option
${SAVE_BUTTON}                 xpath=${CREATE_FORM_XPATH}//button[normalize-space()='Save & View Audio Product']
${SUBMISSION_SUCCESS}          xpath=//*[contains(@class,'success') and (contains(normalize-space(.),'created') or contains(normalize-space(.),'saved'))]
