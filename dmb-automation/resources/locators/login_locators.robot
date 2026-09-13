*** Variables ***
# --- آدرس صفحه لاگین ---
${LOGIN_URL}    https://dmb.kontornewmedia.com/

# --- المان‌های صفحه لاگین ---
${USERNAME_FIELD}    //dmb-input[@id='user']//input
${PASSWORD_FIELD}    //dmb-input[@id='pass']//input
${LOGIN_BUTTON}      //dmb-button[@type='submit']//button[@type='submit']

# --- المان‌های بعد از لاگین موفق ---
${MUSIC_MENU}        xpath=//div[contains(@class, 'text-label') and normalize-space()='Audio']
${CREATE_ALBUM_LINK}    xpath=//a[normalize-space()='Create audio product']
${MAIN_IFRAME}       xpath=//iframe[contains(@src, 'album.create')]
