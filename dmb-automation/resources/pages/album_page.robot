*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    Process
Resource   ../locators/album_locators.robot
Resource   ../locators/login_locators.robot

*** Keywords ***
Navigate To Album Creation Form
    Wait Until Page Contains    Music    timeout=20s
    Click Element    ${MUSIC_MENU}
    Wait Until Element Is Visible    ${CREATE_ALBUM_LINK}    timeout=20s
    Sleep    1s
    Click Element    ${CREATE_ALBUM_LINK}
    Sleep    5s

Select Album Format And Next
    Select Frame    ${MAIN_IFRAME}
    Wait Until Page Contains Element    ${MAXI_SINGLE_OPTION}    timeout=20s
    ${maxi_element}=    Get WebElement    ${MAXI_SINGLE_OPTION}
    Execute Javascript    arguments[0].click();    ARGUMENTS    ${maxi_element}
    Sleep    1s
    Wait Until Page Contains Element    ${NEXT_BUTTON}    timeout=10s
    ${next_element}=    Get WebElement    ${NEXT_BUTTON}
    Execute Javascript    arguments[0].click();    ARGUMENTS    ${next_element}
    Sleep    2s

Generate EAN Code
    Wait Until Element Is Visible    ${GENERATE_EAN_BUTTON}    timeout=20s
    Click Element    ${GENERATE_EAN_BUTTON}
    Sleep    1s

Upload Cover Image
    [Arguments]    ${cover_path}
    # Fail hard if the cover file is missing — a release must never proceed without art.
    File Should Exist    ${cover_path}    msg=Cover file not found: ${cover_path}
    Wait Until Page Contains Element    //input[@type='file']    timeout=100s
    Choose File    //input[@type='file']    ${cover_path}
    Sleep    2s
    Log    ✅ Cover upload completed

Fill Album Title
    [Arguments]    ${title}
    Wait Until Element Is Visible    ${TITLE_INPUT}    timeout=20s
    Input Text    ${TITLE_INPUT}    ${title}
    Press Keys    ${TITLE_INPUT}    TAB

Set Language To English
    Click Element    ${LANGUAGE_SELECT}
    Click Element    ${ENGLISH_OPTION}
    Click Element    ${LANGUAGE_SELECT}

Select Genre
    [Arguments]    ${genre}
    Wait Until Element Is Visible    ${GENRE_INPUT}    timeout=20s
    Click Element    ${GENRE_INPUT}
    Input Text    ${GENRE_INPUT}    ${genre}
    Sleep    1s
    # Select the autocomplete row whose text matches the requested genre exactly.
    ${genre_option}=    Set Variable    //tr[.//td[normalize-space()='${genre}']]
    Wait Until Element Is Visible    ${genre_option}    timeout=15s
    ${genre_element}=    Get WebElement    ${genre_option}
    Execute Javascript    arguments[0].click();    ARGUMENTS    ${genre_element}

Input Date And Trigger Vue
    [Arguments]    ${locator}    ${date_value}
    Scroll Element Into View    ${locator}
    Wait Until Element Is Visible    ${locator}    timeout=20s
    Click Element    ${locator}
    Input Text    ${locator}    ${date_value}
    Press Keys    ${locator}    TAB
    Wait Until Element Is Visible    //body    timeout=15s

Set Release Dates
    [Arguments]    ${start_date}    ${end_date}
    Input Date And Trigger Vue    ${SALES_START_DATE}    ${start_date}
    Input Date And Trigger Vue    ${SALES_END_DATE}    ${end_date}

Set Copyright Details
    [Arguments]    ${year}    ${text}
    # C line
    Input Text    ${C_LINE_YEAR}    ${year}
    Wait Until Element Is Visible    ${C_LINE_TEXT}    timeout=20s
    Click Element    ${C_LINE_TEXT}
    Input Text    ${C_LINE_TEXT}    ${text}
    Sleep    1s
    # صبر برای باز شدن popup و انتخاب گزینه دوم
    Wait Until Element Is Visible    ${C_LINE_POPUP_OPTION}    timeout=15s
    Click Element    ${C_LINE_POPUP_OPTION}
    Sleep    0.5s
    
    # P line
    Input Text    ${P_LINE_YEAR}    ${year}
    Wait Until Element Is Visible    ${P_LINE_TEXT}    timeout=20s
    Click Element    ${P_LINE_TEXT}
    Input Text    ${P_LINE_TEXT}    ${text}
    Sleep    1s
    # صبر برای باز شدن popup و انتخاب گزینه دوم
    Wait Until Element Is Visible    ${P_LINE_POPUP_OPTION}    timeout=15s
    Click Element    ${P_LINE_POPUP_OPTION}
    Sleep    0.5s
    
    Press Keys    ${P_LINE_TEXT}    TAB
    Sleep    1s


Set Price Codes
    # Price code معمولی - انتخاب MA با JavaScript
    Execute Javascript
    ...    var select = document.querySelector('select[name="pricecode"]');
    ...    if(select) {
    ...        select.value = 'MA';
    ...        select.dispatchEvent(new Event('change', {bubbles: true}));
    ...    }
    Sleep    0.5s
    
    # Price code iTunes - انتخاب Digital 45 (value='14')
    Execute Javascript
    ...    var select = document.querySelector('select[name="pricecodeItunes"]');
    ...    if(select) {
    ...        select.value = '14';
    ...        select.dispatchEvent(new Event('change', {bubbles: true}));
    ...    }
    Sleep    0.5s
    
    Log    ✅ Price codes set successfully


Add Contributor
    [Arguments]    ${artist_name}
    Scroll Element Into View    ${NEXT_BUTTON}
    # وارد کردن نام هنرمند
    Wait Until Element Is Visible    ${CONTRIBUTOR_NAME_INPUT}    timeout=20s
    Click Element    ${CONTRIBUTOR_NAME_INPUT}
    Input Text    ${CONTRIBUTOR_NAME_INPUT}    ${artist_name}
    Sleep    1s
    
    # صبر برای باز شدن popup و انتخاب گزینه
    ${popup_exists}=    Run Keyword And Return Status    Wait Until Element Is Visible    //table[contains(@class, 'vc-js-ajax-result-list')]//tr/td    timeout=5s
    Run Keyword If    ${popup_exists}    Click Element    //table[contains(@class, 'vc-js-ajax-result-list')]//tr[1]/td
    Sleep    1s
    
    # حذف Composer (کلیک روی ×)
    ${composer_exists}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${REMOVE_COMPOSER}    timeout=30s
    Run Keyword If    ${composer_exists}    Click Element    ${REMOVE_COMPOSER}
    Sleep    0.5s
    
    # حذف Lyricist (کلیک روی ×)
    ${lyricist_exists}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${REMOVE_LYRICIST}    timeout=30s
    Run Keyword If    ${lyricist_exists}    Click Element    ${REMOVE_LYRICIST}
    Sleep    0.5s
    
    # کلیک روی دکمه Add
    Wait Until Element Is Enabled    ${ADD_CONTRIBUTOR_BUTTON}    timeout=50s
    Click Element    ${ADD_CONTRIBUTOR_BUTTON}
    Sleep    2s
    
    Log    ✅ Contributor added successfully



Click Next Button
    # صبر برای فعال شدن دکمه Next
    Wait Until Element Is Enabled    ${NEXT_BUTTON}    timeout=20s
    
    # اسکرول به پایین برای دیدن دکمه
    Scroll Element Into View    ${NEXT_BUTTON}
    Sleep    1s
    
    # کلیک روی Next
    Click Element    ${NEXT_BUTTON}
    Sleep    5s
    
    Log    ✅ Navigated to next step


Upload Track
    [Arguments]    ${music_path}
    # Fail hard if the audio file is missing — a release must never proceed without a track.
    File Should Exist    ${music_path}    msg=Music file not found: ${music_path}

    # پیدا کردن input file و آپلود
    Execute Javascript
    ...    var container = document.querySelector('div.moxie-shim-html5');
    ...    if(container) {
    ...        var input = container.querySelector('input[type="file"]');
    ...        if(input) {
    ...            input.style.opacity = '1';
    ...            input.style.visibility = 'visible';
    ...            input.style.display = 'block';
    ...            input.style.position = 'relative';
    ...            input.style.zIndex = '9999';
    ...            input.style.width = '200px';
    ...            input.style.height = '40px';
    ...            input.id = 'track-file-input';
    ...        }
    ...    }
    Sleep    1s

    Choose File    id=track-file-input    ${music_path}
    Sleep    2s

    Log    ✅ Track uploaded successfully


Fill Track Info And Generate ISRC
    [Arguments]    ${track_title}
    
    # ۱. کلیک روی Generate all ISRCs (از header)
    Wait Until Element Is Visible    //a[@data-tippy-content='Generate all ISRCs']    timeout=10s
    Click Element    //a[@data-tippy-content='Generate all ISRCs']
    Sleep    2s
    
    # ۲. پر کردن Title با JavaScript (پیدا کردن ردیف visible)
    Execute Javascript
    ...    var rows = document.querySelectorAll('tbody tr.track');
    ...    for(var row of rows) {
    ...        if(row.style.display !== 'none') {
    ...            var titleInput = row.querySelector('input[name="track:title[]"]');
    ...            if(titleInput) {
    ...                titleInput.value = '${track_title}';
    ...                titleInput.dispatchEvent(new Event('input', {bubbles: true}));
    ...                titleInput.dispatchEvent(new Event('change', {bubbles: true}));
    ...                break;
    ...            }
    ...        }
    ...    }
    Sleep    2s
    
    Log    ✅ Track info filled successfully

Click Next And Wait For Upload
    # کلیک روی Next
    Wait Until Element Is Enabled    ${NEXT_BUTTON}    timeout=10s
    Scroll Element Into View    ${NEXT_BUTTON}
    Sleep    1s
    Click Element    ${NEXT_BUTTON}
    
    # صبر تا تکمیل آپلود و لود صفحه بعدی
    Wait Until Page Contains Element    
    ...    //table[contains(@class, 'AlbumUploadTrackTable')]//tr[contains(@class, 'track')]//input[@name='track:filename[]' and not(@value='')]    
    ...    timeout=120s
    
    Sleep    3s
    Log    ✅ Upload completed and next page loaded



Select Worldwide And Next
    # ۱. کلیک روی دکمه Worldwide
    Wait Until Element Is Visible    //label[contains(text(), 'Worldwide')]    timeout=10s
    Click Element    //label[contains(text(), 'Worldwide')]
    Sleep    1s
    
    # ۲. کلیک روی Next
    Wait Until Element Is Enabled    ${NEXT_BUTTON}    timeout=10s
    Scroll Element Into View    ${NEXT_BUTTON}
    Sleep    1s
    Click Element    ${NEXT_BUTTON}
    
    # . صبر برای لود صفحه بعدی
    Wait Until Page Contains Element    //body    timeout=15s
    Sleep    3s
    
    Log    ✅ Worldwide selected and navigated to next step