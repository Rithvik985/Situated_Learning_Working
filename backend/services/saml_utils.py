import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
import zlib
import base64
import logging
# Load environment variables
load_dotenv()

# Environment variables
ASSERTION_CONSUMER_SERVICE_URL = os.getenv("ASSERTION_CONSUMER_SERVICE_URL")
ISSUER_URL = os.getenv("ISSUER_URL")
Destination = os.getenv("Destination")


def create_authn_request():
    issue_instant = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    request_id = f"_{uuid.uuid4().hex}"

    authn_request = f'''
        <samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
            AssertionConsumerServiceURL="{ASSERTION_CONSUMER_SERVICE_URL}"
            Destination="{Destination}"
            ID="{request_id}"
            IssueInstant="{issue_instant}"
            ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Version="2.0">
            <saml:Issuer xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
                {ISSUER_URL}
            </saml:Issuer>
            <samlp:NameIDPolicy AllowCreate="1"/>
        </samlp:AuthnRequest>
    '''
    return authn_request.strip()

def compress_and_encode_request(authn_request):
    compressor = zlib.compressobj(wbits=-15)
    deflated_request = compressor.compress(authn_request.encode('utf-8')) + compressor.flush()
    encoded_request = base64.b64encode(deflated_request).decode('utf-8')
    return encoded_request

