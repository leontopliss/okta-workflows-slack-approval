import pytest
import main
from time import time
import hmac
import hashlib
from unittest.mock import Mock
from unittest.mock import MagicMock


def test_valid_signature():
    timestamp = int(time())
    slack_signing_secret = 'abcdefg'
    main.slack_signing_secret = slack_signing_secret
    req_body = 'abcdefgabcdefgabcdefgabcdefg'

    signature = create_signature(timestamp,req_body,slack_signing_secret)
    
    headers = {
        'X-Slack-Signature': signature,
        'X-Slack-Request-Timestamp': str(timestamp)
    }

    decode = Mock(decode=Mock(return_value=req_body))
    req = Mock(get_data=Mock(return_value=decode), headers=headers)

    assert main.verify_slack_signature(req) == True


def test_invalid_signature_secret_invalid():
    timestamp = int(time())
    slack_signing_secret = 'abcdefg'
    main.slack_signing_secret = 'qwerty'
    req_body = 'abcdefgabcdefgabcdefgabcdefg'

    signature = create_signature(timestamp,req_body,slack_signing_secret)

    headers = {
        'X-Slack-Signature': signature,
        'X-Slack-Request-Timestamp': str(timestamp)
    }

    decode = Mock(decode=Mock(return_value=req_body))
    req = Mock(get_data=Mock(return_value=decode), headers=headers)

    assert main.verify_slack_signature(req) == False


def test_invalid_signature_old_timestamp():
    timestamp = int(time()) - 86400
    slack_signing_secret = 'abcdefg'
    main.slack_signing_secret = slack_signing_secret
    req_body = 'abcdefgabcdefgabcdefgabcdefg'

    signature = create_signature(timestamp,req_body,slack_signing_secret)
    
    headers = {
        'X-Slack-Signature': signature,
        'X-Slack-Request-Timestamp': str(timestamp)
    }

    decode = Mock(decode=Mock(return_value=req_body))
    req = Mock(get_data=Mock(return_value=decode), headers=headers)

    assert main.verify_slack_signature(req) == False

def test_invalid_signature_signature_missing():
    timestamp = int(time())
    req_body = 'abcdefgabcdefgabcdefgabcdefg'

    headers = {
        'X-Slack-Request-Timestamp': str(timestamp)
    }

    decode = Mock(decode=Mock(return_value=req_body))
    req = Mock(get_data=Mock(return_value=decode), headers=headers)

    assert main.verify_slack_signature(req) == False

def test_invalid_signature_timestamp_missing():
    req_body = 'abcdefgabcdefgabcdefgabcdefg'
    
    headers = {
        'X-Slack-Signature': 'dadsdasadsads'
    }

    decode = Mock(decode=Mock(return_value=req_body))
    req = Mock(get_data=Mock(return_value=decode), headers=headers)

    assert main.verify_slack_signature(req) == False

def create_signature(timestamp,req_body,slack_signing_secret):
    signature_string = str.encode('v0:' + str(timestamp) + ':' + req_body)
    signature = 'v0=' + hmac.new(str.encode(slack_signing_secret),
                                signature_string,
                                hashlib.sha256).hexdigest()
    return signature