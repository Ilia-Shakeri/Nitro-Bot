*** Variables ***
# --- اطلاعات ورود به سایت DMB ---
${LOGIN_URL}            https://dmb.kontornewmedia.com/
# Credentials are read from the environment (set by the worker / docker-compose).
${VALID_USERNAME}         %{DMB_USERNAME}
${VALID_PASSWORD}         %{DMB_PASSWORD}

