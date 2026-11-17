*** Settings ***
Library    SeleniumLibrary
Library    OperatingSystem
Library    ../libraries/dmb_job.py
Resource   ../resources/pages/login_page.robot
Resource   ../resources/pages/album_page.robot
Resource   ../resources/variables/global_vars.robot

*** Test Cases ***
Missing Track Metadata Must Block Publication
    [Setup]    Open Login Page
    Set Environment Variable    DMB_LOGIN_ALLOWED    false
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    ${job}=    Load Dmb Job    %{DMB_JOB_FILE}
    Run Keyword And Expect Error    *DMB track confirmation rejected*
    ...    Confirm Exact Saved Track    ${job}[source_dmb_release_id]    ${job}[source_dmb_ean_upc]    ${job}[source_dmb_isrcs][0]    ${job}[song_name]
    Active Form Should Contain    Audio language is required
    Active Form Should Contain    The pricecode is missing
    Capture Page Screenshot    ${OUTPUT DIR}${/}metadata-required.png
    [Teardown]    Capture Failure Evidence And Close Browser
