*** Settings ***
Library    DatabaseLibrary
Resource   ../variables/db_vars.robot

*** Keywords ***
Connect To My Database
    Connect To Database    sqlite3    database=${DB_PATH}

Close Database Connection
    Disconnect From Database