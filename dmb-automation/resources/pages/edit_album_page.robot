*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    String
Library    ../../libraries/dmb_profiles.py
Resource   ../locators/edit_album_locators.robot
Resource   ../variables/global_vars.robot
Resource   form_ready.robot

*** Keywords ***
Open Single Track Metadata Editor
    [Arguments]    ${dmb_release_id}
    Go To    ${LOGIN_URL}page/track-edit-metadata?targetAlbumId=${dmb_release_id}
    Wait Until Element Is Visible    ${TRACK_EDIT_IFRAME}    timeout=30s
    Select Frame    ${TRACK_EDIT_IFRAME}
    Wait For DMB Form Ready
    Wait Until Element Is Visible    ${TRACK_EDIT_ACTION}    timeout=30s
    Click Element    ${TRACK_EDIT_ACTION}
    Click Element    ${TRACK_EDIT_NEXT}
    Wait Until Element Is Visible    ${TRACK_EDIT_FORM}    timeout=30s

Fill Single Track Metadata
    [Arguments]    ${job}    ${replace_contributors}=${TRUE}
    Replace Edit Text    ${TRACK_EDIT_TITLE}    ${job}[song_name]
    Set DMB Checkbox    ${TRACK_EDIT_FIELD_TITLE}
    Select Edit Genre    ${TRACK_EDIT_GENRE}    ${job}[dmb_genre]    ${TRACK_EDIT_GENRE_PICKER}    ${TRACK_EDIT_IFRAME}
    Set DMB Checkbox    ${TRACK_EDIT_FIELD_GENRE}
    IF    ${job}[explicit_content]
        Select From List By Value    ${TRACK_EDIT_EXPLICIT}    explicit
    ELSE
        Select From List By Value    ${TRACK_EDIT_EXPLICIT}    normal
    END
    Set DMB Checkbox    ${TRACK_EDIT_FIELD_EXPLICIT}
    Replace Edit Text    ${TRACK_EDIT_P_YEAR}    ${job}[p_line_year]
    Select Edit Ajax Value    ${TRACK_EDIT_P_TEXT}    ${job}[label]
    Set DMB Checkbox    ${TRACK_EDIT_FIELD_P_LINE}
    IF    ${replace_contributors}
        Set DMB Checkbox    ${TRACK_EDIT_FIELD_CONTRIBUTORS}
        Select From List By Value    ${TRACK_EDIT_CONTRIBUTOR_MODE}    apply
        Replace Track Contributors    ${job}[contributors]
    END
    Click Element    ${TRACK_EDIT_NEXT}
    Wait Until Element Is Visible    ${TRACK_EDIT_SAVE}    timeout=30s
    ${track_count}=    Get Element Count    ${TRACK_EDIT_SELECTED_TRACK}
    Should Be Equal As Integers    ${track_count}    1
    Active Form Should Contain    ${job}[source_dmb_isrcs][0]

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
        Select Contributor Suggestion    ${name}
    ELSE
        Commit Edit Input    ${TRACK_EDIT_CONTRIBUTOR_NAME}
    END
    Set Performer Role    ${TRACK_EDIT_CONTRIBUTOR_ROLES}
    Click Element    ${TRACK_EDIT_ADD_CONTRIBUTOR}
    Wait Until Keyword Succeeds    20s    1s    Active Form Should Contain    ${name}
    Set DMB Checkbox    ${TRACK_EDIT_CONTRIBUTOR_PRIMARY}

Save Single Track Metadata
    Click Element    ${TRACK_EDIT_SAVE}
    Wait Until Keyword Succeeds    60s    2s    Page Should Not Contain Element    ${TRACK_EDIT_SAVE}
    Unselect Frame

Open Source Album In Edit Mode
    [Arguments]    ${dmb_release_id}
    Go To    ${LOGIN_URL}page/album/${dmb_release_id}
    Wait Until Element Is Visible    ${EDIT_IFRAME}    timeout=30s
    Select Frame    ${EDIT_IFRAME}
    Wait For DMB Form Ready
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
    Input Text    ${locator}    ${value}
    Commit Edit Input    ${locator}
    ${actual}=    Get Value    ${locator}
    Should Be Equal As Strings    ${actual}    ${value}

Select Edit Ajax Value
    [Arguments]    ${locator}    ${value}
    Input Text    ${locator}    ${value}
    ${option}=    Replace String    ${EDIT_AJAX_OPTION}    __VALUE__    ${value}
    ${option_visible}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${option}    timeout=3s
    IF    ${option_visible}
        Click Element    ${option}
    ELSE
        Commit Edit Input    ${locator}
    END
    ${actual}=    Get Value    ${locator}
    Should Be Equal As Strings    ${actual}    ${value}

Commit Edit Input
    [Arguments]    ${locator}
    ${element}=    Get WebElement    ${locator}
    Execute Javascript    arguments[0].dispatchEvent(new Event('change', {bubbles: true})); arguments[0].blur();    ARGUMENTS    ${element}

Select Edit Genre
    [Arguments]    ${locator}    ${value}    ${picker}    ${frame}
    ${current}=    Get Value    ${locator}
    ${current_id}=    Execute Javascript    return document.querySelector('input[name="genre_id"]')?.value || '';
    IF    $current == $value and $current_id
        RETURN
    END
    Select Genre From Picker    ${value}    ${picker}    ${frame}
    ${actual}=    Get Value    ${locator}
    Should Be Equal As Strings    ${actual}    ${value}
    ${genre_id}=    Execute Javascript    return document.querySelector('input[name="genre_id"]')?.value || '';
    Should Not Be Empty    ${genre_id}    DMB track genre ID was not committed

Set Edit Album Metadata
    [Arguments]    ${job}
    ${normalization}=    Get Element Count    xpath=${EDIT_FORM_XPATH}//input[@name='withTitleCheck']
    IF    ${normalization} > 0
        Set DMB Checkbox    xpath=${EDIT_FORM_XPATH}//input[@name='withTitleCheck']    ${FALSE}
    END
    Replace Edit Text    ${EDIT_TITLE}    ${job}[song_name]
    Select From List By Value    ${EDIT_LANGUAGE}    en
    Select Edit Genre    ${EDIT_GENRE}    ${job}[dmb_genre]    ${EDIT_GENRE_PICKER}    ${EDIT_IFRAME}
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
        Select Contributor Suggestion    ${name}
    ELSE
        Commit Edit Input    ${EDIT_CONTRIBUTOR_NAME}
    END
    Set Performer Role    ${EDIT_CONTRIBUTOR_ROLES}
    Click Element    ${EDIT_ADD_CONTRIBUTOR}
    Wait Until Keyword Succeeds    20s    1s    Active Form Should Contain    ${name}
    Set DMB Checkbox    ${EDIT_CONTRIBUTOR_PRIMARY}

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
        Active Form Should Contain    ${contributor}[name]
    END

Save And Publish Edit
    [Arguments]    ${job}
    Should Be Equal    %{DMB_EDIT_SUBMIT_ENABLED}    true
    ${save}=    Get WebElement    ${EDIT_SAVE_ACTION}
    Click Element    ${EDIT_SAVE_ACTION}
    Wait For Saved Form    ${save}
    Unselect Frame
    Open Source Album In Edit Mode    ${job}[source_dmb_release_id]
    Verify Source Album Identity    ${job}[source_dmb_release_id]    ${job}[source_dmb_ean_upc]
    Verify Edit Form Data    ${job}
    Configure Saved Album Profiles    ${job}    ${job}[source_dmb_release_id]    ${job}[source_dmb_ean_upc]    ${TRUE}
    Confirm Exact Saved Track    ${job}[source_dmb_release_id]    ${job}[source_dmb_ean_upc]    ${job}[source_dmb_isrcs][0]    ${job}[song_name]
    Publish Created Album And Verify Identity    ${job}[source_dmb_release_id]    ${job}[source_dmb_ean_upc]

Edit Publication Should Be Confirmed
    ${success}=    Run Keyword And Return Status    Page Should Contain Element    ${EDIT_SUCCESS}
    ${publish_present}=    Run Keyword And Return Status    Page Should Contain Element    ${EDIT_PUBLISH_ACTION}
    ${confirmed}=    Evaluate    $success or not $publish_present
    Should Be True    ${confirmed}    DMB did not confirm edit publication

Capture Edit Failure Evidence And Close Browser
    Run Keyword And Ignore Error    Capture Page Screenshot    ${OUTPUT DIR}${/}final-state.png
    Run Keyword And Ignore Error    Close Browser Session
