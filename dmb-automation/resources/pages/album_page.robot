*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    String
Resource   ../locators/album_locators.robot
Resource   ../locators/login_locators.robot

*** Keywords ***
Navigate To Album Creation Form
    Wait Until Element Is Visible    ${MUSIC_MENU}    timeout=30s
    Click Element    ${MUSIC_MENU}
    Wait Until Element Is Visible    ${CREATE_ALBUM_LINK}    timeout=20s
    Click Element    ${CREATE_ALBUM_LINK}
    Wait Until Element Is Visible    ${MAIN_IFRAME}    timeout=30s

Select Album Format And Next
    Select Frame    ${MAIN_IFRAME}
    Wait Until Element Is Visible    ${MAXI_SINGLE_OPTION}    timeout=30s
    Click Element    ${MAXI_SINGLE_OPTION}
    Click Ready Next
    Wait Until Element Is Visible    ${EAN_INPUT}    timeout=30s

Click Ready Next
    Wait Until Element Is Enabled    ${NEXT_BUTTON}    timeout=30s
    Scroll Element Into View    ${NEXT_BUTTON}
    Click Element    ${NEXT_BUTTON}

Generate EAN Code
    Wait Until Element Is Visible    ${GENERATE_EAN_BUTTON}    timeout=20s
    Click Element    ${GENERATE_EAN_BUTTON}
    Wait Until Keyword Succeeds    30s    1s    EAN Should Be Generated
    ${ean}=    Get Value    ${EAN_INPUT}
    RETURN    ${ean}

EAN Should Be Generated
    ${ean}=    Get Value    ${EAN_INPUT}
    Should Match Regexp    ${ean}    ^[0-9]{8,14}$

Upload Cover Image
    [Arguments]    ${cover_path}
    File Should Exist    ${cover_path}    msg=Cover file not found: ${cover_path}
    Wait Until Page Contains Element    ${COVER_FILE_INPUT}    timeout=30s
    Choose File    ${COVER_FILE_INPUT}    ${cover_path}
    Wait Until Keyword Succeeds    60s    1s    Cover Input Should Have File

Cover Input Should Have File
    ${value}=    Get Value    ${COVER_FILE_INPUT}
    Should Not Be Empty    ${value}

Fill Album Title
    [Arguments]    ${title}
    Wait Until Element Is Visible    ${TITLE_INPUT}    timeout=20s
    Input Text    ${TITLE_INPUT}    ${title}
    Press Keys    ${TITLE_INPUT}    TAB

Set Language To English
    Select From List By Value    ${LANGUAGE_SELECT}    en
    ${language}=    Get Selected List Value    ${LANGUAGE_SELECT}
    Should Be Equal As Strings    ${language}    en

Select DMB Genre
    [Arguments]    ${dmb_genre}
    Wait Until Element Is Visible    ${GENRE_INPUT}    timeout=20s
    Input Text    ${GENRE_INPUT}    ${dmb_genre}
    ${genre_option}=    Replace String    ${AJAX_EXACT_OPTION}    __VALUE__    ${dmb_genre}
    Wait Until Element Is Visible    ${genre_option}    timeout=20s
    Click Element    ${genre_option}
    Wait Until Keyword Succeeds    10s    1s    Genre Should Be Selected    ${dmb_genre}

Genre Should Be Selected
    [Arguments]    ${dmb_genre}
    ${value}=    Get Value    ${GENRE_INPUT}
    Should Be Equal As Strings    ${value}    ${dmb_genre}

Fill Ajax Value
    [Arguments]    ${locator}    ${value}
    Wait Until Element Is Visible    ${locator}    timeout=20s
    Input Text    ${locator}    ${value}
    ${exact_option}=    Replace String    ${AJAX_EXACT_OPTION}    __VALUE__    ${value}
    Wait Until Element Is Visible    ${exact_option}    timeout=20s
    Click Element    ${exact_option}

Set Label
    [Arguments]    ${label}
    Select From List By Label    ${LABEL_SELECT}    ${label}
    ${selected_label}=    Get Selected List Label    ${LABEL_SELECT}
    Should Be Equal As Strings    ${selected_label}    ${label}

Input Date And Confirm
    [Arguments]    ${locator}    ${date_value}
    Wait Until Element Is Visible    ${locator}    timeout=20s
    Press Keys    ${locator}    CTRL+A
    Input Text    ${locator}    ${date_value}
    Press Keys    ${locator}    TAB
    ${actual_date}=    Get Value    ${locator}
    Should Be Equal As Strings    ${actual_date}    ${date_value}

Set Release Dates
    [Arguments]    ${start_date}    ${end_date}
    ${dmb_start_date}=    Format Dmb Date    ${start_date}
    ${dmb_end_date}=    Format Dmb Date    ${end_date}
    Input Date And Confirm    ${SALES_START_DATE}    ${dmb_start_date}
    Input Date And Confirm    ${SALES_END_DATE}    ${dmb_end_date}

Set Price Codes
    [Arguments]    ${price_code}    ${itunes_price_code}
    Select From List By Value    ${PRICE_CODE_SELECT}    ${price_code}
    Select From List By Value    ${PRICE_CODE_ITUNES_SELECT}    ${itunes_price_code}
    ${selected_price}=    Get Selected List Value    ${PRICE_CODE_SELECT}
    ${selected_itunes}=    Get Selected List Value    ${PRICE_CODE_ITUNES_SELECT}
    Should Be Equal As Strings    ${selected_price}    ${price_code}
    Should Be Equal As Strings    ${selected_itunes}    ${itunes_price_code}

Set Copyright Details
    [Arguments]    ${c_year}    ${p_year}    ${label}
    Input Text    ${C_LINE_YEAR}    ${c_year}
    Fill Ajax Value    ${C_LINE_TEXT}    ${label}
    Input Text    ${P_LINE_YEAR}    ${p_year}
    Fill Ajax Value    ${P_LINE_TEXT}    ${label}

Add DMB Contributor
    [Arguments]    ${name}    ${has_account}
    Wait Until Element Is Visible    ${CONTRIBUTOR_NAME_INPUT}    timeout=20s
    Input Text    ${CONTRIBUTOR_NAME_INPUT}    ${name}
    IF    ${has_account}
        ${contributor_option}=    Replace String    ${AJAX_EXACT_OPTION}    __VALUE__    ${name}
        Wait Until Element Is Visible    ${contributor_option}    timeout=20s
        Click Element    ${contributor_option}
    ELSE
        Press Keys    ${CONTRIBUTOR_NAME_INPUT}    TAB
        Keep Only Performer Role
    END
    Wait Until Element Is Enabled    ${ADD_CONTRIBUTOR_BUTTON}    timeout=20s
    Click Element    ${ADD_CONTRIBUTOR_BUTTON}
    Wait Until Keyword Succeeds    20s    1s    Page Should Contain    ${name}

Keep Only Performer Role
    Unselect All From List    ${CONTRIBUTOR_ROLES_SELECT}
    Select From List By Label    ${CONTRIBUTOR_ROLES_SELECT}    Performer
    @{selected_roles}=    Get Selected List Labels    ${CONTRIBUTOR_ROLES_SELECT}
    ${role_count}=    Get Length    ${selected_roles}
    Should Be Equal As Integers    ${role_count}    1
    Should Be Equal As Strings    ${selected_roles}[0]    Performer

Apply Contributors To Tracks
    Select Checkbox    ${APPLY_CONTRIBUTORS_TO_TRACKS}
    Checkbox Should Be Selected    ${APPLY_CONTRIBUTORS_TO_TRACKS}

Open Add Tracks
    Wait Until Page Contains Element    ${TRACK_FILE_INPUT}    timeout=30s

Upload Track
    [Arguments]    ${music_path}
    File Should Exist    ${music_path}    msg=Music file not found: ${music_path}
    Choose File    ${TRACK_FILE_INPUT}    ${music_path}
    Wait Until Keyword Succeeds    60s    1s    Track Input Should Have File

Track Input Should Have File
    ${value}=    Get Value    ${TRACK_FILE_INPUT}
    Should Not Be Empty    ${value}

Fill Track Info And Generate ISRC
    [Arguments]    ${track_title}
    Wait Until Element Is Visible    ${GENERATE_ALL_ISRCS}    timeout=30s
    Click Element    ${GENERATE_ALL_ISRCS}
    Wait Until Keyword Succeeds    30s    1s    ISRC Should Be Generated
    Wait Until Element Is Visible    ${TRACK_TITLE_INPUT}    timeout=20s
    Input Text    ${TRACK_TITLE_INPUT}    ${track_title}
    Press Keys    ${TRACK_TITLE_INPUT}    TAB
    ${isrc}=    Get Value    ${TRACK_ISRC_INPUT}
    RETURN    ${isrc}

ISRC Should Be Generated
    ${isrc}=    Get Value    ${TRACK_ISRC_INPUT}
    Should Match Regexp    ${isrc}    ^[A-Za-z0-9-]{8,20}$

Continue To Territory Page
    Click Ready Next
    Wait Until Element Is Visible    ${WORLDWIDE_OPTION}    timeout=180s

Select Worldwide And Next
    Wait Until Element Is Visible    ${WORLDWIDE_OPTION}    timeout=30s
    Click Element    ${WORLDWIDE_OPTION}
    Click Ready Next
    Wait Until Element Is Visible    ${ALL_PLATFORMS_BUTTON}    timeout=60s

Select All Platforms And Next
    Click Element    ${ALL_PLATFORMS_BUTTON}
    Click Ready Next
    Wait Until Element Is Visible    ${SAVE_BUTTON}    timeout=60s

Verify Review Data
    [Arguments]    ${title}    ${ean}    ${isrc}    ${release_date}    ${genre}    ${label}    ${contributors}
    Page Should Contain    ${title}
    Page Should Contain    ${ean}
    Page Should Contain    ${isrc}
    Page Should Contain    ${release_date}
    Page Should Contain    ${genre}
    Page Should Contain    ${label}
    FOR    ${contributor}    IN    @{contributors}
        Page Should Contain    ${contributor}[name]
    END

Submission Should Be Confirmed
    [Arguments]    ${before_url}
    ${success}=    Run Keyword And Return Status    Page Should Contain Element    ${SUBMISSION_SUCCESS}
    ${current_url}=    Get Location
    ${confirmed}=    Evaluate    $success or $current_url != $before_url
    Should Be True    ${confirmed}    DMB did not confirm album submission

Submit Album And Verify Success
    [Arguments]    ${release_id}
    Should Be Equal    %{DMB_SUBMIT_ENABLED}    true
    Wait Until Element Is Enabled    ${SAVE_BUTTON}    timeout=30s
    Scroll Element Into View    ${SAVE_BUTTON}
    ${before_url}=    Get Location
    Write Submit Checkpoint    %{DMB_SUBMIT_CHECKPOINT}    ${release_id}
    Click Element    ${SAVE_BUTTON}
    Wait Until Keyword Succeeds    60s    2s    Submission Should Be Confirmed    ${before_url}

Capture Failure Evidence And Close Browser
    Run Keyword And Ignore Error    Capture Page Screenshot    ${OUTPUT DIR}${/}final-state.png
    Run Keyword And Ignore Error    Close Browser Session
