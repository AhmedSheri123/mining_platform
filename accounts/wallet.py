from tronpy import Tron
from tronpy.providers import HTTPProvider
from tronpy.keys import PrivateKey
import requests
from tronpy.exceptions import AddressNotFound

API_KEY = "5662225a-0098-455b-9df9-ef3dbaa1f8e4"

master_address = "TV1vV9eu2FEXf2QmCV7ivE7drj9cBYwqEf"
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
# ربط مع شبكة TRON الرئيسية (Mainnet)
client = Tron(provider=HTTPProvider(
    api_key=API_KEY, 
    endpoint_uri="https://api.trongrid.io"
))
contract = client.get_contract(USDT_CONTRACT)

def wallet_gen():
    # إنشاء محفظة جديدة (خاصة بالمستخدم)
    wallet = client.generate_address()
    print(wallet)
    context = {
        "address":wallet['base58check_address'],
        "private_key":wallet['private_key']
        }
    return context


def get_usdt_balance(address):
    url = f"https://api.trongrid.io/v1/accounts/{address}"
    response = requests.get(url).json()
    usdt_balance = 0

    # البحث ضمن TRC20 tokens في الاستجابة
    for token in response.get("trc20", []):
        if token.get("token_address") == "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj":
            usdt_balance = int(token.get("balance")) / 10**6  # USDT عادة 6 أرقام عشرية
            break

    return usdt_balance


def transfer_to_master(wallet):
    priv_key_obj = PrivateKey(bytes.fromhex(wallet.private_key))  # تحويل النص إلى كائن PrivateKey
    addr = wallet.address
    trx_balance = client.get_account_balance(wallet.address)
    if trx_balance == 0:
        print("المحفظة لا تحتوي على TRX لتغطية رسوم التحويل")
        
    txn = (
        contract.functions.transfer(master_address, int(wallet.balance * 10**6))
        .with_owner(addr)
        .fee_limit(5_000_000)
        .build()
        .sign(priv_key_obj)
    )
    result = txn.broadcast().wait()
    return result


def get_trx_balance(address: str) -> float:
    """
    تُرجع رصيد TRX لمحفظة معينة.
    إذا كانت المحفظة غير موجودة على البلوكشين، تُرجع 0.
    
    :param address: عنوان المحفظة (Base58)
    :return: الرصيد بوحدة TRX
    """
    try:
        balance = client.get_account_balance(address)
        return balance
    except AddressNotFound:
        # المحفظة غير موجودة على البلوكشين
        return 0.0
    except Exception as e:
        print(f"حدث خطأ أثناء جلب الرصيد: {e}")
        return False