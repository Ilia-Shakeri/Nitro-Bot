import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('dmb_profiles', Path(__file__).parents[1] / 'libraries' / 'dmb_profiles.py')
profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profiles)


def test_exact_store_ids_ignore_url_query():
    assert profiles.store_identity('https://open.spotify.com/artist/abc123?si=x', 'spotify') == 'abc123'
    assert profiles.store_identity('https://music.apple.com/us/artist/name/123456', 'apple') == '123456'
    assert profiles.store_identity('https://open.spotify.com:443/artist/abc123', 'spotify') == 'abc123'


@pytest.mark.parametrize('url', ['https://open.spotify.com/album/abc', 'https://open.spotify.com.evil/artist/abc', 'https://user@open.spotify.com/artist/abc', 'https://open.spotify.com:444/artist/abc'])
def test_wrong_profile_urls_rejected(url):
    with pytest.raises(ValueError):
        profiles.store_identity(url, 'spotify')


def test_shared_profile_conflict_blocks_all_changes():
    mapping = {'spotify_url': 'https://open.spotify.com/artist/right', 'apple_music_url': 'https://music.apple.com/artist/123'}
    with pytest.raises(ValueError, match='spotify_conflict'):
        profiles.profile_plan(mapping, {'spotify': 'wrong', 'apple': ''})


def test_existing_profile_is_idempotent_and_missing_store_gets_new():
    assert profiles.profile_plan({'spotify_url': 'https://open.spotify.com/artist/right'}, {'spotify': 'right', 'apple': 'new'}) == {'spotify': 'right', 'apple': 'new'}


def test_unrequested_existing_store_identity_is_preserved():
    assert profiles.profile_plan({'spotify_url': 'https://open.spotify.com/artist/right'}, {'spotify': 'right', 'apple': '123'}) == {'spotify': 'right', 'apple': '123'}


def test_new_profile_cannot_silently_reuse_an_existing_identity():
    with pytest.raises(ValueError, match='conflict'):
        profiles.profile_plan({'requires_new_profile': True}, {'spotify': 'existing'})


def test_new_profile_cannot_also_request_existing_link():
    with pytest.raises(ValueError, match='new_with_existing_link'):
        profiles.profile_plan({'requires_new_profile': True, 'spotify_url': 'https://open.spotify.com/artist/id'}, {})


@pytest.mark.parametrize('store,label', [('spotify', 'Spotify'), ('apple', 'AppleMusic | iTunes')])
def test_pending_profile_request_is_recognized_without_literal_new_id(store, label):
    from unittest.mock import MagicMock
    driver = MagicMock()
    driver.find_element.return_value.get_attribute.return_value = ''
    message = MagicMock()
    message.text = f'A new {label} profile request has been created on 2026-11-17.'
    driver.find_elements.return_value = [message]
    state = profiles.DmbProfiles()._store_state(driver, {'spotify': 'storeIds[2]', 'apple': 'storeIds[1]'})
    assert state[store] == 'new'
    assert state['apple' if store == 'spotify' else 'spotify'] == ''
    assert profiles.profile_plan({'requires_new_profile': True}, state)[store] == 'new'


def test_profile_warning_does_not_count_as_created_request():
    from unittest.mock import MagicMock
    driver = MagicMock()
    driver.find_element.return_value.get_attribute.return_value = ''
    message = MagicMock(); message.text = 'Spotify artist ID is missing'
    driver.find_elements.return_value = [message]
    assert profiles.DmbProfiles()._store_state(driver, {'spotify': 'storeIds[2]'}) == {'spotify': ''}


@pytest.mark.parametrize('count', [1, 2])
def test_contributor_suggestions_require_unique_exact_name(count):
    from unittest.mock import MagicMock, patch
    driver = MagicMock()
    choices = [MagicMock() for _ in range(count)]
    for choice in choices:
        choice.text = 'Artist "Name"'
        choice.is_displayed.return_value = True
    driver.find_elements.return_value = choices
    with patch.object(profiles.DmbProfiles, '_driver', return_value=driver):
        if count == 2:
            with pytest.raises(ValueError, match='identity_ambiguous'):
                profiles.select_contributor_suggestion('Artist "Name"')
            for choice in choices:
                choice.click.assert_not_called()
        else:
            profiles.select_contributor_suggestion('Artist "Name"')
            choices[0].click.assert_called_once()


def test_created_apple_profile_receipt_is_bound_to_release_and_exact_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(profiles, 'RESULTS_ROOT', tmp_path)
    job = {'release_id': 12}
    profiles.record_created_profile(job, '3755577', 'apple', 'Name', '6835857508',
        'New iTunes Artist with ID 6835857508 has been created.')
    receipt = profiles.read_profile_receipts(job)['3755577:apple']
    assert receipt['assigned_id'] == '6835857508'
    assert receipt['requested_new'] is True
    assert profiles.read_profile_receipts({'release_id': 13}) == {}
    with pytest.raises(ValueError, match='confirmation_missing'):
        profiles.record_created_profile(job, '3755577', 'apple', 'Name', 'other',
            'New iTunes Artist with ID 6835857508 has been created.')


def test_pending_request_takes_precedence_over_old_artist_id():
    from unittest.mock import MagicMock
    driver = MagicMock()
    driver.find_element.return_value.get_attribute.return_value = 'old-id'
    message = MagicMock(); message.text = 'A new Spotify profile request has been created on 2026-11-17.'
    driver.find_elements.return_value = [message]
    assert profiles.DmbProfiles()._store_state(driver, {'spotify': 'storeIds[2]'}) == {'spotify': 'new'}
