*** Settings ***
Library    SeleniumLibrary
Library    ../libraries/dmb_job.py
Resource   ../resources/pages/login_page.robot
Resource   ../resources/pages/album_page.robot
Resource   ../resources/variables/global_vars.robot
Resource   ../resources/locators/login_locators.robot

*** Test Cases ***
Publish Exact Saved Album From Checkpoint
    [Setup]    Open Login Page
    User Logs In For Publish Recovery
    User Publishes Exact Saved Album
    [Teardown]    Capture Failure Evidence And Close Browser

*** Keywords ***
User Logs In For Publish Recovery
    Wait Until Element Is Visible    ${USERNAME_FIELD}    timeout=20s
    Input Username    ${VALID_USERNAME}
    Input DMB Password    ${VALID_PASSWORD}
    Click Login Button
    Wait Until Page Contains Element    ${MUSIC_MENU}    timeout=30s

User Publishes Exact Saved Album
    Publish Created Album And Verify Identity
    ...    %{DMB_RECOVERY_DMB_ID}
    ...    %{DMB_RECOVERY_EAN}
    ${current_url}=    Get Location
    ${actual_dmb_id}=    Extract Dmb Release Id    ${current_url}
    Should Be Equal As Strings    ${actual_dmb_id}    %{DMB_RECOVERY_DMB_ID}
    ${screenshot}=    Set Variable    ${OUTPUT DIR}${/}published.png
    Capture Page Screenshot    ${screenshot}
    Write Dmb Result
    ...    %{DMB_RESULT_FILE}
    ...    %{DMB_RECOVERY_RELEASE_ID}
    ...    ${actual_dmb_id}
    ...    %{DMB_RECOVERY_EAN}
    ...    %{DMB_RECOVERY_ISRC}
    ...    ${current_url}
    ...    ${screenshot}
