*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    String
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
    And User Fills Album Form With Database Data
    And User Uploads Track
    And User Selects Worldwide
    Then User Submits Album And Stores Evidence
    [Teardown]    Capture Failure Evidence And Close Browser

*** Keywords ***
Given User Is Logged In
    [Arguments]    ${username}    ${password}
    Wait Until Element Is Visible    ${USERNAME_FIELD}    timeout=10s
    Input Username    ${username}
    Input Password    ${password}
    Click Login Button
    Wait Until Page Contains    Music    timeout=15s

And User Loads Isolated Job Data
    ${job}=    Load Dmb Job    %{DMB_JOB_FILE}
    ${RELEASE_ID}=    Set Variable    ${job}[release_id]
    ${ALBUM_TITLE}=    Set Variable    ${job}[song_name]
    ${ARTISTS}=    Set Variable    ${job}[artists]
    ${PRODUCERS}=    Set Variable    ${job}[producers]
    ${LEGAL_NAMES}=    Set Variable    ${job}[legal_names]
    ${LEGAL_NAME}=    Set Variable    ${LEGAL_NAMES}[0]
    ${COVER_PATH}=    Set Variable    ${job}[cover_path]
    ${MUSIC_PATH}=    Set Variable    ${job}[track_path]
    ${RELEASE_DATE}=    Set Variable    ${job}[release_date]
    ${GENRE}=    Set Variable    ${job}[genre]
    ${SUB_GENRE}=    Set Variable    ${job}[sub_genre]
    ${IS_RERELEASE}=    Set Variable    ${job}[is_rerelease]
    ${ORIGINAL_RELEASE_DATE}=    Set Variable    ${job}[original_release_date]
    ${ARTIST_MAPPINGS}=    Set Variable    ${job}[artist_mappings]
    ${EXPLICIT_CONTENT}=    Set Variable    ${job}[explicit_content]
    ${COPYRIGHT_REQUESTED}=    Set Variable    ${job}[copyright_requested]
    ${COPYRIGHT_YEAR}=    Get Substring    ${RELEASE_DATE}    0    4
    Set Suite Variable    ${RELEASE_ID}
    Set Suite Variable    ${ALBUM_TITLE}
    Set Suite Variable    ${ARTISTS}
    Set Suite Variable    ${PRODUCERS}
    Set Suite Variable    ${LEGAL_NAMES}
    Set Suite Variable    ${LEGAL_NAME}
    Set Suite Variable    ${RELEASE_DATE}
    Set Suite Variable    ${COVER_PATH}
    Set Suite Variable    ${MUSIC_PATH}
    Set Suite Variable    ${GENRE}
    Set Suite Variable    ${SUB_GENRE}
    Set Suite Variable    ${IS_RERELEASE}
    Set Suite Variable    ${ORIGINAL_RELEASE_DATE}
    Set Suite Variable    ${ARTIST_MAPPINGS}
    Set Suite Variable    ${EXPLICIT_CONTENT}
    Set Suite Variable    ${COPYRIGHT_REQUESTED}
    Set Suite Variable    ${COPYRIGHT_YEAR}

When User Navigates To Album Creation Form
    Navigate To Album Creation Form
    Select Album Format And Next

And User Fills Album Form With Database Data
    ${EAN}=    Generate EAN Code
    Set Suite Variable    ${EAN}
    Upload Cover Image    ${COVER_PATH}
    Fill Album Title    ${ALBUM_TITLE}
    Set Language To English
    Select Genre    ${GENRE}
    Set Release Dates    ${RELEASE_DATE}    2099-12-31
    Set Price Codes
    Set Copyright Details    ${COPYRIGHT_YEAR}    ${LEGAL_NAME}
    FOR    ${artist}    IN    @{ARTISTS}
        Log    Adding contributor ${artist}[name] with role ${artist}[role]
        Add Contributor    ${artist}[name]
    END
    Click Next Button

And User Uploads Track
    Upload Track    ${MUSIC_PATH}
    ${ISRC}=    Fill Track Info And Generate ISRC    ${ALBUM_TITLE}
    Set Suite Variable    ${ISRC}
    Click Next And Wait For Upload

And User Selects Worldwide
    Select Worldwide And Next

Then User Submits Album And Stores Evidence
    Should Match Regexp    ${EAN}    ^[0-9]{8,14}$
    Should Match Regexp    ${ISRC}    ^[A-Za-z0-9-]{8,20}$
    Submit Album And Verify Success    ${RELEASE_ID}
    ${CURRENT_URL}=    Get Location
    ${DMB_RELEASE_ID}=    Extract Dmb Release Id    ${CURRENT_URL}
    ${SCREENSHOT}=    Set Variable    ${OUTPUT DIR}${/}submitted.png
    Capture Page Screenshot    ${SCREENSHOT}
    Write Dmb Result
    ...    %{DMB_RESULT_FILE}
    ...    ${RELEASE_ID}
    ...    ${DMB_RELEASE_ID}
    ...    ${EAN}
    ...    ${ISRC}
    ...    ${CURRENT_URL}
    ...    ${SCREENSHOT}
