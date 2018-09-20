import os
import collections
import asyncio

import dotenv


os.environ['SECRET_KEY'] = "s0secret"  # noqa
os.environ.setdefault('BITCOIN_URL', 'http://test:test@localhost:18443')
os.environ.setdefault('LITECOIN_URL', 'http://test:test@localhost:19332')
os.environ.setdefault('BITCOIN_CASH_URL', 'http://test:test@localhost:18332')
os.environ.setdefault('ETH_URL', 'http://localhost:8545')
os.environ.setdefault('ETH_CHAIN_ID', '1')
os.environ.setdefault('VAULT_URL', 'http://localhost:8200')
os.environ.setdefault('VAULT_SECRET_ID', 'vault-test')
os.environ.setdefault(
    'BUFFER_ETH_PRIV',
    '0x869844d42d74171d1c5e71ecd8964118e68f610af94047fd1e98afb4df1c5e1b'
)

dotenv.load_dotenv('.test.env')  # noqa

import pytest

import uvloop

from moonwalk.blocks.eth import EthereumProxy
from moonwalk import settings

from eth_utils.currency import to_wei
from eth_utils.address import to_checksum_address

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class EthHelper:

    MAIN_ADDR = to_checksum_address(
        '0x4a6a0f44e165bb2dc9afbc7574f82d2388a52638')
    MAIN_PRIV_KEY = \
        '0x869844d42d74171d1c5e71ecd8964118e68f610af94047fd1e98afb4df1c5e1b'

    def __init__(self):
        self.proxy = EthereumProxy()

    async def send_money(self, addr, amount):
        nonce = await self.proxy.post(
            'eth_getTransactionCount',
            self.MAIN_ADDR,
        )
        tx = {
            'from': self.MAIN_ADDR,
            'to': addr,
            'value': to_wei(amount, 'ether'),
            'gas': 22000,
            'gasPrice': to_wei(8, 'gwei'),
            'chainId': 1,
            'nonce': nonce,
        }
        return await self.proxy.post('eth_sendTransaction', tx)


class LndHelper:

    MAIN_ADDR = to_checksum_address(
        '0x4a6a0f44e165bb2dc9afbc7574f82d2388a52638')
    MAIN_PRIV_KEY = \
        '0x869844d42d74171d1c5e71ecd8964118e68f610af94047fd1e98afb4df1c5e1b'
    cd = os.path.dirname
    FIXTURE_DIR = os.path.join(cd(cd(__file__)), 'fixtures')
    COMPILED_CONTRACT_JSON = os.path.join(FIXTURE_DIR, 'LendingBlockToken.json')

    def __init__(self):
        self.proxy = EthereumProxy()

    async def create_contract(self):
        tx_hash = await self.proxy.post('eth_sendTransaction', {
            'from': self.MAIN_ADDR,
            'gas': 4000000,
            'gasPrice': 100,
            'data': settings.LND_CONTRACT['bytecode'],
        })
        receipt = await self.proxy.post(
            'eth_getTransactionReceipt',
            tx_hash
        )
        return receipt['contractAddress']


@pytest.fixture(autouse=True)
def loop():
    """Return an instance of the event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def eth_helper():
    yield EthHelper()


@pytest.fixture()
async def lnd_helper(mocker):
    lnd_helper = LndHelper()
    contract_addr = await lnd_helper.create_contract()
    mocker.patch(
        'moonwalk.blocks.lnd.LendingblockProxy.get_contract_addr',
        lambda self: contract_addr,
    )
    yield lnd_helper


async def calc_fee_mock(self, tx):
    return 500


async def get_gas_price_mock(self):
    return to_wei(10, 'gwei')


@pytest.fixture()
async def fee_mocker(mocker):
    mocker.patch(
        'moonwalk.blocks.bitcoin.BitcoinProxy.calc_fee',
        calc_fee_mock
    )
    mocker.patch(
        'moonwalk.blocks.ltc.LitecoinProxy.calc_fee',
        calc_fee_mock
    )
    mocker.patch(
        'moonwalk.blocks.bitcoin_cash.BitcoinCashProxy.calc_fee',
        lambda x, y, z: 500
    )
    mocker.patch(
        'moonwalk.blocks.eth.EthereumProxy.get_gas_price',
        get_gas_price_mock
    )
