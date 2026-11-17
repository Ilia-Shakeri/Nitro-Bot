*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Resource   ../resources/pages/login_page.robot
Resource   ../resources/pages/album_page.robot
Resource   ../resources/variables/global_vars.robot

*** Test Cases ***
Verify Single Creation Route Without Saving Or Logging In
    [Setup]    Open Login Page
    Set Environment Variable    DMB_LOGIN_ALLOWED    false
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Navigate To Album Creation Form
    Select Album Format And Next
    Element Should Be Visible    ${EAN_INPUT}
    Capture Page Screenshot    ${OUTPUT DIR}${/}single-form.png
    Capture Active Form Source
    [Teardown]    Capture Failure Evidence And Close Browser
