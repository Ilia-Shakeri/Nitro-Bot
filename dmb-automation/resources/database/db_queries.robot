*** Settings ***
Resource   db_connection.robot

*** Keywords ***
Get Album Data From DB
    Connect To My Database
    ${data}=    Query    SELECT title, artist_name, legal_name, cover_image_path, music_file_path, release_date, genre FROM album_metadata LIMIT 1;
    Close Database Connection
    RETURN    ${data}