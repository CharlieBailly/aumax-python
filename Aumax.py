import requests
import json
import datetime
import base64
from utils import generateDigest, generateOperation, generateTOTP, printResponse, addPaddingToBase64String
from consts import BASE_URL, API_KEY, CLIENT_SECRET, BASIC_AUTH_KEY, VERSION
from exceptions import ConnectionError, SensibleOperationsDisabledError


class Aumax():

    def __init__(self, email: str, password: str):
        """
        Create an Aumax object to interact with the Aumax API

        :param email: The email used to connect to your Aumax account
        :type email: str
        :param password: The password used to connect to your Aumax account
        :type password: str
        """
        self.__email = email
        self.__password = password

        # False by default, can be activated using enableSensibleOperations method
        self.__sensibleOperationsEnabled = False
        # False by default, True once you are connected using the connect method
        self.__connected = False

        self.__JwtData = {}  # This will be updated in __extractDataFromJWT method

        self.__initSession()

        # The following will be initialized in the enableSensibleOperations method if needed

        # See ReadMe to know how to get the following values
        self.__deviceName = ""  # Example : "OnePlus 6T"
        self.__deviceVendor = ""  # Example : "OnePlus"
        self.__deviceModel = ""  # Example : "ONEPLUS A6013"
        self.__deviceSerialNumber = ""  # Example : "38aa48613fd1536f"
        self.__deviceId = ""  # Example : "sdm845"
        # seedDevice is the code you receive by SMS when adding your phone as "the trusted phone" (the last one if you received severals)
        self.__seedDevice = ""  # Example : xfu3rbzqb47njp5y
        # mCode is the 6 digits code you set to protect sensible actions such as creating a virtual credit card
        self.__mCode = ""  # Example : 012345

    def __initSession(self) -> None:
        """
        Create a request session and initialize it with basic headers needed for future requests
        """
        self.__s = requests.Session()
        self.__s.headers.update({
            'apikey': API_KEY,
            'client_id': API_KEY,
            'User-Agent': 'okhttp/3.12.1',
        })

    def __setAuthenticationAndAuthorization(self, authentication: str, authorization: str) -> None:
        """
        Method to add some authentication headers that are needed for future requests

        :param authentication: Authentication headers that is in the response of the connection request
        :type authentication: str
        :param authorization: Authorization headers that is in the response of the connection request
        :type authorization: str
        """
        self.__s.headers.update({
            'authentication': f"Bearer {authentication}",
            'authorization': f"Bearer {authorization}",
        })

    def __extractDataFromJWT(self, jwt: str) -> None:
        """
        Extract data contained in the JWT in the response of the connection request

        :param jwt: The JWT (base64 string separated by a '.')
        :type jwt: str
        """
        self.__JwtData = {}
        # Only the two first part of the JWT contains relevant data
        for jsonBase64String in jwt.split('.')[:2]:
            jsonBase64String = addPaddingToBase64String(jsonBase64String)
            jsonStr = base64.b64decode(jsonBase64String).decode('utf-8')
            jsonObj = json.loads(jsonStr)
            self.__JwtData.update(jsonObj)

    def __generateSeed(self, length: int, amount: float) -> str:
        """
        Generate a Seed (a string) based on current time when creating a new virtual credit card

        :param length: The duration of the virtual credit card in months
        :type length: int
        :param amount: The amount in Euros contained in the virtual credit card
        :type amount: float
        :return: The Seed needed to generate a TOTP (Time One Time Password)
        :rtype: str
        """
        if not self.__connected:
            raise ConnectionError
        if not self.__sensibleOperationsEnabled:
            raise SensibleOperationsDisabledError

        op = generateOperation(length, amount)

        headers = {
            'Content-Type': 'application/json',
        }

        data = {
            "operationInfos": {
                "accessInfos": {
                    "accessCode": self.__JwtData["accessCode"],
                    "efs": self.__JwtData["efs"],
                    # Yes oauthToken is the same as accessCode
                    "oauthToken": self.__JwtData["accessCode"],
                    "si": self.__JwtData["si"]
                },
                "device": {
                    "biometryActivation": "N",
                    "model": self.__deviceModel,
                    "serialNumber": self.__deviceSerialNumber,
                    "vendor": self.__deviceVendor
                },
                "digest": generateDigest(self.__seedDevice, self.__mCode, length, amount),
                "encodeOperation": op,
                "secuChannel": "OATH_S",
                # The signature with the private key seems to be useless ( nice, we don't need to extract the private key :) )
                # "signature": "",
            }
        }

        data = json.dumps(data)

        r = self.__s.post(
            f"{BASE_URL}/nvsecurityapi/rest/enrollments/operation/generateSeed", headers=headers, data=data)

        return r.json()["seedOperation"]

    def connect(self) -> bool:
        """
        Method to connect to the Aumax API

        :return: True if the connection was successful, False otherwise
        :rtype: bool
        """

        headers = {
            'authorization': f"Basic {BASIC_AUTH_KEY}",
        }

        data = {
            'username': self.__email,
            'password': self.__password,
            'grant_type': 'password',
            'deviceVendor': self.__deviceVendor,
            'client_id': CLIENT_SECRET,
            'apikey': API_KEY,
            'deviceSerialNumber': self.__deviceSerialNumber,
            'deviceModel': self.__deviceModel,
        }

        r = self.__s.post(
            f"{BASE_URL}/oauth-validate-key-secret/token", headers=headers, data=data)

        if r.status_code != 200:
            printResponse(r)
            return False

        # No errors : we are connected
        headers = r.headers

        authentication = headers.get("Authentication")
        authorization = headers.get("Authorization")
        self.__setAuthenticationAndAuthorization(authentication, authorization)

        self.__extractDataFromJWT(authentication)

        self.__connected = True
        return True

    def enableSensibleOperations(self, deviceName: str, deviceVendor: str, deviceModel: str, deviceSerialNumber: str, deviceId: str, seedDevice: str, mCode: str) -> None:
        """
        Method to enable sensible operations (such as creating a new virtual credit card)
        (See the ReadMe to know how to get the parameters)

        :param deviceName: The name of the device, example : "OnePlus 6T"
        :type deviceName: str
        :param deviceVendor: The vendor of the device, example : "OnePlus"
        :type deviceVendor: str
        :param deviceModel: The model of the device, example : "ONEPLUS A6013"
        :type deviceModel: str
        :param deviceSerialNumber: The device serial number, example : "38aa48613fd1536f"
        :type deviceSerialNumber: str
        :param deviceId: The device Id, example : "sdm845"
        :type deviceId: str
        :param seedDevice: seedDevice is the code you receive by SMS when adding your phone as "the trusted phone" (the last one if you received severals)
        :type seedDevice: str
        :param mCode: mCode is the 6 digits code you set to protect sensible actions such as creating a virtual credit card
        :type mCode: str
        """

        self.__sensibleOperationsEnabled = True

        # See ReadMe to know how to get the following values
        self.__deviceName = deviceName  # Example : "OnePlus 6T"
        self.__deviceVendor = deviceVendor  # Example : "OnePlus"
        self.__deviceModel = deviceModel  # Example : "ONEPLUS A6013"
        self.__deviceSerialNumber = deviceSerialNumber  # Example : "38aa48613fd1536f"
        self.__deviceId = deviceId  # Example : "sdm845"

        # seedDevice is the code you receive by SMS when adding your phone as "the trusted phone" (the last one if you received severals)
        self.__seedDevice = seedDevice  # Example : xfu3rbzqb47njp5y
        # mCode is the 6 digits code you set to protect sensible actions such as creating a virtual credit card
        self.__mCode = mCode  # Example : 012345

    def getUserInfo(self) -> dict:

        if not self.__connected:
            raise ConnectionError

        r = self.__s.get(f"{BASE_URL}/user/{VERSION}person/me")
        return r.json()

    def getCards(self) -> dict:

        if not self.__connected:
            raise ConnectionError

        # We can remove the /preview at the end
        r = self.__s.get(f"{BASE_URL}/carte/{VERSION}cards/preview")
        return r.json()

    def getMaxCard(self) -> dict:

        if not self.__connected:
            raise ConnectionError

        r = self.__s.get(f"{BASE_URL}/carte/{VERSION}cards/max")
        return r.json()

    def getAccouts(self) -> dict:

        if not self.__connected:
            raise ConnectionError

        r = self.__s.get(
            f"{BASE_URL}/compte/{VERSION}accounts/preview")
        return r.json()

    def getTransactions(self, accountId: str, count: int) -> dict:

        if not self.__connected:
            raise ConnectionError

        r = self.__s.get(
            f"{BASE_URL}/compte/{VERSION}accounts/{accountId}/transactions?count={count}")
        return r.json()

    def getVirtualCards(self) -> list:

        if not self.__connected:
            raise ConnectionError

        r = self.__s.get(
            f"{BASE_URL}/nvvirtualisapi/rest/virtualcard")
        return r.json()

    def getVirtualCardOperations(self, cardNum: str) -> list:
        """
        [summary]

        :param cardNum: [description]
        :type cardNum: str
        :return: [description]
        :rtype: list
        """

        if not self.__connected:
            raise ConnectionError

        r = self.__s.get(
            f"{BASE_URL}/nvvirtualisapi/rest/virtualcard/{cardNum}/operation")
        return r.json()

    def getEnrollmentStatus(self) -> dict:
        """
        Check if device can be used for sensitive (deviceEnrolled) actions such as creating a new virtual card
        Output example : {'enrolled': True, 'deviceEnrolled': True, 'biometryActivated': False}

        :return: A dictionnary of booleans telling if the account is enrolled, if the device is enrolled and if biometry is enabled
        :rtype: dict
        """
        if not self.__connected:
            raise ConnectionError
        if not self.__sensibleOperationsEnabled:
            raise SensibleOperationsDisabledError

        headers = {
            'Content-Type': 'application/json;charset=utf-8',
        }

        data = {
            "device": {
                "serialNumber": self.__deviceSerialNumber,
                "model": self.__deviceModel,
                # It seems that "id" and "name" are not usefull to identify the device
                # "id": self.__deviceId,
                # "name": self.__deviceName,
                "vendor": self.__deviceVendor,
            }
        }

        data = json.dumps(data)

        r = self.__s.post(
            f"{BASE_URL}/nvsecurityapi/rest/enrollments/enrollmentStatus/getEnrollmentStatus", headers=headers, data=data)

        return r.json()

    def getServerTimeForOTP(self) -> datetime.datetime:
        """
        This method can be used to synchronize time with the server, but it seems it is useless for now.

        :return: A datetime object giving the time of the server
        :rtype: datetime.datetime
        """
        # This method seems to be useless to generate the OTP(One Time Password), but I leave it there

        if not self.__connected:
            raise ConnectionError

        r = self.__s.get(f"{BASE_URL}/nvsecurityapi/rest/enrollments/time")
        httpTime = r.headers["Date"]
        time = datetime.datetime.strptime(
            httpTime, '%a, %d %b %Y %H:%M:%S GMT')
        return time

    def generateVirtualCard(self, length: int, amount: float) -> dict:
        """
        Generate a new virtual credit card (11 virtual credit cards per day maximum)
        Output example : {'num': '5372040642164191000', 'dateCreation': '26/03/2021', 'duree': 0, 'dateEch': '09/21', 'mntSaisi': 14.3, 'mntRestant': 14.3, 'crypto': '812', 'devise': 'EUR'}

        :param length: The duration of the virtual credit card in months
        :type length: int
        :param amount: The amount in Euros contained in the virtual credit card
        :type amount: float
        :return: A dictionnary containing the information of the card
        :rtype: dict
        """
        if not self.__connected:
            raise ConnectionError
        if not self.__sensibleOperationsEnabled:
            raise SensibleOperationsDisabledError

        # We request a seed to create the OTP(One Time Password)
        seedOperation = self.__generateSeed(length, amount)
        # We generate the One Time Password (it is "totp" and not "otp" because it is a Time One Time Password...)
        totp = generateTOTP(self.__seedDevice, self.__mCode, seedOperation)

        headers = {
            'Content-Type': 'application/json',
        }

        data = {
            "accessInfos": {
                "accessCode": self.__JwtData["accessCode"],
                "efs": self.__JwtData["efs"],
                # Yes oauthToken is the same as accessCode
                "oauthToken": self.__JwtData["accessCode"],
                "si": self.__JwtData["si"]
            },
            "device": {
                "biometryActivation": "N",  # For now we do not treat biometry
                "model": self.__deviceModel,
                "serialNumber": self.__deviceSerialNumber,
                "vendor": self.__deviceVendor
            },
            "totp": totp
        }

        data = json.dumps(data)

        r = self.__s.post(
            f"{BASE_URL}/nvvirtualisapi/rest/virtualcard", headers=headers, data=data)

        return r.json()
