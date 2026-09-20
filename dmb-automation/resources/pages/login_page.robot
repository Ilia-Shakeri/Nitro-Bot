*** Settings ***
Library    SeleniumLibrary
Resource   ../locators/login_locators.robot

*** Keywords ***
Open Login Page
    ${options}=    Evaluate    selenium.webdriver.FirefoxOptions()    modules=selenium.webdriver
    IF    '${BROWSER_MODE}' == 'headless'
        Call Method    ${options}    add_argument    -headless
    ELSE IF    '${BROWSER_MODE}' != 'visible'
        Fail    DMB_browser_mode_invalid
    END
    Call Method    ${options}    set_preference    browser.cache.disk.enable    ${FALSE}
    Call Method    ${options}    set_preference    browser.sessionstore.resume_from_crash    ${FALSE}
    Open Browser    ${LOGIN_URL}    firefox    options=${options}
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
