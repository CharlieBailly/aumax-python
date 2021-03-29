from datetime import datetime
import hmac
import requests
import hashlib
import base64
import time


def printResponse(r: requests.models.Response) -> None:
    """
    Print a response from an http request to the console, it prints status code, headers, and body as a JSON dictionnary

    :param r: The response to print
    :type r: requests.models.Response
    """
    print(f"Response : {r}")
    print()
    print("Headers :")
    print(r.headers)
    print()
    print("Content :")
    print(r.json())


def addPaddingToBase64String(base64String: str) -> str:
    """
    Return a padded version of a base64String that is not long enough to be decoded by base64.b64decode()

    :param base64String: The base64String that is not long enough to be decoded by base64.b64decode()
    :type base64String: str
    :return: base64String padded with "=" so it can be decoded by base64.b64decode()
    :rtype: str
    """
    return base64String + '=' * (-len(base64String) % 4)  # Padding with "="


def hashMCode(mCode: str) -> str:
    """
    Function to hash the mCode

    :param mCode: mCode is the 6 digits code you set to protect sensible actions such as creating a virtual credit card
    :type mCode: str
    :return: The base32 string in lowercase of the SHA-256 of the UTF-8 bytes of the mCode
    :rtype: str
    """
    res = mCode.encode('utf-8')
    res = hashlib.sha256(res).digest()
    return base64.b32encode(res).decode('utf-8').lower()


def getHmacKeyFromSeedDevice(seedDevice: str, mCode: str, otherBytes: bytes) -> bytes:
    """
    Generate the Hmac key (needed to hash with a password) using the seedDevice and the mCode

    :param seedDevice: seedDevice is the code you receive by SMS when adding your phone as "the trusted phone" (the last one if you received severals)
    :type seedDevice: str
    :param mCode: mCode is the 6 digits code you set to protect sensible actions such as creating a virtual credit card
    :type mCode: str
    :param otherBytes: Just bytes that are appended at the end of the result
    :type otherBytes: bytes
    :return: A Hmax key made of the bytes of the hash of the mCode using hashMcode function(uppered and then decoded in base32), concatained with the bytes of the seedDevice(uppered and then decoded in base32), concatained with otherBytes
    :rtype: bytes
    """
    mCodeHashed = hashMCode(mCode)
    res = bytearray(base64.b32decode(mCodeHashed.upper().encode('utf-8')))
    for byt in bytearray(base64.b32decode(seedDevice.upper().encode('utf-8'))):
        res.append(byt)
    if otherBytes is None:
        return res

    # If otherBytes are not bytes but string, we convert them in bytes using base32
    if type(otherBytes) is str:
        otherBytes = base64.b32decode(otherBytes.upper())

    for byt in bytearray(otherBytes):
        res.append(byt)

    return res


def hMacSHA256(key: bytes, msg: bytes) -> bytes:
    """
    Hash a message using HMAC-SHA256 using a key

    :param key: The key used in the HMAC-SHA256 function(generated by getHmacKeyFromSeedDevice for example)
    :type key: bytes
    :param msg: The message you want to hash using HMAC-SHA256
    :type msg: bytes
    :return: The hash of the message using a key with the HMAC-SHA256 algorithm
    :rtype: bytes
    """
    return hmac.new(key, msg, digestmod=hashlib.sha256).digest()


def hMacSHA1(key: bytes, msg: bytes) -> bytes:
    """
    Hash a message using HMAC-SHA1 using a key

    :param key: The key used in the HMAC-SHA1 function(generated by getHmacKeyFromSeedDevice for example)
    :type key: bytes
    :param msg: The message you want to hash using HMAC-SHA1
    :type msg: bytes
    :return: The hash of the message using a key with the HMAC-SHA1 algorithm
    :rtype: bytes
    """
    return hmac.new(key, msg, digestmod=hashlib.sha1).digest()


def signOperation(key: bytes, msg: bytes) -> bytes:
    """
    Sign an operation (operation = creation of a virtual credit card) generated by the generateOperation(then encoded in utf-8) using a key (generated by the getHmacKeyFromSeedDevice function)

    :param key: The key to use in the HMAC-SHA256 algorithm
    :type key: bytes
    :param msg: The UTF8 bytes of the operation you want to sign
    :type msg: bytes
    :return: The base64 bytes of the HMAC-SHA256 of the operation using the key
    :rtype: bytes
    """
    return base64.b64encode(hMacSHA256(key, msg))


def getHMACSHA1AuthCode(seedDevice: str, mCode: str, encodedOperationDict: bytes) -> bytes:
    """
    Generate the bytes of the digest of the operation (operation = creation of a virtual credit card)

    :param seedDevice: seedDevice is the code you receive by SMS when adding your phone as "the trusted phone" (the last one if you received severals)
    :type seedDevice: str
    :param mCode: mCode is the 6 digits code you set to protect sensible actions such as creating a virtual credit card
    :type mCode: str
    :param encodedOperationDict: The UTF8 bytes of the operation you want to digest
    :type encodedOperationDict: bytes
    :return: The UTF8 bytes of the digest of an operation
    :rtype: bytes
    """
    key = getHmacKeyFromSeedDevice(seedDevice, mCode, None)
    return signOperation(key, encodedOperationDict)


def generateOperation(length: int, amount: float) -> str:
    """
    Generate an operation (operation = creation of a virtual credit card)

    :param length: The duration of the virtual credit card in months
    :type length: int
    :param amount: The amount in Euros contained in the virtual credit card
    :type amount: float
    :return: A string describing the virtual credit card / the operation
    :rtype: str
    """
    return ("{\"duree\":" + str(length) +
            ",\"mntSaisi\":" + str(amount) + "}")


def generateDigest(seedDevice: str, mCode: str, length: int, amount: float) -> str:
    """
    Generate the string of the digest of the credit card

    :param seedDevice: seedDevice is the code you receive by SMS when adding your phone as "the trusted phone" (the last one if you received severals)
    :type seedDevice: str
    :param mCode: mCode is the 6 digits code you set to protect sensible actions such as creating a virtual credit card
    :type mCode: str
    :param length: The duration of the virtual credit card in months
    :type length: int
    :param amount: The amount in Euros contained in the virtual credit card
    :type amount: float
    :return: The string of the digest of the operation (needed in the request to generate a virtual credit card)
    :rtype: str
    """
    encodedOperation = generateOperation(length, amount).encode('utf-8')
    return getHMACSHA1AuthCode(seedDevice, mCode, encodedOperation).decode('utf-8')


def current_milli_time() -> int:
    """
    Simulate Java.lang.System.currentTimeMillis() Method 

    :return: The current time in milliseconds
    :rtype: int
    """
    return round(time.time() * 1000)


def hexStr2Bytes(hexStr: str) -> bytes:
    """
    Convert an hexadecimal string in bytes

    :param hexStr: The hexadecimal string
    :type hexStr: str
    :return: The bytes of the hexadecimal string
    :rtype: bytes
    """
    return bytes.fromhex(hexStr)


def generateTOTP(seedDevice: str, mCode: str, seedOperation: str) -> str:
    """
    Generate a Time One Time Password (TOPT) based on the current time

    :param seedDevice: seedDevice is the code you receive by SMS when adding your phone as "the trusted phone" (the last one if you received severals)
    :type seedDevice: str
    :param mCode: mCode is the 6 digits code you set to protect sensible actions such as creating a virtual credit card
    :type mCode: str
    :param seedOperation: seedOperation is a string returned when calling the API (path : /nvsecurityapi/rest/enrollments/operation/generateSeed)
    :type seedOperation: str
    :return: A Time One Time Password (TOPT) based on the current time needed to generate a virtual credit card
    :rtype: str
    """

    seedOperationBytes = base64.b32decode(seedOperation.upper())
    key = getHmacKeyFromSeedDevice(seedDevice, mCode, seedOperationBytes)

    j = -1
    currentTimeMilli = (current_milli_time() // 1000) - j
    timeInHex = hex((currentTimeMilli) // 30)[2:].upper()
    res = ""
    for i in range(len(timeInHex), 16):
        res += '0'
    res += timeInHex
    resBytes = hexStr2Bytes(res)
    # Now we will HmacSHA1 resBytes using key
    resHmacSHA1 = bytearray(hMacSHA1(key, resBytes))

    DIGITS_POWER = [1, 10, 100, 1000, 10000,
                    100000, 1000000, 10000000, 100000000]
    MAX_VALUE = 127
    CAN = 24

    b = resHmacSHA1[-1] & 15
    i = ((resHmacSHA1[b + 3] & 255) | ((((resHmacSHA1[b] & MAX_VALUE) << CAN) |
                                        ((resHmacSHA1[b + 1] & 255) << 16)) | ((resHmacSHA1[b + 2] & 255) << 8))) % DIGITS_POWER[6]
    final = ""
    for j in range(len(str(i)), 6):
        final += '0'
    final += str(i)

    return final