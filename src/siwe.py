import datetime
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

def create_siwe_message(address: str, nonce: str, domain: str = "hub.coconnect.co", statement: str = "Sign in to CoConnect Hub", chain_id: int = 1) -> str:
    """
    Menghasilkan SIWE (Sign-In with Ethereum) message EIP-4361
    yang 100% kompatibel dengan viem di frontend CoConnect Hub.
    """
    checksummed = Web3.to_checksum_address(address)
    now = datetime.datetime.now(datetime.timezone.utc)
    issued_at = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    exp = now + datetime.timedelta(minutes=5)
    exp_at = exp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    uri = f"https://{domain}/auth"

    msg = (
        f"{domain} wants you to sign in with your Ethereum account:\n"
        f"{checksummed}\n\n"
        f"{statement}\n\n"
        f"URI: {uri}\n"
        f"Version: 1\n"
        f"Chain ID: {chain_id}\n"
        f"Nonce: {nonce}\n"
        f"Issued At: {issued_at}\n"
        f"Expiration Time: {exp_at}"
    )
    return msg

def sign_siwe_message(message: str, private_key: str) -> str:
    """
    Menandatangani pesan SIWE secara lokal menggunakan EIP-191 personal_sign.
    """
    if not private_key.startswith("0x"):
        private_key = "0x" + private_key
    
    encoded = encode_defunct(text=message)
    signed = Account.sign_message(encoded, private_key=private_key)
    sig_hex = signed.signature.hex()
    if not sig_hex.startswith("0x"):
        sig_hex = "0x" + sig_hex
    return sig_hex
