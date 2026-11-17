*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    String
Library    ../../libraries/dmb_profiles.py
Resource   ../locators/album_locators.robot
Resource   ../locators/login_locators.robot
Resource   form_ready.robot
Resource   edit_album_page.robot

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
    Wait For DMB Form Ready
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
    [Arguments]    ${dmb_genre}    ${picker_locator}=${GENRE_PICKER}    ${frame_locator}=${MAIN_IFRAME}
    ${genre_picker}=    Get WebElement    ${picker_locator}
    Execute Javascript    arguments[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));    ARGUMENTS    ${genre_picker}
    Wait Until Element Is Visible    ${GENRE_CHOOSER_IFRAME}    timeout=20s
    Select Frame    ${GENRE_CHOOSER_IFRAME}
    ${has_parent}=    Evaluate    " [" in $dmb_genre and $dmb_genre.endswith("]")
    IF    ${has_parent}
        ${tree_value}=    Evaluate    $dmb_genre.rsplit(" [", 1)[0]
        ${tree_parent}=    Evaluate    $dmb_genre.rsplit(" [", 1)[1][:-1]
        ${tree_value_visible}=    Run Keyword And Return Status    Wait Until Keyword Succeeds    2s    250ms    Genre Tree Value Is Selectable    ${tree_value}
        IF    not ${tree_value_visible}
            Expand Genre Tree Parent    ${tree_parent}
        END
        Wait Until Keyword Succeeds    10s    500ms    Select Genre Tree Value    ${tree_value}
    ELSE
        Wait Until Keyword Succeeds    10s    500ms    Select Genre Tree Value    ${dmb_genre}
    END
    Wait Until Element Is Enabled    ${GENRE_PICKER_OK}    timeout=10s
    Click Element    ${GENRE_PICKER_OK}
    Unselect Frame
    Wait Until Element Is Visible    ${frame_locator}    timeout=30s
    Select Frame    ${frame_locator}
    Wait For DMB Form Ready
    Wait Until Element Is Not Visible    ${GENRE_CHOOSER_IFRAME}    timeout=20s

Expand Genre Tree Parent
    [Arguments]    ${parent}
    ${expanded}=    Execute Javascript    const expected = arguments[0].trim(); const aliases = { 'Kids- and Youthprogramm (Children)': 'Kids and youth program (Children)' }; const alias = aliases[expected] || expected; const labels = Array.from(document.querySelectorAll('mat-tree-node .node-value span')); const label = labels.find((node) => { const text = node.textContent.trim(); return text === expected || text === alias || text.includes(alias); }); let row = label?.closest('mat-tree-node'); if (!row && alias === 'Kids and youth program (Children)') row = document.getElementById('300000000'); if (!row) return false; if (row.getAttribute('aria-expanded') !== 'true') { const button = row.querySelector('.collapsible button'); if (!button) return false; button.click(); } return true;    ARGUMENTS    ${parent}
    Should Be True    ${expanded}    DMB genre parent not found: ${parent}
    Wait Until Keyword Succeeds    10s    250ms    Genre Tree Parent Should Be Expanded    ${parent}

Genre Tree Parent Should Be Expanded
    [Arguments]    ${parent}
    ${expanded}=    Execute Javascript    const expected = arguments[0].trim(); const alias = expected === 'Kids- and Youthprogramm (Children)' ? 'Kids and youth program (Children)' : expected; const labels = Array.from(document.querySelectorAll('mat-tree-node .node-value span')); const label = labels.find((node) => { const text = node.textContent.trim(); return text === expected || text === alias; }); const row = label?.closest('mat-tree-node') || (alias === 'Kids and youth program (Children)' ? document.getElementById('300000000') : null); return row?.getAttribute('aria-expanded') === 'true';    ARGUMENTS    ${parent}
    Should Be True    ${expanded}    DMB genre parent did not expand: ${parent}

Genre Tree Value Is Selectable
    [Arguments]    ${value}
    ${selectable}=    Execute Javascript    const expected = arguments[0].trim(); return Array.from(document.querySelectorAll('mat-tree-node')).some((row) => { const label = row.querySelector('.node-value'); const radio = row.querySelector('input[type="radio"]:not([disabled])'); const rect = row.getBoundingClientRect(); return label?.textContent.trim() === expected && !!radio && rect.width > 0 && rect.height > 0; });    ARGUMENTS    ${value}
    Should Be True    ${selectable}    DMB genre value is not selectable: ${value}

Select Genre Tree Value
    [Arguments]    ${value}
    ${selected}=    Execute Javascript    const expected = arguments[0]; const labels = Array.from(document.querySelectorAll('mat-tree-node .node-value span')).filter((node) => { const text = node.textContent.trim(); return text === expected || text.includes(expected); }); const selectable = labels.map((label) => label.closest('mat-tree-node')).find((row) => row.querySelector('input[type="radio"]:not([disabled])')); if (selectable) { const radio = selectable.querySelector('input[type="radio"]:not([disabled])'); radio.click(); return radio.checked; } const expandable = labels.map((label) => label.closest('mat-tree-node')).find((row) => row.getAttribute('aria-expanded') !== 'true' && row.querySelector('.collapsible button')); if (expandable) { expandable.querySelector('.collapsible button').click(); } return false;    ARGUMENTS    ${value}
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
    Date Value Should Match    ${actual_date}    ${date_value}
    Wait Until Element Is Not Visible    ${DATEPICKER}    timeout=5s

Date Value Should Match
    [Arguments]    ${actual_date}    ${dotted_date}
    ${iso_date}=    Evaluate    "-".join(reversed($dotted_date.split(".")))
    ${matches}=    Evaluate    $actual_date in ($dotted_date, $iso_date)
    Should Be True    ${matches}    DMB date value mismatch: ${actual_date}

Date Field Should Equal
    [Arguments]    ${locator}    ${iso_date}
    ${actual_date}=    Get Value    ${locator}
    ${dotted_date}=    Format Dmb Date    ${iso_date}
    Date Value Should Match    ${actual_date}    ${dotted_date}

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
        Select Contributor Suggestion    ${name}
    ELSE
        Press Keys    ${CONTRIBUTOR_NAME_INPUT}    TAB
    END
    Keep Only Performer Role
    Wait Until Element Is Enabled    ${ADD_CONTRIBUTOR_BUTTON}    timeout=20s
    Click Element    ${ADD_CONTRIBUTOR_BUTTON}
    Wait Until Keyword Succeeds    20s    1s    Active Form Should Contain    ${name}
    Set DMB Checkbox    ${CONTRIBUTOR_PRIMARY}

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
    Wait For DMB Form Ready

Apply Contributors To Tracks
    Wait Until Element Is Visible    ${APPLY_CONTRIBUTORS_TO_TRACKS}    timeout=20s
    ${label}=    Get WebElement    ${APPLY_CONTRIBUTORS_TO_TRACKS}
    ${checkbox}=    Execute Javascript    const label = arguments[0]; return label.control || label.querySelector('input[type="checkbox"]') || document.getElementById(label.htmlFor);    ARGUMENTS    ${label}
    Should Not Be Equal    ${checkbox}    ${None}    Track contributor checkbox missing
    ${checked}=    Execute Javascript    return arguments[0].checked;    ARGUMENTS    ${checkbox}
    IF    not ${checked}
        Click Element    ${APPLY_CONTRIBUTORS_TO_TRACKS}
    END
    ${checked}=    Execute Javascript    return arguments[0].checked;    ARGUMENTS    ${checkbox}
    Should Be True    ${checked}    Track contributors were not enabled

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
    Field Value Should Equal    ${REVIEW_EAN_INPUT}    ${ean}
    Review Wizard Value Should Equal    eanUpc    ${ean}
    Review Wizard List Should Contain    track:isrc    ${isrc}
    Review Wizard List Should Contain    track:title    ${title}
    Date Field Should Equal    ${SALES_START_DATE}    ${release_date}
    Date Field Should Equal    ${SALES_END_DATE}    ${expiration_date}
    Field Value Should Equal    ${GENRE_INPUT}    ${genre}
    Review Wizard Value Should Equal    genre    ${genre}
    Review Wizard Value Should Not Be Empty    genre_id
    Review Wizard Value Should Equal    contributors2tracks    1
    ${selected_label}=    Get Selected List Label    ${LABEL_SELECT}
    Should Be Equal As Strings    ${selected_label}    ${label}
    FOR    ${contributor}    IN    @{contributors}
        Review Wizard List Should Contain    cce_aName    ${contributor}[name]
    END

Get Review Wizard Value
    [Arguments]    ${field}
    ${wizard_data}=    Get WebElement    ${REVIEW_WIZARD_DATA}
    ${value}=    Execute Javascript    const data = JSON.parse(arguments[0].value); return data[arguments[1]] ?? '';    ARGUMENTS    ${wizard_data}    ${field}
    RETURN    ${value}

Review Wizard Value Should Equal
    [Arguments]    ${field}    ${expected}
    ${actual}=    Get Review Wizard Value    ${field}
    Should Be Equal As Strings    ${actual}    ${expected}

Review Wizard Value Should Not Be Empty
    [Arguments]    ${field}
    ${actual}=    Get Review Wizard Value    ${field}
    ${present}=    Evaluate    $actual is not None and str($actual).strip() != ""
    Should Be True    ${present}    DMB review field is empty: ${field}

Review Wizard List Should Contain
    [Arguments]    ${field}    ${expected}
    ${actual}=    Get Review Wizard Value    ${field}
    Should Contain    ${actual}    ${expected}

Submission Should Be Confirmed
    [Arguments]    ${before_url}
    ${success}=    Run Keyword And Return Status    Page Should Contain Element    ${SUBMISSION_SUCCESS}
    ${current_url}=    Get Location
    ${confirmed}=    Evaluate    $success or $current_url != $before_url
    Should Be True    ${confirmed}    DMB did not confirm album submission

Submit Album And Verify Success
    [Arguments]    ${release_id}    ${ean}    ${isrc}    ${title}    ${job}
    Should Be Equal    %{DMB_SUBMIT_ENABLED}    true
    Should Be Equal    %{DMB_PUBLISH_ENABLED=false}    true
    Wait Until Element Is Enabled    ${SAVE_BUTTON}    timeout=30s
    ${save_button}=    Get WebElement    ${SAVE_BUTTON}
    Execute Javascript    arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});    ARGUMENTS    ${save_button}
    ${before_url}=    Get Location
    Write Submit Checkpoint    %{DMB_SUBMIT_CHECKPOINT}    ${release_id}    ${ean}    ${isrc}    ${title}
    Execute Javascript    arguments[0].click();    ARGUMENTS    ${save_button}
    Wait Until Keyword Succeeds    60s    2s    Submission Should Be Confirmed    ${before_url}
    Unselect Frame
    ${saved_url}=    Get Location
    ${dmb_release_id}=    Extract Dmb Release Id    ${saved_url}
    Write Saved Checkpoint
    ...    %{DMB_SAVED_CHECKPOINT}
    ...    ${release_id}
    ...    ${dmb_release_id}
    ...    ${ean}
    ...    ${isrc}
    ...    ${title}
    ...    ${saved_url}
    Prepare Saved Single For Publication    ${job}    ${dmb_release_id}    ${ean}    ${isrc}
    Publish Created Album And Verify Identity    ${dmb_release_id}    ${ean}

Prepare Saved Single For Publication
    [Arguments]    ${job}    ${dmb_release_id}    ${ean}    ${isrc}
    Configure Saved Album Profiles    ${job}    ${dmb_release_id}    ${ean}    ${TRUE}
    ${track_job}=    Evaluate    dict($job, source_dmb_release_id=$dmb_release_id, source_dmb_ean_upc=$ean, source_dmb_isrcs=[$isrc])
    Unselect Frame
    Open Single Track Metadata Editor    ${dmb_release_id}
    Fill Single Track Metadata    ${track_job}    ${FALSE}
    Save Single Track Metadata
    Open Source Album In Edit Mode    ${dmb_release_id}
    Verify Source Album Identity    ${dmb_release_id}    ${ean}
    Set Edit Album Metadata    ${track_job}
    Verify Edit Form Data    ${track_job}
    ${save}=    Get WebElement    ${EDIT_SAVE_ACTION}
    Click Element    ${EDIT_SAVE_ACTION}
    Wait For Saved Form    ${save}
    Confirm Exact Saved Track    ${dmb_release_id}    ${ean}    ${isrc}    ${job}[song_name]

Confirm Exact Saved Track
    [Arguments]    ${dmb_release_id}    ${ean}    ${isrc}    ${title}
    Should Be Equal    %{DMB_PUBLISH_ENABLED=false}    true
    Preserve Exact Saved Track Title    ${dmb_release_id}    ${ean}    ${isrc}    ${title}
    Unselect Frame
    Go To    ${LOGIN_URL}page/album-confirm-tracks/${dmb_release_id}?successUrl=page%2Falbum%2F${dmb_release_id}
    Wait Until Element Is Visible    xpath=//iframe    timeout=60s
    Select Frame    xpath=//iframe
    Wait For DMB Form Ready
    ${count}=    Get Element Count    xpath=//input[@name='all_tracks[]']
    Should Be Equal As Integers    ${count}    1    Only a single exact track can be confirmed
    Active Form Should Contain    ${isrc}
    Active Form Should Contain    ${title}
    ${checkbox}=    Get WebElement    xpath=//input[@name='selectedProductId[]']
    ${track_id}=    Get Element Attribute    ${checkbox}    value
    ${all_track_id}=    Get Value    xpath=//input[@name='all_tracks[]']
    Should Be Equal As Strings    ${track_id}    ${all_track_id}
    ${selected}=    Execute Javascript    if (!arguments[0].checked) { arguments[0].click(); } return arguments[0].checked;    ARGUMENTS    ${checkbox}
    Should Be True    ${selected}
    ${confirm}=    Get WebElement    xpath=//button[contains(@onclick,'"action":"confirm"')]
    Click Element    ${confirm}
    Wait For Saved Form    ${confirm}
    Wait For DMB Form Ready
    ${confirmation_issues}=    Execute Javascript    return Array.from(document.querySelectorAll('.dmb-message--error .dmb-message__text')).filter(e => e.offsetParent !== null).map(e => e.textContent.trim()).join(' | ');
    Should Be Empty    ${confirmation_issues}    DMB track confirmation rejected: ${confirmation_issues}
    Unselect Frame
    Go To    ${LOGIN_URL}page/album/${dmb_release_id}
    Wait Until Element Is Visible    ${CREATED_ALBUM_IFRAME}    timeout=60s
    Select Frame    ${CREATED_ALBUM_IFRAME}
    Wait For DMB Form Ready
    ${actual_ean}=    Get Value    ${CREATED_ALBUM_EAN}
    Should Be Equal As Strings    ${actual_ean}    ${ean}
    Wait Until Keyword Succeeds    30s    1s    Exact Saved Track Should Remain Identical    ${track_id}    ${isrc}    ${title}

Preserve Exact Saved Track Title
    [Arguments]    ${dmb_release_id}    ${ean}    ${isrc}    ${title}
    Unselect Frame
    Open Source Album In Edit Mode    ${dmb_release_id}
    Verify Source Album Identity    ${dmb_release_id}    ${ean}
    ${track_url}=    Execute Javascript    const infos = Array.from(document.querySelectorAll('.dmb-module-tracks__track-info')).filter(e => e.textContent.includes(arguments[0])); if (infos.length !== 1) return ''; let row = infos[0]; while (row && !row.querySelector('a[href*="page/track/"]')) row = row.parentElement; const links = Array.from(row?.querySelectorAll('a[href*="page/track/"]') || []).map(a => a.href); const unique = [...new Set(links)]; return unique.length === 1 ? unique[0] : '';    ARGUMENTS    ${isrc}
    Should Match Regexp    ${track_url}    ^https://dmb[.]kontornewmedia[.]com/page/track/[0-9]+([?].*)?$
    Unselect Frame
    Go To    ${track_url}
    Wait Until Element Is Visible    xpath=//iframe    timeout=60s
    Select Frame    xpath=//iframe
    Wait For DMB Form Ready
    ${saved_isrc}=    Get Value    xpath=//input[@name='isrc']
    Should Be Equal As Strings    ${saved_isrc}    ${isrc}
    ${actual_title}=    Get Value    xpath=//input[@name='title']
    IF    $actual_title == $title
        RETURN
    END
    Set DMB Checkbox    xpath=//input[@name='withTitleCheck']    ${FALSE}
    Replace Edit Text    xpath=//input[@name='title']    ${title}
    ${save}=    Get WebElement    xpath=//a[contains(@onclick,'"action":"save"')]
    Click Element    ${save}
    Wait For Saved Form    ${save}
    Unselect Frame
    Go To    ${track_url}
    Wait Until Element Is Visible    xpath=//iframe    timeout=60s
    Select Frame    xpath=//iframe
    Wait For DMB Form Ready
    ${saved_isrc}=    Get Value    xpath=//input[@name='isrc']
    ${saved_title}=    Get Value    xpath=//input[@name='title']
    Should Be Equal As Strings    ${saved_isrc}    ${isrc}
    Should Be Equal As Strings    ${saved_title}    ${title}

Exact Saved Track Should Remain Identical
    [Arguments]    ${track_id}    ${isrc}    ${title}
    ${matched}=    Execute Javascript    const rows = Array.from(document.querySelectorAll('.dmb-module-tracks__track-row')).filter(e => e.dataset.trackId === arguments[0]); return rows.length === 1 && rows[0].textContent.includes(arguments[1]) && rows[0].textContent.includes(arguments[2]);    ARGUMENTS    ${track_id}    ${isrc}    ${title}
    Should Be True    ${matched}    Exact saved track identity changed after confirmation

Publish Created Album And Verify Identity
    [Arguments]    ${dmb_release_id}    ${ean}
    Should Be Equal    %{DMB_PUBLISH_ENABLED=false}    true
    Go To    ${LOGIN_URL}page/album/${dmb_release_id}
    Wait Until Element Is Visible    ${CREATED_ALBUM_IFRAME}    timeout=60s
    Select Frame    ${CREATED_ALBUM_IFRAME}
    Wait For DMB Form Ready
    Wait Until Element Is Visible    ${CREATED_ALBUM_FORM}    timeout=60s
    ${saved_ean}=    Get Value    ${CREATED_ALBUM_EAN}
    Should Be Equal As Strings    ${saved_ean}    ${ean}
    ${issues}=    Execute Javascript    return Array.from(document.querySelectorAll('.dmb-message__text')).filter(e => e.offsetParent !== null).map(e => e.textContent.trim()).filter(text => /assigned Spotify Artist ID|primary artist is missing|genre at the album level|tracks are still unconfirmed/i.test(text)).join(' | ');
    Should Be Empty    ${issues}    DMB validation requires review: ${issues}
    Wait Until Element Is Visible    ${CREATE_PUBLISH_ACTION}    timeout=30s
    ${publish_button}=    Get WebElement    ${CREATE_PUBLISH_ACTION}
    Execute Javascript    arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});    ARGUMENTS    ${publish_button}
    Execute Javascript    arguments[0].click();    ARGUMENTS    ${publish_button}
    Wait Until Keyword Succeeds    60s    1s    Publication Response Should Be Ready
    Wait Until Keyword Succeeds    60s    2s    Created Album Publication Should Be Confirmed    ${ean}

Publication Response Should Be Ready
    ${issues}=    Execute Javascript    return Array.from(document.querySelectorAll('.dmb-message--error .dmb-message__text')).filter(e => e.offsetParent !== null).map(e => e.textContent.trim()).join(' | ');
    IF    $issues
        Fatal Error    DMB publication rejected: ${issues}
    END
    ${loading}=    Execute Javascript    return !!window.jQuery && jQuery.active > 0;
    Should Not Be True    ${loading}    DMB publication request is still pending

Created Album Publication Should Be Confirmed
    [Arguments]    ${ean}
    Publication Response Should Be Ready
    ${success}=    Run Keyword And Return Status    Page Should Contain Element    ${PUBLICATION_SUCCESS}
    ${form_present}=    Run Keyword And Return Status    Page Should Contain Element    ${CREATED_ALBUM_FORM}
    ${publish_present}=    Run Keyword And Return Status    Page Should Contain Element    ${CREATE_PUBLISH_ACTION}
    ${saved_ean}=    Run Keyword If    ${form_present}    Get Value    ${CREATED_ALBUM_EAN}    ELSE    Set Variable    ${EMPTY}
    ${confirmed}=    Evaluate    $success or ($form_present and not $publish_present and $saved_ean == $ean)
    Should Be True    ${confirmed}    DMB did not confirm album publication

Capture Failure Evidence And Close Browser
    Run Keyword And Ignore Error    Capture Page Screenshot    ${OUTPUT DIR}${/}final-state.png
    Run Keyword And Ignore Error    Capture Final Page Source
    Run Keyword And Ignore Error    Close Browser Session

Capture Final Page Source
    ${source}=    Execute Javascript    return document.documentElement.outerHTML;
    Create File    ${OUTPUT DIR}${/}final-state.html    ${source}
