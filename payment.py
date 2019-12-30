import requests


class PaystackPay(object):
    """
     Paystack functions
    """
    def __init__(self):
        self.authorization_url = 'https://api.paystack.co/transaction/initialize'
        self.trans_verification_url = 'https://api.paystack.co/transaction/verify/{}'
        self.bvn_verification_url = 'https://api.paystack.co/bank/resolve_bvn/{}'

    def fetch_authorization_url(self, email, amount):
        response = requests.post(self.authorization_url, json={'email': email, 'amount': int(amount*100)},
                                 headers={'Authorization': 'Bearer sk_test_3f33d1a7e198c4ca0af6b19b90f9c26e0c79ddbe'})
        return response

    def verify_reference_transaction(self, reference):
        response = requests.get(self.trans_verification_url.format(reference), headers={
            'Authorization': 'Bearer sk_test_3f33d1a7e198c4ca0af6b19b90f9c26e0c79ddbe'})

        return response
