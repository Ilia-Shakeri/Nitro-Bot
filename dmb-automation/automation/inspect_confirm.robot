*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Resource   ../resources/pages/login_page.robot
Resource   ../resources/variables/global_vars.robot
Resource   ../resources/locators/login_locators.robot

*** Test Cases ***
Inspect Track Confirmation Form
    [Setup]    Open Login Page
    Set Environment Variable    DMB_LOGIN_ALLOWED    false
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    ${album_id}=    Get Environment Variable    DMB_INSPECT_ID
    Go To    ${LOGIN_URL}page/album/${album_id}
    Wait Until Element Is Visible    xpath=//iframe[contains(@src, '/page/album/')]    timeout=30s
    Select Frame    xpath=//iframe[contains(@src, '/page/album/')]
    Wait Until Element Is Visible    xpath=//button[contains(@onclick, 'album-confirm-tracks')]    timeout=30s
    Click Element    xpath=//button[contains(@onclick, 'album-confirm-tracks')]
    Sleep    3s
    Unselect Frame
    ${source}=    Execute Javascript    return document.documentElement.outerHTML;
    Create File    ${OUTPUT DIR}${/}confirm-state.html    ${source}
    Capture Page Screenshot    ${OUTPUT DIR}${/}confirm-state.png
    [Teardown]    Close Browser Session
