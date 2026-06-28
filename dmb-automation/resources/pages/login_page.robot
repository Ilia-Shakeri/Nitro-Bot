*** Settings ***
Library    SeleniumLibrary
Resource   ../locators/login_locators.robot

*** Keywords ***
Open Login Page
    Open Browser    ${LOGIN_URL}    firefox
    Set Window Size    1366    768

Input Username
    [Arguments]    ${username}
    Wait Until Element Is Visible    ${USERNAME_FIELD}    timeout=10s
    Input Text    ${USERNAME_FIELD}    ${username}

Input Password
    [Arguments]    ${password}
    Wait Until Element Is Visible    ${PASSWORD_FIELD}    timeout=10s
    Input Text    ${PASSWORD_FIELD}    ${password}

Click Login Button
    Wait Until Element Is Enabled    ${LOGIN_BUTTON}    timeout=10s
    Click Button    ${LOGIN_BUTTON}

Login With Credentials
    [Arguments]    ${username}    ${password}
    Input Username    ${username}
    Input Password    ${password}
    Click Login Button

Close Browser Session
    Close Browser