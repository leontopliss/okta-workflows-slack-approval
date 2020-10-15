import pytest
import main
import json

from unittest.mock import Mock


def test_valid_api_key():
    main.notification_key = 'abcdefghijklmnop'
    assert main.api_key_valid('abcdefghijklmnop') == True

def test_invalid_api_key():
    main.notification_key = 'abcdefghijklmn'
    assert main.api_key_valid('abcdefghijklmnop') == False

def test_mock_no_api_key():
    data = {'title': 'test'}
    headers = {}
    req = Mock(get_json=Mock(return_value=data), headers=headers)

    # Call tested function
    assert main.approval_notify(req) == ('unauthorized', 403)

def test_mock_invalid_api_key():
    main.notification_key = 'abcdefghijklmnop'
    data = {'title': 'test'}
    headers = {'X-Api-Key': 'abcdefghijkl'}
    req = Mock(get_json=Mock(return_value=data), headers=headers)

    # Call tested function
    assert main.approval_notify(req) == ('unauthorized', 403)

def test_mock_data_missing():
    main.notification_key = 'abcdefghijklmnop'
    data = {'title': 'test'}
    headers = {'X-Api-Key': 'abcdefghijklmnop'}
    req = Mock(get_json=Mock(return_value=data), headers=headers)

    # Call tested function
    assert main.approval_notify(req) == ('payload malformed or mandatory data missing', 500)


def test_mock_with_data():
    main.notification_key = 'abcdefghijklmnop'
    main.slack_token = 'abcdefghijklmnop'
    data = {
        'title': 'test title', 
        'type': 'test approval', 
        'data': json.dumps({'name': 'john smith'}), 
        'msg_fields': ['name'], 
        'slack_channel': 'dadasas' 
    }
    headers = {'X-Api-Key': 'abcdefghijklmnop'}
    req = Mock(get_json=Mock(return_value=data), headers=headers)

    # Call tested function
    assert main.approval_notify(req) == ('error posting to slack', 500)