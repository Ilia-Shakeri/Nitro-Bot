*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    ../libraries/dmb_job.py
Resource   ../resources/pages/login_page.robot
Resource   ../resources/pages/album_page.robot
Resource   ../resources/variables/global_vars.robot
Resource   ../resources/locators/login_locators.robot

*** Test Cases ***
End-to-End Album Creation From Isolated Job
    [Setup]    Open Login Page
    Given User Is Logged In    ${VALID_USERNAME}    ${VALID_PASSWORD}
    And User Loads Isolated Job Data
    When User Navigates To Album Creation Form
    And User Fills Album Form
    And User Adds Track
    And User Selects Territory And Platforms
    Then User Verifies And Submits Album
    [Teardown]    Capture Failure Evidence And Close Browser

*** Keywords ***
Given User Is Logged In
    [Arguments]    ${username}    ${password}
    Wait Until Element Is Visible    ${USERNAME_FIELD}    timeout=20s
    Input Username    ${username}
    Input Password    ${password}
    Click Login Button
    Wait Until Element Is Visible    ${MUSIC_MENU}    timeout=30s

And User Loads Isolated Job Data
    ${JOB}=    Load Dmb Job    %{DMB_JOB_FILE}
    Set Suite Variable    ${JOB}

When User Navigates To Album Creation Form
    Navigate To Album Creation Form
    Select Album Format And Next

And User Fills Album Form
    ${EAN}=    Generate EAN Code
    Set Suite Variable    ${EAN}
    Upload Cover Image    ${JOB}[cover_path]
    Fill Album Title    ${JOB}[song_name]
    Set Language To English
    Select DMB Genre    ${JOB}[dmb_genre]
    Set Label    ${JOB}[label]
    Set Release Dates    ${JOB}[release_date]    ${JOB}[expiration_date]
    Set Price Codes    ${JOB}[price_code]    ${JOB}[itunes_price_code]
    Set Copyright Details    ${JOB}[c_line_year]    ${JOB}[p_line_year]    ${JOB}[label]
    FOR    ${contributor}    IN    @{JOB}[contributors]
        Add DMB Contributor    ${contributor}[name]    ${contributor}[has_account]
    END
    Click Ready Next
    Wait Until Element Is Visible    ${ADD_TRACKS_BUTTON}    timeout=120s

And User Adds Track
    Open Add Tracks
    Upload Track    ${JOB}[track_path]
    ${ISRC}=    Fill Track Info And Generate ISRC    ${JOB}[song_name]
    Set Suite Variable    ${ISRC}
    Continue To Territory Page

And User Selects Territory And Platforms
    Select Worldwide And Next
    Select All Platforms And Next

Then User Verifies And Submits Album
    Should Match Regexp    ${EAN}    ^[0-9]{8,14}$
    Should Match Regexp    ${ISRC}    ^[A-Za-z0-9-]{8,20}$
    Verify Review Data
    ...    ${JOB}[song_name]
    ...    ${EAN}
    ...    ${ISRC}
    ...    ${JOB}[release_date]
    ...    ${JOB}[dmb_genre]
    ...    ${JOB}[label]
    ...    ${JOB}[contributors]
    Submit Album And Verify Success    ${JOB}[release_id]
    ${CURRENT_URL}=    Get Location
    ${DMB_RELEASE_ID}=    Extract Dmb Release Id    ${CURRENT_URL}
    ${SCREENSHOT}=    Set Variable    ${OUTPUT DIR}${/}submitted.png
    Capture Page Screenshot    ${SCREENSHOT}
    Write Dmb Result
    ...    %{DMB_RESULT_FILE}
    ...    ${JOB}[release_id]
    ...    ${DMB_RELEASE_ID}
    ...    ${EAN}
    ...    ${ISRC}
    ...    ${CURRENT_URL}
    ...    ${SCREENSHOT}
