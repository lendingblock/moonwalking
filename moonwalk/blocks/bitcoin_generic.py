import io
from typing import List, Tuple
from binascii import unhexlify
from decimal import Decimal as D

from aiohttp import ClientSession
from bitcoin import SelectParams
from bitcoin.core import COIN, lx, COutPoint
from bitcoin.core.script import CScript
from bitcoin.wallet import CBitcoinAddress
from pycoin.key import Key
from pycoin.tx.Tx import Tx
from pycoin.tx.Spendable import Spendable
from pycoin.tx.TxOut import TxOut
from pycoin.tx.tx_utils import sign_tx
from pycoin.ui import standard_tx_out_script
from pywallet.wallet import create_wallet

from .base import NotEnoughAmountError, BaseProxy


class BitcoinGenericProxy(BaseProxy):

    def __init__(self):
        SelectParams(self.NETWORK)

    def get_data(self, method, *params):
        return {
            'version': '1.1',
            'method': method,
            'params': list(params),
            'id': self.NETWORK
        }

    async def post(self, *args):
        async with ClientSession() as session:
            async with session.post(
                self.URL,
                json=self.get_data(*args),
            ) as res:
                resp_dict = await res.json()
                return resp_dict['result']

    async def create_wallet(self):
        wallet = create_wallet(self.NET_WALLET)
        addr = wallet['address']
        await self.post('importaddress', addr, '', False)
        return addr, wallet['wif']

    async def create_wallet_with_initial_balance(self):
        wallet = create_wallet(self.NET_WALLET)
        addr = wallet['address']
        await self.post('importaddress', addr, '', False)
        await self.post('sendtoaddress', addr, 10)
        await self.post('generate', 1)
        return addr, wallet['wif']

    async def get_listunspent_for_addr(self, addr, confirmations=1):
        res = await self.post('listunspent', confirmations, 9999999, [addr])
        for unspent in res:
            coutpoint = COutPoint(lx(unspent['txid']), unspent['vout'])
            cscript = CScript(unhexlify(unspent['scriptPubKey']))
            unspent['outpoint'] = coutpoint
            unspent['address'] = CBitcoinAddress(unspent['address'])
            unspent['scriptPubKey'] = cscript
            unspent['amount'] = int(unspent['amount'] * COIN)
        return res

    async def get_spendable_list_for_addr(self, addr: str) -> List[Spendable]:
        unspent_list = await self.get_listunspent_for_addr(addr)
        return [
            Spendable(
                unspent['amount'],
                bytes(unspent['scriptPubKey']),
                unspent['outpoint'].hash,
                unspent['outpoint'].n,
            )
            for unspent in unspent_list
        ]

    async def get_balance(self, addr):
        unspent_list = await self.get_listunspent_for_addr(addr)
        return D(sum(unspent['amount'] for unspent in unspent_list)) / COIN

    def calc_fee(self, tx: Tx) -> D:
        raise NotImplementedError

    @classmethod
    def calculate_tx_size(cls, tx: Tx) -> int:
        s = io.BytesIO()
        tx.stream(s)
        return len(s.getvalue())

    async def create_and_sign_transaction(
        self,
        priv: str,
        addrs: List[Tuple[str, D]],
    ) -> str:
        """
        We distribute fee equaly on every recipient by reducing the amount
        of money they will receive. The rest will go back to the sender
        as a change.

        :param priv: WIF private key of sender -> str
        :param addrs: list of tuples -> [(addr1, amount1), (addr2, amount2),..]
        :return: transaction id -> str
        """
        addr = Key.from_text(priv).address()

        spendables = await self.get_spendable_list_for_addr(addr)
        addrs.append((addr, D(0)))

        txs_out = []
        for payable in addrs:
            bitcoin_address, coin_value = payable
            coin_value *= COIN
            script = standard_tx_out_script(bitcoin_address)
            txs_out.append(TxOut(coin_value, script))

        txs_in = [spendable.tx_in() for spendable in spendables]
        tx = Tx(version=1, txs_in=txs_in, txs_out=txs_out, lock_time=0)

        tx.set_unspents(spendables)

        fee = await self.calc_fee(tx)

        fee_per_tx_out, extra_count = divmod(fee, len(tx.txs_out) - 1)

        total_coin_value = sum(
            spendable.coin_value
            for spendable in tx.unspents
        )
        coins_allocated = sum(tx_out.coin_value for tx_out in tx.txs_out)

        if coins_allocated > total_coin_value:
            raise NotEnoughAmountError()

        for tx_out in tx.txs_out:
            if tx_out.address(netcode=self.NETCODE) == addr:
                tx_out.coin_value = total_coin_value - coins_allocated
            else:
                tx_out.coin_value -= fee_per_tx_out
                if extra_count > 0:
                    tx_out.coin_value -= 1
                    extra_count -= 1
                if tx_out.coin_value < 1:
                    raise NotEnoughAmountError()

        sign_tx(tx, wifs=[priv])

        return await self.post('sendrawtransaction', tx.as_hex())

    async def send_money(self, priv, addrs):
        return await self.create_and_sign_transaction(priv, addrs)