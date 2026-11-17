"""Match saved contributors to explicit store identities before publication."""

import os
import re
import json
from pathlib import Path
from urllib.parse import urlparse
from robot.api.deco import keyword

ROBOT_AUTO_KEYWORDS = False
RESULTS_ROOT = Path(__file__).resolve().parents[1] / 'results'


def profile_receipt_path(job):
    release_id = str(job['release_id'])
    if not re.fullmatch(r'[1-9][0-9]*', release_id):
        raise ValueError('dmb_profile_release_id_invalid')
    return RESULTS_ROOT / release_id / 'profile-requests.json'


def read_profile_receipts(job):
    path = profile_receipt_path(job)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('dmb_profile_receipts_invalid')
    return data


def record_created_profile(job, contributor_id, store, artist_name, assigned_id, confirmation):
    if store != 'apple' or not re.fullmatch(r'[0-9]+', str(contributor_id)):
        raise ValueError('dmb_profile_receipt_invalid')
    match = re.search(r'New iTunes Artist with ID ([0-9]+) has been created\.', confirmation)
    if not match or match.group(1) != str(assigned_id):
        raise ValueError('dmb_profile_new_confirmation_missing')
    data = read_profile_receipts(job)
    data[f'{contributor_id}:{store}'] = {
        'artist_name': artist_name, 'assigned_id': str(assigned_id),
        'confirmation': match.group(0), 'requested_new': True,
    }
    path = profile_receipt_path(job)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False)
    temporary.replace(path)


def store_identity(value, store):
    if not value:
        return None
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError('dmb_profile_url_invalid')
    parsed = urlparse(value.strip())
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port not in (None, 443) or parsed.fragment:
        raise ValueError('dmb_profile_url_invalid')
    if store == 'spotify':
        match = re.fullmatch(r'/artist/([A-Za-z0-9]+)/*', parsed.path)
        valid = parsed.hostname == 'open.spotify.com'
    elif store == 'apple':
        match = re.fullmatch(r'/(?:[a-z]{2}/)?artist/(?:[^/]+/)?([0-9]+)/*', parsed.path)
        valid = parsed.hostname == 'music.apple.com'
    else:
        raise ValueError('dmb_profile_store_invalid')
    if not valid or not match:
        raise ValueError('dmb_profile_url_invalid')
    return match.group(1)


def profile_plan(mapping, current):
    """Reject conflicting shared profiles before making any store change."""
    result = {}
    for store, field in [('spotify', 'spotify_url'), ('apple', 'apple_music_url')]:
        expected = store_identity(mapping.get(field), store)
        actual = str(current.get(store) or '').strip()
        if mapping.get('requires_new_profile') and expected:
            raise ValueError('dmb_profile_new_with_existing_link')
        expected = expected or (actual if actual and not mapping.get('requires_new_profile') else 'new')
        if actual and actual != expected:
            raise ValueError(f'dmb_profile_{store}_conflict')
        result[store] = expected
    return result


class DmbProfiles:
    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _driver(self):
        from robot.libraries.BuiltIn import BuiltIn
        return BuiltIn().get_library_instance('SeleniumLibrary').driver

    def _store_state(self, driver, fields):
        from selenium.webdriver.common.by import By
        messages = [e.text for e in driver.find_elements(By.CSS_SELECTOR, '.dmb-message__text')]
        result = {}
        for store, field in fields.items():
            value = driver.find_element(By.NAME, field).get_attribute('value')
            store_pattern = r'Spotify' if store == 'spotify' else r'Apple|iTunes'
            pending = any(re.search(store_pattern, text, re.I) and re.search(
                r'new\s+.+?profile request has been created', text, re.I
            ) for text in messages)
            result[store] = 'new' if pending else (value or '')
        return result

    def _open(self, path):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as E
        from selenium.webdriver.support.ui import WebDriverWait
        driver = self._driver()
        driver.switch_to.default_content()
        driver.get('https://dmb.kontornewmedia.com/' + path)
        wait = WebDriverWait(driver, 60)
        wait.until(E.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe')))
        wait.until(lambda d: d.execute_script(
            "return document.readyState==='complete' && !!window.DMB && !!window.VC"))
        return driver, wait

    def configure_saved_album_profiles(self, job, album_id, ean, submit=False):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as E
        if submit and os.getenv('DMB_PUBLISH_ENABLED') != 'true':
            raise ValueError('dmb_profile_submit_disabled')
        if not re.fullmatch(r'[0-9]+', str(album_id)):
            raise ValueError('dmb_profile_album_id_invalid')
        driver, wait = self._open(f'page/album/{album_id}')
        wait.until(E.presence_of_element_located((By.CSS_SELECTOR, 'input[name="ean"]')))
        if driver.find_element(By.CSS_SELECTOR, 'input[name="ean"]').get_attribute('value') != str(ean):
            raise ValueError('dmb_profile_album_identity_mismatch')
        bindings = driver.execute_script("""
            return Array.from(document.querySelectorAll('tr.js-dmb-cce__item'))
                .map(row => ({name: row.querySelector('.dmb-js-artist-name')?.textContent.trim(),
                    id: row.querySelector('.dmb-js-cce__a-id')?.value}))
                .filter(row => row.name && row.id);
        """)
        mapping_ids = []
        for mapping in job['artist_mappings']:
            name = mapping['artist_name'].strip().casefold()
            matches = {row['id'] for row in bindings if row['name'].strip().casefold() == name}
            if len(matches) != 1:
                raise ValueError('dmb_profile_contributor_identity_mismatch')
            contributor_id = matches.pop()
            if not re.fullmatch(r'[0-9]+', contributor_id):
                raise ValueError('dmb_profile_contributor_id_invalid')
            mapping_ids.append((mapping, contributor_id))
        results = []
        for mapping, contributor_id in mapping_ids:
            driver, wait = self._open(f'page/contributor/{contributor_id}')
            name_input = wait.until(E.presence_of_element_located((By.CSS_SELECTOR, 'input[name="name"]')))
            if name_input.get_attribute('value').strip().casefold() != mapping['artist_name'].strip().casefold():
                raise ValueError('dmb_profile_contributor_name_mismatch')
            fields = {'apple': 'storeIds[1]', 'spotify': 'storeIds[2]'}
            current = self._store_state(driver, fields)
            receipts = read_profile_receipts(job)
            for store in fields:
                receipt = receipts.get(f'{contributor_id}:{store}', {})
                if (mapping.get('requires_new_profile') and receipt.get('requested_new') is True
                        and receipt.get('artist_name') == mapping['artist_name']
                        and receipt.get('assigned_id') == current[store]):
                    current[store] = 'new'
            plan = profile_plan(mapping, current)
            for store, expected in plan.items():
                if current[store] == expected:
                    continue
                if expected == 'new':
                    driver, wait = self._open(f'page/contributor-artist-id/{contributor_id}')
                    label = 'Spotify' if store == 'spotify' else 'AppleMusic | iTunes'
                    choice = wait.until(E.element_to_be_clickable((By.XPATH,
                        f"//li[.//span[normalize-space()='{label}']]")))
                    choice.click()
                    wait.until(E.staleness_of(choice))
                    wait.until(lambda d: d.execute_script(
                        "return document.readyState==='complete' && !!window.DMB && !!window.VC && (!window.jQuery || jQuery.active===0)"))
                    store_id = '2' if store == 'spotify' else '1'
                    wait.until(lambda d: d.find_element(By.NAME, 'storeId').get_attribute('value') == store_id)
                    radio = wait.until(E.presence_of_element_located((By.CSS_SELECTOR,
                        'input[name="artistId"][value="new"]')))
                    driver.execute_script('arguments[0].click()', radio)
                    if not radio.is_selected():
                        raise ValueError('dmb_profile_new_not_selected')
                    if driver.execute_script('return new FormData(arguments[0].form).get("artistId")', radio) != 'new':
                        raise ValueError('dmb_profile_new_payload_mismatch')
                else:
                    driver, wait = self._open(f'page/contributor/{contributor_id}')
                    field = wait.until(E.visibility_of_element_located((By.NAME, fields[store])))
                    field.clear()
                    field.send_keys(expected)
                if submit:
                    save = driver.find_element(By.XPATH, '//a[contains(@onclick,\'"action":"save"\')]')
                    driver.execute_script('arguments[0].click()', save)
                    wait.until(E.staleness_of(save))
                    created_id = None
                    confirmation = ''
                    if expected == 'new' and store == 'apple':
                        wait.until(lambda d: d.execute_script("return document.readyState==='complete' && !!window.DMB && !!window.VC"))
                        confirmation = '\n'.join(e.text for e in driver.find_elements(By.CSS_SELECTOR, '.dmb-message__text'))
                        match = re.search(r'New iTunes Artist with ID ([0-9]+) has been created\.', confirmation)
                        if not match:
                            raise ValueError('dmb_profile_new_confirmation_missing')
                        created_id = match.group(1)
                    driver, wait = self._open(f'page/contributor/{contributor_id}')
                    wait.until(lambda d: self._store_state(d, fields)[store] == (created_id or expected))
                    if created_id:
                        record_created_profile(job, contributor_id, store, mapping['artist_name'], created_id, confirmation)
                results.append({'store': store, 'expected': expected, 'saved': bool(submit)})
        return results


@keyword
def configure_saved_album_profiles(job, album_id, ean, submit: bool = False):
    return DmbProfiles().configure_saved_album_profiles(job, album_id, ean, submit)


@keyword
def reuse_saved_contributors(job):
    driver = DmbProfiles()._driver()
    bindings = driver.execute_script("""
        return Array.from(document.querySelectorAll('tr.js-dmb-cce__item'))
            .map(row => ({name: row.querySelector('.dmb-js-artist-name')?.textContent.trim(),
                id: row.querySelector('.dmb-js-cce__a-id')?.value}))
            .filter(row => row.name && row.id);
    """)
    contributors = []
    for item in job['contributors']:
        matches = {row['id'] for row in bindings if row['name'].casefold() == item['name'].strip().casefold()}
        if len(matches) > 1:
            raise ValueError('dmb_contributor_identity_ambiguous')
        contributors.append(dict(item, has_account=True) if matches else dict(item))
    return dict(job, contributors=contributors)


@keyword
def wait_for_saved_form(element):
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as E
    WebDriverWait(DmbProfiles()._driver(), 60).until(E.staleness_of(element))


@keyword
def set_dmb_checkbox(locator, selected: bool = True):
    from robot.libraries.BuiltIn import BuiltIn
    library = BuiltIn().get_library_instance('SeleniumLibrary')
    element = library.get_webelement(locator)
    if element.is_selected() == selected:
        return
    if not element.is_enabled():
        raise ValueError('dmb_checkbox_disabled')
    library.driver.execute_script("""
        const input = arguments[0];
        const label = Array.from(document.querySelectorAll('label'))
            .find(candidate => candidate.htmlFor === input.id);
        (label || input).click();
    """, element)
    if element.is_selected() != selected:
        raise ValueError('dmb_checkbox_state_mismatch')


@keyword
def set_performer_role(locator):
    from robot.libraries.BuiltIn import BuiltIn
    library = BuiltIn().get_library_instance('SeleniumLibrary')
    element = library.get_webelement(locator)
    library.driver.execute_script("""
        const select = arguments[0];
        Array.from(select.options).forEach(option => {
            option.selected = option.textContent.trim() === 'Performer';
        });
        select.dispatchEvent(new Event('change', {bubbles: true}));
    """, element)
    if library.get_selected_list_labels(locator) != ['Performer']:
        raise ValueError('dmb_contributor_performer_role_missing')


@keyword
def select_contributor_suggestion(name):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    driver = DmbProfiles()._driver()
    def exact_choice(_):
        choices = [element for element in driver.find_elements(By.CSS_SELECTOR,
            '.vc-js-ajax-result-list td, .ui-autocomplete .ui-menu-item-wrapper')
            if element.is_displayed() and element.text.strip() == name]
        if len(choices) > 1:
            raise ValueError('dmb_contributor_identity_ambiguous')
        return choices[0] if choices else False
    WebDriverWait(driver, 20).until(exact_choice).click()
