*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    ../libraries/dmb_profiles.py
Resource   ../resources/pages/login_page.robot
Resource   ../resources/variables/global_vars.robot
Resource   ../resources/locators/login_locators.robot

*** Test Cases ***
Inspect Explicit Saved Contributor Without Saving
    [Setup]    Open Login Page
    Set Environment Variable    DMB_LOGIN_ALLOWED    false
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    ${data}=    Get File    %{DMB_PROFILE_PREFLIGHT_JOB}
    ${job}=    Evaluate    json.loads($data)    modules=json
    ${checks}=    Configure Saved Album Profiles    ${job}    %{DMB_PROFILE_PREFLIGHT_ALBUM}    %{DMB_PROFILE_PREFLIGHT_EAN}    ${FALSE}
    ${count}=    Get Length    ${checks}
    Should Be Equal As Integers    ${count}    2
    FOR    ${check}    IN    @{checks}
        Should Be Equal    ${check}[saved]    ${FALSE}
    END
    Capture Page Screenshot    ${OUTPUT DIR}${/}profile-preflight.png
    [Teardown]    Close Browser Session
