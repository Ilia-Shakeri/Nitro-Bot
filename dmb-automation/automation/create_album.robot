*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    String
Resource   ../resources/pages/login_page.robot
Resource   ../resources/pages/album_page.robot
Resource   ../resources/database/db_queries.robot
Resource   ../resources/variables/global_vars.robot
Resource   ../resources/locators/login_locators.robot

*** Test Cases ***
End-to-End Album Creation From Database
    [Setup]    Open Login Page
    Given User Is Logged In    ${VALID_USERNAME}    ${VALID_PASSWORD}
    And User Fetches Album Data From Database
    When User Navigates To Album Creation Form
    And User Fills Album Form With Database Data
    And User Uploads Track
    And User Selects Worldwide
    Then Album Form Should Be Completed Successfully
    [Teardown]    Close Browser Session

*** Keywords ***
Given User Is Logged In
    [Arguments]    ${username}    ${password}
    Wait Until Element Is Visible    ${USERNAME_FIELD}    timeout=10s
    Input Username    ${username}
    Input Password    ${password}
    Click Login Button
    Wait Until Page Contains    Music    timeout=15s

And User Fetches Album Data From Database
    ${result}=    Get Album Data From DB
    ${ALBUM_TITLE}=    Set Variable    ${result}[0][0]
    ${ARTIST_NAME}=    Set Variable    ${result}[0][1]
    ${LEGAL_NAME}=    Set Variable    ${result}[0][2]
    ${COVER_PATH}=    Set Variable    ${result}[0][3]
    ${MUSIC_PATH}=    Set Variable    ${result}[0][4]
    ${RELEASE_DATE}=    Set Variable    ${result}[0][5]
    ${GENRE}=    Set Variable    ${result}[0][6]
    ${COPYRIGHT_YEAR}=    Get Substring    ${RELEASE_DATE}    0    4
    Set Suite Variable    ${ALBUM_TITLE}
    Set Suite Variable    ${ARTIST_NAME}
    Set Suite Variable    ${LEGAL_NAME}
    Set Suite Variable    ${RELEASE_DATE}
    Set Suite Variable    ${COVER_PATH}
    Set Suite Variable    ${MUSIC_PATH}
    Set Suite Variable    ${GENRE}
    Set Suite Variable    ${COPYRIGHT_YEAR}

When User Navigates To Album Creation Form
    Navigate To Album Creation Form
    Select Album Format And Next

And User Fills Album Form With Database Data
    Generate EAN Code
    Upload Cover Image    ${COVER_PATH}
    Fill Album Title    ${ALBUM_TITLE}
    Set Language To English
    Select Genre    ${GENRE}
    Set Release Dates    ${RELEASE_DATE}    2099-12-31
    Set Price Codes
    Set Copyright Details    ${COPYRIGHT_YEAR}    ${LEGAL_NAME}
    Add Contributor    ${ARTIST_NAME}
    Click Next Button

And User Uploads Track
    Upload Track    ${MUSIC_PATH}
    Fill Track Info And Generate ISRC    ${ALBUM_TITLE}
    Click Next And Wait For Upload

And User Selects Worldwide
    Select Worldwide And Next

Then Album Form Should Be Completed Successfully
    Element Should Be Visible    ${EAN_INPUT}
    Element Should Be Visible    ${TITLE_INPUT}
    Element Should Be Visible    ${C_LINE_TEXT}