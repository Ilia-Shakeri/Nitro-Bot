*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    String
Resource   ../locators/album_locators.robot
Resource   ../locators/login_locators.robot

*** Keywords ***
Navigate To Album Creation Form
    Wait Until Page Contains Element    ${MUSIC_MENU}    timeout=30s
    ${music_menu}=    Get WebElement    ${MUSIC_MENU}
    Execute Javascript    arguments[0].click();    ARGUMENTS    ${music_menu}
    Wait Until Element Is Visible    ${CREATE_ALBUM_LINK}    timeout=20s
    ${create_link}=    Get WebElement    ${CREATE_ALBUM_LINK}
    Execute Javascript    arguments[0].click();    ARGUMENTS    ${create_link}
    Wait Until Element Is Visible    ${MAIN_IFRAME}    timeout=30s

Select Album Format And Next
    Select Frame    ${MAIN_IFRAME}
    Wait Until Element Is Visible    ${MAXI_SINGLE_OPTION}    timeout=30s
    Click Element    ${MAXI_SINGLE_OPTION}
    Click Ready Next
    Wait Until Element Is Visible    ${EAN_INPUT}    timeout=30s

Click Ready Next
    Wait Until Element Is Enabled    ${NEXT_BUTTON}    timeout=30s
    ${next_button}=    Get WebElement    ${NEXT_BUTTON}
    Execute Javascript    arguments[0].click();    ARGUMENTS    ${next_button}

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
    ${cover_dir}    ${cover_name}=    Split Path    ${cover_path}
    Wait Until Keyword Succeeds    60s    1s    Cover Upload Should Be Ready    ${cover_name}

Cover Upload Should Be Ready
    [Arguments]    ${cover_name}
    ${ready}=    Execute Javascript    return document.body.innerText.includes(arguments[0]) || Array.from(document.querySelectorAll('input')).some((element) => element.value.endsWith(arguments[0]));    ARGUMENTS    ${cover_name}
    Should Be True    ${ready}    Cover filename is not visible after upload

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
    ${choice_clicked}=    Run Keyword And Return Status    Wait Until Keyword Succeeds    3s    500ms    Click Visible Exact Choice    ${dmb_genre}
    IF    not ${choice_clicked}
        Select Genre From Picker    ${dmb_genre}
    END
    Wait Until Keyword Succeeds    10s    1s    Genre Should Be Selected    ${dmb_genre}

Select Genre From Picker
    [Arguments]    ${dmb_genre}
    ${genre_picker}=    Get WebElement    ${GENRE_PICKER}
    Execute Javascript    arguments[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));    ARGUMENTS    ${genre_picker}
    Wait Until Element Is Visible    ${GENRE_CHOOSER_IFRAME}    timeout=20s
    Select Frame    ${GENRE_CHOOSER_IFRAME}
    ${has_parent}=    Evaluate    " [" in $dmb_genre and $dmb_genre.endswith("]")
    IF    ${has_parent}
        ${tree_value}=    Evaluate    $dmb_genre.rsplit(" [", 1)[0]
        ${tree_parent}=    Evaluate    $dmb_genre.rsplit(" [", 1)[1][:-1]
        Wait Until Keyword Succeeds    20s    500ms    Expand Genre Tree Parent    ${tree_parent}
        Wait Until Keyword Succeeds    10s    500ms    Select Genre Tree Value    ${tree_value}
    ELSE
        Wait Until Keyword Succeeds    10s    500ms    Select Genre Tree Value    ${dmb_genre}
    END
    Wait Until Element Is Enabled    ${GENRE_PICKER_OK}    timeout=10s
    Click Element    ${GENRE_PICKER_OK}
    Unselect Frame
    Wait Until Element Is Visible    ${MAIN_IFRAME}    timeout=30s
    Select Frame    ${MAIN_IFRAME}
    Wait Until Element Is Not Visible    ${GENRE_CHOOSER_IFRAME}    timeout=20s

Expand Genre Tree Parent
    [Arguments]    ${parent}
    ${expanded}=    Execute Javascript    const expected = arguments[0]; const labels = Array.from(document.querySelectorAll('mat-tree-node .node-value span')); const label = labels.find((node) => { const text = node.textContent.trim(); return text === expected || text.includes(expected); }); if (!label) { return false; } const row = label.closest('mat-tree-node'); if (row.getAttribute('aria-expanded') === 'true') { return true; } const button = row.querySelector('.collapsible button'); if (!button) { return false; } button.click(); return true;    ARGUMENTS    ${parent}
    Should Be True    ${expanded}    DMB genre parent not found: ${parent}

Select Genre Tree Value
    [Arguments]    ${value}
    ${selected}=    Execute Javascript    const expected = arguments[0]; const labels = Array.from(document.querySelectorAll('mat-tree-node .node-value span')); const label = labels.find((node) => { const text = node.textContent.trim(); return text === expected || text.includes(expected); }); if (!label) { return false; } const radio = label.closest('mat-tree-node').querySelector('input[type="radio"]:not([disabled])'); if (!radio) { return false; } radio.click(); return radio.checked;    ARGUMENTS    ${value}
    Should Be True    ${selected}    DMB genre value not found: ${value}

Click Visible Exact Choice
    [Arguments]    ${value}
    ${clicked}=    Execute Javascript    const value = arguments[0]; const nodes = Array.from(document.querySelectorAll('td, li, a, button, span, div')); const choice = nodes.find((node) => node.offsetParent !== null && node.textContent.trim() === value && !Array.from(node.children).some((child) => child.textContent.trim() === value)); if (!choice) { return false; } choice.click(); return true;    ARGUMENTS    ${value}
    Should Be True    ${clicked}    Exact DMB choice not visible: ${value}

Genre Should Be Selected
    [Arguments]    ${dmb_genre}
    ${value}=    Get Value    ${GENRE_INPUT}
    ${genre_id}=    Get Value    ${GENRE_ID_INPUT}
    Should Be Equal As Strings    ${value}    ${dmb_genre}
    Should Not Be Empty    ${genre_id}    DMB genre ID was not committed

Fill Ajax Value
    [Arguments]    ${locator}    ${value}
    Wait Until Element Is Visible    ${locator}    timeout=20s
    Input Text    ${locator}    ${value}
    Choose Ajax Result Or Confirm Text    ${locator}    ${value}
    Wait Until Keyword Succeeds    10s    1s    Field Value Should Equal    ${locator}    ${value}

Choose Ajax Result Or Confirm Text
    [Arguments]    ${locator}    ${value}
    ${exact_option}=    Replace String    ${AJAX_EXACT_OPTION}    __VALUE__    ${value}
    ${option_visible}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${exact_option}    timeout=3s
    IF    ${option_visible}
        Click Element    ${exact_option}
    ELSE
        Press Keys    ${locator}    ARROW_DOWN
        Press Keys    ${locator}    ENTER
    END

Field Value Should Equal
    [Arguments]    ${locator}    ${value}
    ${actual}=    Get Value    ${locator}
    Should Be Equal As Strings    ${actual}    ${value}

Set Label
    [Arguments]    ${label}
    Select From List By Label    ${LABEL_SELECT}    ${label}
    ${selected_label}=    Get Selected List Label    ${LABEL_SELECT}
    Should Be Equal As Strings    ${selected_label}    ${label}

Input Date And Confirm
    [Arguments]    ${locator}    ${date_value}
    Wait Until Element Is Visible    ${locator}    timeout=20s
    ${date_input}=    Get WebElement    ${locator}
    ${actual_date}=    Execute Javascript    const element = arguments[0]; const value = arguments[1]; const parts = value.split('.').map(Number); if (window.jQuery && window.jQuery.fn.datepicker) { window.jQuery(element).datepicker('setDate', new Date(parts[2], parts[1] - 1, parts[0])); window.jQuery(element).trigger('input').trigger('change'); } else { const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; setter.call(element, value); element.dispatchEvent(new Event('input', { bubbles: true })); element.dispatchEvent(new Event('change', { bubbles: true })); } element.blur(); return element.value;    ARGUMENTS    ${date_input}    ${date_value}
    Should Be Equal As Strings    ${actual_date}    ${date_value}
    Wait Until Element Is Not Visible    ${DATEPICKER}    timeout=5s

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
    ${roles_select}=    Get WebElement    ${CONTRIBUTOR_ROLES_SELECT}
    Execute Javascript    const select = arguments[0]; Array.from(select.options).forEach((option) => { option.selected = option.textContent.trim() === 'Performer'; }); select.dispatchEvent(new Event('change', { bubbles: true }));    ARGUMENTS    ${roles_select}
    @{selected_roles}=    Get Selected List Labels    ${CONTRIBUTOR_ROLES_SELECT}
    ${role_count}=    Get Length    ${selected_roles}
    Should Be Equal As Integers    ${role_count}    1
    Should Be Equal As Strings    ${selected_roles}[0]    Performer

Restore Album Frame After Contributor
    Unselect Frame
    Wait Until Element Is Visible    ${MAIN_IFRAME}    timeout=30s
    Select Frame    ${MAIN_IFRAME}

Capture Active Form Source
    ${source}=    Execute Javascript    return document.documentElement.outerHTML;
    Create File    ${OUTPUT DIR}${/}form-state.html    ${source}

Open Add Tracks
    Wait Until Page Contains Element    ${TRACK_FILE_INPUT}    timeout=30s

Upload Track
    [Arguments]    ${music_path}
    File Should Exist    ${music_path}    msg=Music file not found: ${music_path}
    ${music_dir}    ${music_name}=    Split Path    ${music_path}
    Choose File    ${TRACK_FILE_INPUT}    ${music_path}
    Wait Until Keyword Succeeds    60s    1s    Track Upload Should Be Ready    ${music_name}

Track Upload Should Be Ready
    [Arguments]    ${music_name}
    ${ready}=    Execute Javascript    return document.body.innerText.includes(arguments[0]) || Array.from(document.querySelectorAll('input')).some((element) => element.value.endsWith(arguments[0]));    ARGUMENTS    ${music_name}
    Should Be True    ${ready}    Track filename is not visible after upload

Fill Track Info And Generate ISRC
    [Arguments]    ${track_title}
    Wait Until Element Is Visible    ${GENERATE_ALL_ISRCS}    timeout=30s
    Click Element    ${GENERATE_ALL_ISRCS}
    Wait Until Keyword Succeeds    30s    1s    ISRC Should Be Generated
    ${actual_title}=    Execute Javascript    const element = Array.from(document.querySelectorAll("input[name='track:title[]']")).find((candidate) => candidate.offsetParent !== null); if (!element) { return ""; } element.value = arguments[0]; element.dispatchEvent(new Event("input", {bubbles: true})); element.dispatchEvent(new Event("change", {bubbles: true})); element.blur(); return element.value;    ARGUMENTS    ${track_title}
    Should Be Equal As Strings    ${actual_title}    ${track_title}
    ${isrc}=    Get Generated ISRC
    RETURN    ${isrc}

ISRC Should Be Generated
    ${isrc}=    Get Generated ISRC
    Should Match Regexp    ${isrc}    ^[A-Za-z0-9-]{8,20}$

Get Generated ISRC
    ${isrc}=    Execute Javascript    return Array.from(document.querySelectorAll("input[name='track:isrc[]']")).map((element) => element.value.trim()).find(Boolean) || "";
    RETURN    ${isrc}

Continue To Territory Page
    Click Ready Next
    Wait Until Element Is Visible    ${WORLDWIDE_OPTION}    timeout=180s

Select Worldwide And Next
    Wait Until Element Is Visible    ${WORLDWIDE_OPTION}    timeout=30s
    Click Element    ${WORLDWIDE_OPTION}
    Click Ready Next
    Wait Until Element Is Visible    ${ALL_PLATFORMS_BUTTON}    timeout=60s

Select All Platforms And Next
    Wait Until Element Is Not Visible    ${LOADING_OVERLAY}    timeout=60s
    Click Element    ${ALL_PLATFORMS_BUTTON}
    Wait Until Keyword Succeeds    10s    1s    Assigned Platforms Should Exist
    Wait Until Element Is Not Visible    ${LOADING_OVERLAY}    timeout=60s
    Click Ready Next
    Wait Until Element Is Not Visible    ${ALL_PLATFORMS_BUTTON}    timeout=60s
    Wait Until Element Is Visible    ${SAVE_BUTTON}    timeout=60s

Assigned Platforms Should Exist
    ${count}=    Get Element Count    ${ASSIGNED_PLATFORMS}
    Should Be True    ${count} > 0    No assigned DMB outlets found

Verify Review Data
    [Arguments]    ${title}    ${ean}    ${isrc}    ${release_date}    ${expiration_date}    ${genre}    ${label}    ${contributors}
    Field Value Should Equal    ${TITLE_INPUT}    ${title}
    Field Value Should Equal    ${EAN_INPUT}    ${ean}
    ${review_isrc}=    Get Generated ISRC
    Should Be Equal As Strings    ${review_isrc}    ${isrc}
    ${dmb_release_date}=    Format Dmb Date    ${release_date}
    ${dmb_expiration_date}=    Format Dmb Date    ${expiration_date}
    Field Value Should Equal    ${SALES_START_DATE}    ${dmb_release_date}
    Field Value Should Equal    ${SALES_END_DATE}    ${dmb_expiration_date}
    Genre Should Be Selected    ${genre}
    ${selected_label}=    Get Selected List Label    ${LABEL_SELECT}
    Should Be Equal As Strings    ${selected_label}    ${label}
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
    [Arguments]    ${release_id}    ${ean}    ${isrc}    ${title}
    Should Be Equal    %{DMB_SUBMIT_ENABLED}    true
    Wait Until Element Is Enabled    ${SAVE_BUTTON}    timeout=30s
    Scroll Element Into View    ${SAVE_BUTTON}
    ${before_url}=    Get Location
    Write Submit Checkpoint    %{DMB_SUBMIT_CHECKPOINT}    ${release_id}    ${ean}    ${isrc}    ${title}
    Click Element    ${SAVE_BUTTON}
    Wait Until Keyword Succeeds    60s    2s    Submission Should Be Confirmed    ${before_url}

Capture Failure Evidence And Close Browser
    Run Keyword And Ignore Error    Capture Page Screenshot    ${OUTPUT DIR}${/}final-state.png
    Run Keyword And Ignore Error    Capture Final Page Source
    Run Keyword And Ignore Error    Close Browser Session

Capture Final Page Source
    ${source}=    Execute Javascript    return document.documentElement.outerHTML;
    Create File    ${OUTPUT DIR}${/}final-state.html    ${source}
