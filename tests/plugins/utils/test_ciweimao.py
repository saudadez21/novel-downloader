from novel_downloader.plugins.utils.ciweimao.my_encryt import my_decrypt

ENCRYT_KEYS = [
    "riZBIkTTqO/MI67HGtMvVGHjCiZPMLXfThf+LsWaUHE=",
    "ql9CFN+tDexJHll3Kjlem5XpcLCQxYllQrKHMBLJQ7k=",
    "QxGGott+d9Ke+ck//BPfwXg55iS7PkLd+xGqVk0syng=",
    "7B/+0MXVlwSk3RDuRM6T3r0EgMQI3talsZ2UaB/A154=",
    "WV8/NSS/07urnni28UIB4bLqnErOYk2lAYDGPB9lSLA=",
    "e8U/zJNJunRRUmspX5tldfkCBsd3sIN0BSFyOGxtzgo=",
    "mBHtIpOEtk2bg0zoEEl92gJHxUYHVV6BH+ql/pTDShE=",
    "miY1TTGhfdtJOyza/oLqHavL7mFKOLxAx0njXxuae+Q=",
    "bu5PE6GBsGjJ331QASVEUBibVTFsVPU/30JfZo28qII=",
    "eTuY6rqIkk2vdQRbYYxpB+nnU77NoKqZVPo6/PSCcuA=",
    "v2fgzxiWqrvNWAteYVc+uIEBdNzwITpoWkA17+IcJeo=",
    "HDFndE/n28XjrOT9tAxbpBRPgEn5tFdWgwgWwWbCpDQ=",
    "TRxmY5Lu2PdjV6pR9gFX8wxvelnsYybRUOCP8cVrFFg=",
    "h9tKijenuMvf/j8YpjUZ/GgzoTrFaD5duaoU1wIxf0k=",
    "f/s9wn5LaTFphQU/HveVcejv98r1w+Usduhc95/WlQ4=",
    "/gjYBJ9pDgeYA51Gn0ulLcaPttnBNnDUmkL1h4D7esw=",
]

ACCESS_KEY = "DBdVnJEO79qk2rX2"
CONTENT = (
    "LTQ5U0aAAYTHUo3xPUk9ZmAxhz88oN2+5jEN/tLGBFCBG7hDr/d/0UNdMZ4g8CGG9sn1/"
    "5HmMaIATVBwuSb6qRVZBQNMUdkonUs0mxIkP9vsoaec0FFKpzXBYTWJ4sa9a4nnTgDYzhfDI7n7Zqtrvg=="
)
TARGET = "Xtah6wRVV3zlRHI9FwScGVmWURLMmL1j"


def test_my_decrypt_real_case():
    result = my_decrypt(CONTENT, ENCRYT_KEYS, ACCESS_KEY)
    assert result == TARGET
