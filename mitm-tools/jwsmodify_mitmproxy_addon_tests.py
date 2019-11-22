import unittest

import const
import json
import jwsmodify_mitmproxy_addon as jma

class TestJWSModifyMethods(unittest.TestCase):

    def test_can_find_raw_jws(self):
        self.assertTrue(jma.extract_jws_payload(const.RAW_JWS) is not None)
    
    def test_can_find_jws_in_json(self):
        my_obj = {
            'jws': str(const.RAW_JWS, 'utf-8'),
            'foo': 'bar',
            'baz': 2,
        }
        my_obj_str = json.dumps(my_obj)
        print(my_obj_str)
        self.assertTrue(jma.extract_jws_payload(my_obj_str) is not None)



if __name__ == '__main__':
    unittest.main()
