import os
import json
from fastapi.testclient import TestClient

from safemarket_pocket_sdk import create_adapter
from safemarket_pocket_sdk.core import Transaction, Config

# Import the FastAPI app from backend's main (this will create tables using testing DB when ENVIRONMENT=testing)
os.environ.setdefault('ENVIRONMENT', 'testing')
from main import app


def test_local_adapter_scoring():
    adapter = create_adapter(use_remote_api=False)
    tx = Transaction(id='tx_test_local', amount=1000.0, buyer_id='b1', seller_id='s1')
    res = adapter.validate_transaction(tx)
    assert isinstance(res, dict)
    assert 'decision' in res


def test_remote_api_scoring():
    client = TestClient(app)
    payload = {
        "user_id": "u1",
        "amount": 1200.0,
        "transaction_type": "PURCHASE",
        "source_type": "CARD",
        "currency": "USD",
        "merchant_risk_level": "LOW",
        "old_balance_orig": 5000.0,
        "new_balance_orig": 3800.0,
        "old_balance_dest": 0.0,
        "new_balance_dest": 1200.0
    }

    headers = {"x-api-key": "sm_demo_123"}
    r = client.post('/sdk/score', json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert 'decision' in data


if __name__ == '__main__':
    print('Running local adapter test...')
    test_local_adapter_scoring()
    print('Local adapter OK')
    print('Running remote API test via TestClient...')
    test_remote_api_scoring()
    print('Remote API test OK')
