import os
import json

import dotenv


dotenv.load_dotenv()

cd = os.path.dirname
ROOT_DIR = cd(__file__)
SECRET_KEY = os.environ.get('SECRET_KEY') or 's0secret'

LITECOIN_FEE = os.environ.get('LITECOIN_FEE') or '10'  # satoshi / byte
LITECOIN_URL = os.environ.get('LITECOIN_URL')
BITCOIN_CASH_FEE = os.environ.get('BITCOIN_CASH_FEE') or '10'  # satoshi / byte
BITCOIN_CASH_URL = os.environ.get('BITCOIN_CASH_URL')
BITCOIN_URL = os.environ.get('BITCOIN_URL')
BITCOIN_FEE = os.environ.get('BITCOIN_FEE')  # satoshi / byte
BITCOIN_FEE_URL = os.environ.get('BITCOIN_FEE_URL')
ETH_FEE = os.environ.get('ETH_FEE')  # gas price in gwei
ETH_URL = os.environ.get('ETH_URL')
ETH_CHAIN_ID = os.environ.get('ETH_CHAIN_ID') or '4'

BUFFER_ETH_PRIV = os.environ.get('BUFFER_ETH_PRIV')
LND_CONTRACT_ADDR = os.environ.get('LND_CONTRACT_ADDR')
USE_TESTNET = (os.environ.get('USE_TESTNET') or '1') == "1"

COMPILED_CONTRACT_JSON = os.path.join(ROOT_DIR, 'LendingBlockToken.json')

with open(COMPILED_CONTRACT_JSON) as fp:
    LND_CONTRACT = json.load(fp)

MAIN_LND_ADDR = os.environ.get('MAIN_LND_ADDR')
MAIN_LND_PRIV = os.environ.get('MAIN_LND_PRIV')
MAIN_ETH_ADDR = os.environ.get('MAIN_ETH_ADDR')
MAIN_ETH_PRIV = os.environ.get('MAIN_ETH_PRIV')


assert BITCOIN_FEE is None or BITCOIN_FEE.isdigit(), \
    'BITCOIN_FEE must be None or an integer'
assert ETH_FEE is None or ETH_FEE.isdigit(), \
    'ETH_FEE must be None or an integer'
assert BITCOIN_CASH_FEE.isdigit(), 'BITCOIN_CASH_FEE must be an integer'
assert LITECOIN_FEE.isdigit(), 'LITECOIN_FEE must be an integer'