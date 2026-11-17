*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    ../libraries/dmb_job.py
Resource   ../resources/pages/login_page.robot
Resource   ../resources/pages/edit_album_page.robot
Resource   ../resources/pages/album_page.robot
Resource   ../resources/variables/global_vars.robot
Resource   ../resources/locators/login_locators.robot

*** Test Cases ***
Repair Saved Album Metadata
    [Setup]    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    ${job}=    Load Dmb Job    %{DMB_JOB_FILE}
    Open Source Album In Edit Mode    ${job}[source_dmb_release_id]
    Verify Source Album Identity    ${job}[source_dmb_release_id]    ${job}[source_dmb_ean_upc]
    ${job}=    Reuse Saved Contributors    ${job}
    IF    '%{DMB_REPAIR_PREFLIGHT=true}' == 'true'
        Unselect Frame
        Open Single Track Metadata Editor    ${job}[source_dmb_release_id]
        Fill Single Track Metadata    ${job}    ${FALSE}
        Capture Page Screenshot    ${OUTPUT DIR}${/}repair-preflight.png
        Capture Active Form Source
        Pass Execution    Exact existing track reached review without saving
    END
    Should Be Equal    %{DMB_REPAIR_SUBMIT_ENABLED=false}    true
    IF    '%{DMB_REPAIR_RESUME=false}' != 'true'
        Set Edit Album Metadata    ${job}
        Replace Edit Contributors    ${job}[contributors]
        Verify Edit Form Data    ${job}
        ${save}=    Get WebElement    ${EDIT_SAVE_ACTION}
        Click Element    ${EDIT_SAVE_ACTION}
        Wait For Saved Form    ${save}
    ELSE
        Verify Edit Form Data    ${job}
    END
    Unselect Frame
    Configure Saved Album Profiles    ${job}    ${job}[source_dmb_release_id]    ${job}[source_dmb_ean_upc]    ${TRUE}
    Unselect Frame
    Open Single Track Metadata Editor    ${job}[source_dmb_release_id]
    ${track_job}=    Evaluate    dict($job, contributors=[dict(item, has_account=True) for item in $job['contributors']])
    Fill Single Track Metadata    ${track_job}
    Save Single Track Metadata
    Confirm Exact Saved Track    ${job}[source_dmb_release_id]    ${job}[source_dmb_ean_upc]    ${job}[source_dmb_isrcs][0]    ${job}[song_name]
    Publish Created Album And Verify Identity    ${job}[source_dmb_release_id]    ${job}[source_dmb_ean_upc]
    ${screenshot}=    Set Variable    ${OUTPUT DIR}${/}final-page-full.png
    Capture Element Screenshot    xpath=//html    ${screenshot}
    ${url}=    Get Location
    Write Dmb Result    %{DMB_RESULT_FILE}    ${job}[release_id]    ${job}[source_dmb_release_id]    ${job}[source_dmb_ean_upc]    ${job}[source_dmb_isrcs][0]    ${url}    ${screenshot}
    [Teardown]    Capture Failure Evidence And Close Browser
