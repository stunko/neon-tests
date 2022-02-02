import typing as tp
from decimal import Decimal

import web3
import web3.types
import requests
import eth_account.signers.local


class NeonWeb3Client:
    def __init__(self, proxy_url: str, chain_id: int):
        self._proxy_url = proxy_url
        self._web3 = web3.Web3(web3.HTTPProvider(proxy_url))
        self._chain_id = chain_id

    def __getattr__(self, item):
        return getattr(self._web3, item)

    def get_proxy_version(self):
        return requests.get(self._proxy_url, json={"jsonrpc": "2.0", "method": "neon_proxy_version", "params": [], "id": 0}).json()

    def get_cli_version(self):
        return requests.get(self._proxy_url, json={"jsonrpc": "2.0", "method": "neon_cli_version", "params": [], "id": 0}).json()

    def get_evm_version(self):
        return requests.get(self._proxy_url,
                            json={"jsonrpc": "2.0", "method": "web3_clientVersion", "params": [], "id": 0}).json()

    def gas_price(self):
        # TODO: Change this when we will use gasPrice value in proxy for calculations
        return 1000000000

    def create_account(self):
        return self._web3.eth.account.create()

    def get_balance(self, address: tp.Union[str, eth_account.signers.local.LocalAccount]):
        if not isinstance(address, str):
            address = address.address
        return web3.Web3.fromWei(self._web3.eth.get_balance(address), "ether")

    def send_neon(
        self,
        from_: eth_account.signers.local.LocalAccount,
        to: tp.Union[str, eth_account.signers.local.LocalAccount],
        amount: tp.Union[int, float, Decimal],
        gas: int = 21000,
        gas_price: tp.Optional[int] = None,
    ) -> web3.types.TxReceipt:
        to_addr = to if isinstance(to, str) else to.address
        gas_price = gas_price or self.gas_price()
        transaction = {
            "to": to_addr,
            "value": web3.Web3.toWei(amount, "ether"),
            "chainId": self._chain_id,
            "gasPrice": gas_price or self.gas_price(),
            "gas": gas,
            "nonce": self._web3.eth.get_transaction_count(from_.address),
        }

        signed_tx = self._web3.eth.account.sign_transaction(transaction, from_.key)
        tx = self._web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self._web3.eth.wait_for_transaction_receipt(tx)

    def deploy_contract(
        self,
        from_: eth_account.signers.local.LocalAccount,
        abi,
        bytecode: str,
        gas: int = 100000000,
        gas_price: tp.Optional[int] = None,
        constructor_args: tp.List = [],
    ):
        """Proxy doesn't support send_transaction"""
        gas_price = gas_price or self.gas_price()
        contract = self._web3.eth.contract(abi=abi, bytecode=bytecode)
        trans = contract.constructor(*constructor_args).buildTransaction(
            {
                "chainId": self._chain_id,
                "gas": gas,
                "gasPrice": gas_price,
                "nonce": self._web3.eth.get_transaction_count(from_.address),
            }
        )
        signed_tx = self._web3.eth.account.sign_transaction(trans, from_.key)
        tx = self._web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self._web3.eth.wait_for_transaction_receipt(tx)

    def send_erc20(
        self,
        from_: eth_account.signers.local.LocalAccount,
        to: tp.Union[str, eth_account.signers.local.LocalAccount],
        amount: tp.Union[int, float, Decimal],
        address: str,
        abi,
        gas: int = 100000000,
        gas_price: tp.Optional[int] = None,
    ):
        to_addr = to if isinstance(to, str) else to.address
        gas_price = gas_price or self.gas_price()
        contract = self._web3.eth.contract(address=address, abi=abi)
        trans = contract.functions.transfer(to_addr, amount).buildTransaction(
            {
                "chainId": self._chain_id,
                "gas": gas,
                "gasPrice": gas_price,
                "nonce": self._web3.eth.get_transaction_count(from_.address),
                "from": from_.address,
            }
        )
        signed_tx = self._web3.eth.account.sign_transaction(trans, from_.key)
        tx = self._web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self._web3.eth.wait_for_transaction_receipt(tx)