import allure
import pytest
import typing as tp

from integration.tests.basic.helpers.assert_message import AssertMessage
from integration.tests.basic.helpers.basic import BaseMixin
from integration.tests.basic.helpers.rpc_request_factory import RpcRequestFactory
from integration.tests.basic.helpers.rpc_request_params_factory import RpcRequestParamsFactory
from integration.tests.basic.model import model as request_models
from integration.tests.basic.model.tags import Tag
from integration.tests.basic.test_data.input_data import InputData

"""
12.	Verify implemented rpc calls work
12.1.	eth_getBlockByHash		
12.2.	eth_getBlockByNumber		
12.11.	eth_blockNumber		
12.12.	eth_call		
12.13.	eth_estimateGas		
12.14.	eth_gasPrice		
12.22.	eth_getLogs		
12.30.	eth_getBalance		
12.32.	eth_getTransactionCount		
12.33.	eth_getCode		
12.35.	eth_sendRawTransaction		
12.36.	eth_getTransactionByHash		
12.39.	eth_getTransactionReceipt		
12.40.	eht_getStorageAt		
12.61.	web3_clientVersion		
12.63.	net_version
"""

GET_LOGS_TEST_DATA = [
    (Tag.LATEST.value, Tag.LATEST.value),
    (Tag.EARLIEST.value, Tag.LATEST.value),
    (Tag.PENDING.value, Tag.LATEST.value),
    (Tag.LATEST.value, Tag.EARLIEST.value),
    (Tag.LATEST.value, Tag.PENDING.value),
]

# TODO: fix earliest and penging if possible
TAGS_TEST_DATA = [
    (Tag.EARLIEST, True),
    (Tag.EARLIEST, False),
    (Tag.LATEST, True),
    (Tag.LATEST, False),
    (Tag.PENDING, True),
    (Tag.PENDING, False),
]


@allure.story("Basic: Json-RPC call tests")
class TestRpcCalls(BaseMixin):
    @staticmethod
    def is_hex(hex_data: str) -> bool:
        try:
            int(hex_data, 16)
            return True
        except (ValueError, TypeError):
            return False

    def assert_rpc_response(
        self,
        method: str,
        params: tp.Optional[tp.Any] = None,
        err_message: str = "",
        raises: bool = False,
    ) -> tp.Union[request_models.JsonRpcResponse, request_models.JsonRpcErrorResponse]:
        """Verify eth endpoints responses"""
        if not isinstance(params, tp.List):
            params = [params]
        payloads = getattr(RpcRequestFactory(), method)(*params)
        print(f"payloads: {payloads}")
        response = self.json_rpc_client.do_call(payloads)
        print(f"response: {response}")
        if raises:
            if err_message and not isinstance(err_message, str):
                err_message = err_message.value
            self.assert_expected_raises(response, err_message)
        else:
            assert isinstance(
                response, request_models.JsonRpcResponse
            ), f"rpc call is failed: {response.error.get('message')}"
            assert response.id == payloads.id, AssertMessage.WRONG_ID.value
        return response

    @pytest.mark.parametrize(
        "params, raises",
        [({"to": None, "data": None}, False), ({}, True)],
    )
    def test_eth_call(self, params, raises):
        """Verify implemented rpc calls work eth_call"""
        if params:
            params.update({"to": self.recipient_account.address, "data": hex(pow(10, 14))})
        request_data = [request_models.CallRequest(**params), Tag.LATEST.value]
        response = self.assert_rpc_response("eth_call", params=request_data, raises=raises)
        if params:
            assert response.result == "0x", f"Invalid response result, `{response.result}`"

    @pytest.mark.parametrize(
        "params, raises",
        [({"from": None, "to": None, "value": hex(1)}, False), ({}, True)],
    )
    def test_eth_estimate_gas(self, params, raises):
        """Verify implemented rpc calls work eth_estimateGas"""
        if params:
            params.update({"from": self.sender_account.address, "to": self.recipient_account.address})
        response = self.assert_rpc_response("eth_estimateGas", params=params, raises=raises)
        if params:
            assert self.is_hex(response.result)

    def test_eth_gas_price(self):
        """Verify implemented rpc calls work eth_gasPrice"""
        payloads = RpcRequestFactory.get_gas_price(params=[])
        actual_result = self.json_rpc_client.do_call(payloads)

        assert actual_result.id == payloads.id, AssertMessage.WRONG_ID.value
        assert self.assert_is_successful_response(actual_result), AssertMessage.WRONG_TYPE.value
        assert "0x" in actual_result.result, AssertMessage.DOES_NOT_START_WITH_0X.value

    @pytest.mark.parametrize("from_block,to_block", GET_LOGS_TEST_DATA)
    def test_eth_get_logs_via_tags(self, from_block: Tag, to_block: Tag):
        """Verify implemented rpc calls work eth_getLogs"""
        # TODO: use contract instead of account
        sender_account = self.create_account_with_balance()
        params = [
            request_models.GetLogsRequest(from_block=from_block, to_block=to_block, address=sender_account.address)
        ]
        payloads = RpcRequestFactory.get_logs(params=params)

        actual_result = self.json_rpc_client.do_call(payloads)

        assert actual_result.id == payloads.id, AssertMessage.WRONG_ID.value
        assert self.assert_no_error_object(actual_result), AssertMessage.CONTAINS_ERROR
        assert self.assert_result_object(actual_result), AssertMessage.DOES_NOT_CONTAIN_RESULT

    def test_eth_get_logs_via_numbers(self):
        """Verify implemented rpc calls work eth_getLogs"""
        # TODO: use contract instead of account
        sender_account = self.create_account_with_balance()
        # TOOD: variants
        params = [
            request_models.GetLogsRequest(from_block=1, to_block=Tag.LATEST.value, address=sender_account.address)
        ]
        payloads = RpcRequestFactory.get_logs(params=params)

        actual_result = self.json_rpc_client.do_call(payloads)

        assert actual_result.id == payloads.id, AssertMessage.WRONG_ID.value
        assert self.assert_no_error_object(actual_result), AssertMessage.CONTAINS_ERROR
        assert self.assert_result_object(actual_result), AssertMessage.DOES_NOT_CONTAIN_RESULT

    @pytest.mark.only_stands
    def test_eth_get_balance(self):
        """Verify implemented rpc calls work eth_getBalance"""
        sender_account = self.create_account_with_balance()

        params = [sender_account.address, Tag.LATEST.value]
        payloads = RpcRequestFactory.get_balance(params=params)
        actual_result = self.json_rpc_client.do_call(payloads)

        assert actual_result.id == payloads.id, AssertMessage.WRONG_ID.value
        assert actual_result.result == InputData.FIRST_AMOUNT_IN_RESPONSE.value, AssertMessage.WRONG_AMOUNT.value

    def test_eth_get_code(self):
        """Verify implemented rpc calls work eth_getCode"""
        # TODO: use contract instead of account?
        sender_account = self.create_account_with_balance()

        params = [sender_account.address, Tag.LATEST.value]
        payloads = RpcRequestFactory.get_code(params=params)
        actual_result = self.json_rpc_client.do_call(payloads)

        assert actual_result.id == payloads.id, AssertMessage.WRONG_ID.value
        assert self.assert_no_error_object(actual_result), AssertMessage.CONTAINS_ERROR
        assert self.assert_result_object(actual_result), AssertMessage.DOES_NOT_CONTAIN_RESULT

    def test_web3_client_version(self):
        """Verify implemented rpc calls work web3_clientVersion"""
        payloads = RpcRequestFactory.get_web3_client_version(params=[])
        actual_result = self.json_rpc_client.do_call(payloads)

        assert actual_result.id == payloads.id, AssertMessage.WRONG_ID.value
        assert self.assert_is_successful_response(actual_result), AssertMessage.WRONG_TYPE.value
        assert "Neon" in actual_result.result, "version does not contain 'Neon'"

    def test_net_version(self):
        """Verify implemented rpc calls work work net_version"""
        payloads = RpcRequestFactory.get_net_version(params=[])
        actual_result = self.json_rpc_client.do_call(payloads)

        assert actual_result.id == payloads.id, AssertMessage.WRONG_ID.value
        assert self.assert_is_successful_response(actual_result), AssertMessage.WRONG_TYPE.value
        assert actual_result.result == str(
            self.web3_client._chain_id
        ), f"net version is not {self.web3_client._chain_id}"

    def test_eth_get_block_by_hash(self):
        """Verify implemented rpc calls work eth_getBlockByHash"""

        tx_receipt = self.transfer_neon(self.sender_account, self.recipient_account, InputData.SAMPLE_AMOUNT.value)

        params = [tx_receipt.blockHash.hex(), True]
        payloads = RpcRequestFactory.get_block_by_hash(params=params)

        actual_result = self.json_rpc_client.do_call(payloads, request_models.BlockResponse)

        assert actual_result.id == payloads.id, AssertMessage.WRONG_ID.value
        assert self.assert_no_error_object(actual_result), AssertMessage.CONTAINS_ERROR
        assert self.assert_result_object(actual_result), AssertMessage.DOES_NOT_CONTAIN_RESULT

    @pytest.mark.parametrize("quantity_tag,full_trx", TAGS_TEST_DATA)
    def test_eth_get_blockn_by_umber_via_tags(self, quantity_tag: tp.Union[int, Tag], full_trx: bool):
        """Verify implemented rpc calls work eth_getBlockByNumber"""
        params = RpcRequestParamsFactory.get_block_by_number(quantity_tag, full_trx)
        payloads = RpcRequestFactory.get_block_by_number(params=params)

        actual_result = self.json_rpc_client.do_call(payloads, request_models.BlockResponse)
        assert actual_result.id == payloads.id, AssertMessage.WRONG_ID.value

    def test_eth_get_block_by_number_via_numbers(self):
        """Verify implemented rpc calls work eth_getBlockByNumber"""

        tx_receipt = self.transfer_neon(self.sender_account, self.recipient_account, InputData.SAMPLE_AMOUNT.value)

        params = RpcRequestParamsFactory.get_block_by_number(tx_receipt.blockNumber, True)
        payloads = RpcRequestFactory.get_block_by_number(params=params)

        actual_result = self.json_rpc_client.do_call(payloads, request_models.BlockResponse)
        assert actual_result.id == payloads.id, AssertMessage.WRONG_ID.value
        assert self.assert_no_error_object(actual_result), AssertMessage.CONTAINS_ERROR
        assert self.assert_result_object(actual_result), AssertMessage.DOES_NOT_CONTAIN_RESULT

    def test_eth_block_number(self):
        """Verify implemented rpc calls work work eth_blockNumber"""
        payloads = RpcRequestFactory.get_block_number(params=[])
        actual_result = self.json_rpc_client.do_call(payloads)

        assert actual_result.id == payloads.id, AssertMessage.WRONG_ID.value
        assert self.assert_is_successful_response(actual_result), AssertMessage.WRONG_TYPE.value
        assert "0x" in actual_result.result, AssertMessage.DOES_NOT_START_WITH_0X.value

    @pytest.mark.parametrize("params, raises", [(["latest"], False), ([], True)])
    def test_eth_get_storage_at(self, params, raises):
        """Verify implemented rpc calls work eht_getStorageAt"""
        if params:
            params = [self.sender_account.address, hex(1)] + params
        response = self.assert_rpc_response(method="eth_getStorageAt", params=params, raises=raises)
        if params:
            assert self.is_hex(response.result), f"Invalid response: {response.result}"

    @pytest.mark.parametrize("params, raises", [(None, False), ("param", True)])
    def test_eth_mining(self, params, raises):
        """Verify implemented rpc calls work eth_mining"""
        self.assert_rpc_response(method="eth_mining", params=params, raises=raises)

    @pytest.mark.parametrize("params, raises", [(None, False), ("param", True)])
    def test_eth_syncing(self, params, raises):
        """Verify implemented rpc calls work eth_syncing"""
        response = self.assert_rpc_response(method="eth_syncing", params=params, raises=raises)
        if not params:
            assert all(
                isinstance(block, int) for block in response.result.values()
            ), f"Invalid response: {response.result}"

    @pytest.mark.parametrize("params, raises", [(None, False), ("param", True)])
    def test_net_peer_count(self, params, raises):
        """Verify implemented rpc calls work net_peerCount"""
        response = self.assert_rpc_response(method="net_peerCount", params=params, raises=raises)
        if not params:
            assert self.is_hex(response.result), f"Invalid response: {response.result}"

    @pytest.mark.parametrize(
        "params, raises",
        [("0x6865", False), ("param", True), (None, True)],
    )
    def test_web3_sha3(self, params, raises):
        """Verify implemented rpc calls work web3_sha3"""
        response = self.assert_rpc_response(method="web3_sha3", params=params, raises=raises)
        if self.is_hex(params):
            assert response.result.startswith("e5105")
