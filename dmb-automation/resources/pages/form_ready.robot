*** Keywords ***
Wait For DMB Form Ready
    Wait Until Keyword Succeeds    45s    500ms    DMB Form Should Be Ready

DMB Form Should Be Ready
    ${ready}=    Execute Javascript    return document.readyState === 'complete' && typeof window.DMB === 'object' && typeof window.VC === 'object';
    Should Be True    ${ready}    DMB form scripts are not ready

Active Form Should Contain
    [Arguments]    ${expected}
    ${text}=    Execute Javascript    return document.body.innerText;
    Should Contain    ${text}    ${expected}
