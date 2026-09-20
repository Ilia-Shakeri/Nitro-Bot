*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    String
Resource   ../locators/edit_album_locators.robot
Resource   ../variables/global_vars.robot

*** Keywords ***
Open Single Track Metadata Editor
    [Arguments]    ${dmb_release_id}
    ${layer}=    Set Variable    page%2Ftrack-edit-metadata%3FtargetAlbumId%3D${dmb_release_id}
    Go To    ${LOGIN_URL}page/albums?dmbOpenLayerURL=${layer}
    Wait Until Element Is Visible    ${TRACK_EDIT_IFRAME}    timeout=30s
    Select Frame    ${TRACK_EDIT_IFRAME}
    Wait Until Element Is Visible    ${TRACK_EDIT_ACTION}    timeout=30s
    Click Element    ${TRACK_EDIT_ACTION}
    Click Element    ${TRACK_EDIT_NEXT}
    Wait Until Element Is Visible    ${TRACK_EDIT_FORM}    timeout=30s

Fill Single Track Metadata
    [Arguments]    ${job}
    Replace Edit Text    ${TRACK_EDIT_TITLE}    ${job}[song_name]
    Select Checkbox    ${TRACK_EDIT_FIELD_TITLE}
    Select Edit Ajax Value    ${TRACK_EDIT_GENRE}    ${job}[dmb_genre]
    Select Checkbox    ${TRACK_EDIT_FIELD_GENRE}
    IF    ${job}[explicit_content]
        Select From List By Value    ${TRACK_EDIT_EXPLICIT}    explicit
    ELSE
        Select From List By Value    ${TRACK_EDIT_EXPLICIT}    normal
    END
    Select Checkbox    ${TRACK_EDIT_FIELD_EXPLICIT}
    Replace Edit Text    ${TRACK_EDIT_P_YEAR}    ${job}[p_line_year]
    Select Edit Ajax Value    ${TRACK_EDIT_P_TEXT}    ${job}[label]
    Select Checkbox    ${TRACK_EDIT_FIELD_P_LINE}
    Replace Track Contributors    ${job}[contributors]
    Select From List By Value    ${TRACK_EDIT_CONTRIBUTOR_MODE}    apply
    Select Checkbox    ${TRACK_EDIT_FIELD_CONTRIBUTORS}
    Click Element    ${TRACK_EDIT_NEXT}
    Wait Until Element Is Visible    ${TRACK_EDIT_SAVE}    timeout=30s
    ${track_count}=    Get Element Count    ${TRACK_EDIT_SELECTED_TRACK}
    Should Be Equal As Integers    ${track_count}    1
    Page Should Contain    ${job}[source_dmb_isrcs][0]

Replace Track Contributors
    [Arguments]    ${contributors}
    ${count}=    Get Element Count    ${TRACK_EDIT_CONTRIBUTOR_ROW}
    WHILE    ${count} > 0
        Click Element    ${TRACK_EDIT_REMOVE_CONTRIBUTOR}
        Wait Until Keyword Succeeds    10s    500ms    Track Contributor Count Should Drop    ${count}
        ${count}=    Get Element Count    ${TRACK_EDIT_CONTRIBUTOR_ROW}
    END
    FOR    ${contributor}    IN    @{contributors}
        Add Track Contributor    ${contributor}[name]    ${contributor}[has_account]
    END

Track Contributor Count Should Drop
    [Arguments]    ${old_count}
    ${new_count}=    Get Element Count    ${TRACK_EDIT_CONTRIBUTOR_ROW}
    Should Be True    ${new_count} < ${old_count}

Add Track Contributor
    [Arguments]    ${name}    ${has_account}
    Input Text    ${TRACK_EDIT_CONTRIBUTOR_NAME}    ${name}
    IF    ${has_account}
        ${option}=    Replace String    ${EDIT_AJAX_OPTION}    __VALUE__    ${name}
        Wait Until Element Is Visible    ${option}    timeout=20s
        Click Element    ${option}
    ELSE
        Press Keys    ${TRACK_EDIT_CONTRIBUTOR_NAME}    TAB
        Unselect All From List    ${TRACK_EDIT_CONTRIBUTOR_ROLES}
        Select From List By Label    ${TRACK_EDIT_CONTRIBUTOR_ROLES}    Performer
    END
    Click Element    ${TRACK_EDIT_ADD_CONTRIBUTOR}
    Wait Until Keyword Succeeds    20s    1s    Page Should Contain    ${name}

Save Single Track Metadata
    Click Element    ${TRACK_EDIT_SAVE}
    Wait Until Keyword Succeeds    60s    2s    Page Should Not Contain Element    ${TRACK_EDIT_SAVE}
    Unselect Frame

Open Source Album In Edit Mode
    [Arguments]    ${dmb_release_id}
    Go To    ${LOGIN_URL}page/album/${dmb_release_id}
    Wait Until Element Is Visible    ${EDIT_IFRAME}    timeout=30s
    Select Frame    ${EDIT_IFRAME}
    Wait Until Element Is Visible    ${EDIT_FORM}    timeout=30s
    Page Should Contain Element    ${EDIT_SAVE_ACTION}
    Page Should Contain Element    ${EDIT_PUBLISH_ACTION}

Verify Source Album Identity
    [Arguments]    ${expected_dmb_id}    ${expected_ean}
    ${current_url}=    Get Location
    Should Contain    ${current_url}    /page/album/${expected_dmb_id}
    ${actual_ean}=    Get Value    ${EDIT_EAN}
    Should Be Equal As Strings    ${actual_ean}    ${expected_ean}

Replace Edit Text
    [Arguments]    ${locator}    ${value}
    Wait Until Element Is Visible    ${locator}    timeout=20s
    Press Keys    ${locator}    CTRL+A
    Input Text    ${locator}    ${value}
    Press Keys    ${locator}    TAB
    ${actual}=    Get Value    ${locator}
    Should Be Equal As Strings    ${actual}    ${value}

Select Edit Ajax Value
    [Arguments]    ${locator}    ${value}
    Press Keys    ${locator}    CTRL+A
    Input Text    ${locator}    ${value}
    ${option}=    Replace String    ${EDIT_AJAX_OPTION}    __VALUE__    ${value}
    Wait Until Element Is Visible    ${option}    timeout=20s
    Click Element    ${option}
    ${actual}=    Get Value    ${locator}
    Should Be Equal As Strings    ${actual}    ${value}

Set Edit Album Metadata
    [Arguments]    ${job}
    Replace Edit Text    ${EDIT_TITLE}    ${job}[song_name]
    Select From List By Value    ${EDIT_LANGUAGE}    en
    Select Edit Ajax Value    ${EDIT_GENRE}    ${job}[dmb_genre]
    Select From List By Label    ${EDIT_LABEL}    ${job}[label]
    Replace Edit Text    ${EDIT_RELEASE_DATE}    ${job}[release_date]
    Replace Edit Text    ${EDIT_EXPIRATION_DATE}    ${job}[expiration_date]
    Select From List By Value    ${EDIT_PRICE_CODE}    ${job}[price_code]
    Select From List By Value    ${EDIT_ITUNES_PRICE_CODE}    ${job}[itunes_price_code]
    Replace Edit Text    ${EDIT_C_LINE_YEAR}    ${job}[c_line_year]
    Select Edit Ajax Value    ${EDIT_C_LINE_TEXT}    ${job}[label]
    Replace Edit Text    ${EDIT_P_LINE_YEAR}    ${job}[p_line_year]
    Select Edit Ajax Value    ${EDIT_P_LINE_TEXT}    ${job}[label]

Upload Edit Cover
    [Arguments]    ${cover_path}
    File Should Exist    ${cover_path}
    Choose File    ${EDIT_COVER_FILE}    ${cover_path}
    Wait Until Element Is Enabled    ${EDIT_COVER_UPLOAD}    timeout=20s
    Click Element    ${EDIT_COVER_UPLOAD}
    Wait Until Keyword Succeeds    60s    1s    Edit Cover Upload Should Finish

Edit Cover Upload Should Finish
    ${value}=    Get Value    ${EDIT_COVER_FILE}
    Should Be Empty    ${value}

Clear Edit Contributors
    ${count}=    Get Element Count    ${EDIT_CONTRIBUTOR_ROW}
    WHILE    ${count} > 0
        Click Element    ${EDIT_REMOVE_CONTRIBUTOR}
        Wait Until Keyword Succeeds    10s    500ms    Contributor Count Should Drop    ${count}
        ${count}=    Get Element Count    ${EDIT_CONTRIBUTOR_ROW}
    END

Contributor Count Should Drop
    [Arguments]    ${old_count}
    ${new_count}=    Get Element Count    ${EDIT_CONTRIBUTOR_ROW}
    Should Be True    ${new_count} < ${old_count}

Add Edit Contributor
    [Arguments]    ${name}    ${has_account}
    Input Text    ${EDIT_CONTRIBUTOR_NAME}    ${name}
    IF    ${has_account}
        ${option}=    Replace String    ${EDIT_AJAX_OPTION}    __VALUE__    ${name}
        Wait Until Element Is Visible    ${option}    timeout=20s
        Click Element    ${option}
    ELSE
        Press Keys    ${EDIT_CONTRIBUTOR_NAME}    TAB
        Unselect All From List    ${EDIT_CONTRIBUTOR_ROLES}
        Select From List By Label    ${EDIT_CONTRIBUTOR_ROLES}    Performer
    END
    Click Element    ${EDIT_ADD_CONTRIBUTOR}
    Wait Until Keyword Succeeds    20s    1s    Page Should Contain    ${name}

Replace Edit Contributors
    [Arguments]    ${contributors}
    Clear Edit Contributors
    FOR    ${contributor}    IN    @{contributors}
        Add Edit Contributor    ${contributor}[name]    ${contributor}[has_account]
    END

Verify Edit Form Data
    [Arguments]    ${job}
    ${title}=    Get Value    ${EDIT_TITLE}
    ${genre}=    Get Value    ${EDIT_GENRE}
    ${date}=    Get Value    ${EDIT_RELEASE_DATE}
    Should Be Equal As Strings    ${title}    ${job}[song_name]
    Should Be Equal As Strings    ${genre}    ${job}[dmb_genre]
    Should Be Equal As Strings    ${date}    ${job}[release_date]
    FOR    ${contributor}    IN    @{job}[contributors]
        Page Should Contain    ${contributor}[name]
    END

Save And Publish Edit
    [Arguments]    ${job}
    Should Be Equal    %{DMB_EDIT_SUBMIT_ENABLED}    true
    Click Element    ${EDIT_SAVE_ACTION}
    Unselect Frame
    Go To    ${LOGIN_URL}page/album/${job}[source_dmb_release_id]
    Wait Until Element Is Visible    ${EDIT_IFRAME}    timeout=60s
    Select Frame    ${EDIT_IFRAME}
    Wait Until Element Is Visible    ${EDIT_FORM}    timeout=60s
    Verify Edit Form Data    ${job}
    Page Should Contain Element    ${EDIT_PUBLISH_ACTION}
    Click Element    ${EDIT_PUBLISH_ACTION}
    Wait Until Keyword Succeeds    60s    2s    Edit Publication Should Be Confirmed

Edit Publication Should Be Confirmed
    ${success}=    Run Keyword And Return Status    Page Should Contain Element    ${EDIT_SUCCESS}
    ${publish_present}=    Run Keyword And Return Status    Page Should Contain Element    ${EDIT_PUBLISH_ACTION}
    ${confirmed}=    Evaluate    $success or not $publish_present
    Should Be True    ${confirmed}    DMB did not confirm edit publication

Capture Edit Failure Evidence And Close Browser
    Run Keyword And Ignore Error    Capture Page Screenshot    ${OUTPUT DIR}${/}final-state.png
    Run Keyword And Ignore Error    Close Browser Session
