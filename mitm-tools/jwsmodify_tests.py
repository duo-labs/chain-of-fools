import unittest

import const
import jwsmodify

class TestJWSModifyMethods(unittest.TestCase):

    def test_decode_raw(self):
        header, payload, signature = jwsmodify.decode_jws_parts(const.RAW_JWS)
    
    def test_header_parse(self):
        header_raw, _, _ = jwsmodify.decode_jws_parts(const.RAW_JWS)
        header = jwsmodify.parse_jws_header(header_raw)
        self.assertTrue('alg' in header and header['alg'] == 'RS256')
        self.assertTrue('x5c' in header)

if __name__ == '__main__':
    unittest.main()
