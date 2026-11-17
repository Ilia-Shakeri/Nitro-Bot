*** Settings ***
Library    SeleniumLibrary
Library    ../../libraries/dmb_session.py
Resource   ../locators/login_locators.robot

*** Keywords ***
Open Login Page
    Acquire Dmb Session
    Open Persistent Dmb Browser    ${BROWSER_MODE}

Input Username
    [Arguments]    ${username}
    Wait Until Element Is Visible    ${USERNAME_FIELD}    timeout=10s
    Input Text    ${USERNAME_FIELD}    ${username}

Input DMB Password
    [Arguments]    ${password}
    Wait Until Element Is Visible    ${PASSWORD_FIELD}    timeout=10s
    SeleniumLibrary.Input Password    ${PASSWORD_FIELD}    ${password}

Click Login Button
    Wait Until Element Is Enabled    ${LOGIN_BUTTON}    timeout=10s
    Click Button    ${LOGIN_BUTTON}

Login With Credentials
    [Arguments]    ${username}    ${password}
    ${previous_level}=    Set Log Level    NONE
    TRY
        Ensure Dmb Authenticated
    FINALLY
        Set Log Level    ${previous_level}
    END

Close Browser Session
    TRY
        Save Dmb Session
    FINALLY
        Release Dmb Session
    END
