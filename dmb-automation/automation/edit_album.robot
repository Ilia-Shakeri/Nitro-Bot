*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    ../libraries/dmb_job.py
Resource   ../resources/pages/login_page.robot
Resource   ../resources/pages/edit_album_page.robot
Resource   ../resources/locators/login_locators.robot

*** Test Cases ***
Edit Existing Album From Isolated Job
    [Setup]    Open Login Page
    Given User Is Logged In For Edit    ${VALID_USERNAME}    ${VALID_PASSWORD}
    And User Loads Isolated Edit Job
    When User Updates Exact Source Track
    When User Opens Exact Source Album
    And User Updates Album Metadata
    Then User Verifies Saves And Publishes Edit
    [Teardown]    Capture Edit Failure Evidence And Close Browser

*** Keywords ***
Given User Is Logged In For Edit
    [Arguments]    ${username}    ${password}
    Wait Until Element Is Visible    ${USERNAME_FIELD}    timeout=20s
    Input Username    ${username}
    Input Password    ${password}
    Click Login Button
    Wait Until Element Is Visible    ${MUSIC_MENU}    timeout=30s

And User Loads Isolated Edit Job
    ${JOB}=    Load Dmb Job    %{DMB_JOB_FILE}
    Should Be Equal As Strings    ${JOB}[mode]    edit
    Set Suite Variable    ${JOB}

When User Opens Exact Source Album
    Open Source Album In Edit Mode    ${JOB}[source_dmb_release_id]
    Verify Source Album Identity    ${JOB}[source_dmb_release_id]    ${JOB}[source_dmb_ean_upc]

When User Updates Exact Source Track
    Open Single Track Metadata Editor    ${JOB}[source_dmb_release_id]
    Fill Single Track Metadata    ${JOB}
    Write Submit Checkpoint
    ...    %{DMB_SUBMIT_CHECKPOINT}
    ...    ${JOB}[release_id]
    ...    ${JOB}[source_dmb_ean_upc]
    ...    ${JOB}[source_dmb_isrcs][0]
    ...    ${JOB}[song_name]
    Save Single Track Metadata

And User Updates Album Metadata
    Set Edit Album Metadata    ${JOB}
    IF    ${JOB}[replace_cover]
        Upload Edit Cover    ${JOB}[cover_path]
    END
    Replace Edit Contributors    ${JOB}[contributors]

Then User Verifies Saves And Publishes Edit
    Verify Edit Form Data    ${JOB}
    Save And Publish Edit    ${JOB}
    ${CURRENT_URL}=    Get Location
    ${DMB_RELEASE_ID}=    Extract Dmb Release Id    ${CURRENT_URL}
    Should Be Equal As Strings    ${DMB_RELEASE_ID}    ${JOB}[source_dmb_release_id]
    ${SCREENSHOT}=    Set Variable    ${OUTPUT DIR}${/}submitted.png
    Capture Page Screenshot    ${SCREENSHOT}
    Write Dmb Result
    ...    %{DMB_RESULT_FILE}
    ...    ${JOB}[release_id]
    ...    ${DMB_RELEASE_ID}
    ...    ${JOB}[source_dmb_ean_upc]
    ...    ${JOB}[source_dmb_isrcs][0]
    ...    ${CURRENT_URL}
    ...    ${SCREENSHOT}
