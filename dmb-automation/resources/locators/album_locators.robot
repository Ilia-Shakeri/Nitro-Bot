*** Variables ***
# --- المان‌های انتخاب فرمت آلبوم ---
${MAXI_SINGLE_OPTION}       xpath=//*[normalize-space()='(Maxi-) Single']
${NEXT_BUTTON}              //button[normalize-space()='Next']

# --- فیلدهای اصلی فرم ---
${EAN_INPUT}                //input[@name='eanUpc']
${TITLE_INPUT}              //input[@name='title']
${LANGUAGE_SELECT}          //select[@name='language']
${ENGLISH_OPTION}           //option[@value='en']
${GENRE_INPUT}              //input[@name='genre']
# Genre autocomplete rows are matched dynamically by text in the "Select Genre" keyword.

# --- تاریخ‌ها (بدون Pre-order) ---
${SALES_START_DATE}         //input[@name='salesStartDate']
${SALES_END_DATE}           //input[@name='salesEndDate']

# --- کپی‌رایت ---
${C_LINE_YEAR}              //input[@name='c_line_year']
${P_LINE_YEAR}              //input[@name='p_line_year']
${C_LINE_TEXT}              //input[@name='c_line_text']
${P_LINE_TEXT}              //input[@name='p_line_text']

# --- Popup نتایج برای C line و P line ---
${C_LINE_POPUP_OPTION}      //table[contains(@class, 'vc-js-ajax-result-list')]//tr[2]/td
${P_LINE_POPUP_OPTION}      //table[contains(@class, 'vc-js-ajax-result-list')]//tr[2]/td

# --- آپلود فایل‌ها ---
${COVER_FILE_INPUT}         //input[@type='file' and contains(@accept, 'image')]

# --- دکمه‌ها ---
${GENERATE_EAN_BUTTON}      //a[@data-tippy-content='Generate EAN']


# --- Price Code ---
${PRICE_CODE_SELECT}            //select[@name='pricecode']
${PRICE_CODE_ITUNES_SELECT}     //select[@name='pricecodeItunes']
${PRICE_CODE_OPTION_MA}         //option[@value='MA']
${PRICE_CODE_ITUNES_OPTION_14}  //option[@value='14']

# --- Add Contributor ---
${CONTRIBUTOR_NAME_INPUT}     //input[@name='newArtist']
${REMOVE_COMPOSER}            //li[@title='Composer']//span[@class='select2-selection__choice__remove']
${REMOVE_LYRICIST}            //li[@title='Lyricist']//span[@class='select2-selection__choice__remove']
${ADD_CONTRIBUTOR_BUTTON}     //button[contains(@class, 'dmb-js-cce__add-btn')]

# --- دکمه‌ها ---
${NEXT_BUTTON}              //button[normalize-space()='Next']
${SAVE_BUTTON}              //button[contains(text(), 'Save')]