from Aumax import Aumax

# See ReadMe to know how to obtain these values
myDeviceSerialNumber = "38ba48613fd1636f"
myDeviceVendor = "OnePlus"
myDeviceModel = "ONEPLUS A6013"
# myDeviceName and myDeviceId seem not really needed, you can maybe leave them blank : ""
myDeviceName = "OnePlus 6T"
myDeviceId = "sdm845"

# seedDevice id the last code your received by SMS : (See ReadMe to know how to regenerate one)
seedDevice = "xfu3rbzqb47njp5y"
# mCode is your 6-digits password :
mCode = "012345"

email = "youremail@example.com"
password = "yourAumaxPassword"

api = Aumax(email, password)

if api.connect():
    # The following actions only require email and password, not the other parameters

    print(api.getUserInfo())
    print()

    print(api.getCards())
    print()

    print(api.getMaxCard())
    print()

    accounts = api.getAccouts()
    print(accounts)

    firstAccount = accounts["tiles"][0]["account"]
    print()

    print(firstAccount["id"])
    print()

    # Get the 10 last transactions of the first account
    transactions = api.getTransactions(firstAccount["id"], 10)
    print(transactions)
    print()

    virtualCards = api.getVirtualCards()
    print(virtualCards)
    print()

    # Get all the operations made by the first virtual card
    operations = api.getVirtualCardOperations(virtualCards[0]["num"])
    print(operations)
    print()

    #######################################################

    # Now if we want to create a virtual credit card for example, we need to enable sensible operations,
    api.enableSensibleOperations(myDeviceName, myDeviceVendor, myDeviceModel,
                                 myDeviceSerialNumber, myDeviceId, seedDevice, mCode)
    print(api.getEnrollmentStatus())
    print()
    # If you entered the right info, you should have True to 'enrolled' and 'deviceEnrolled'
    # example : {'enrolled': True, 'deviceEnrolled': True, 'biometryActivated': False}

    # Now let's create a new virtual credit card (limited to 11 per day) with 7.0 euros on it and that is valid for 9 months
    duree = "9"  # 9 months
    amount = "7.0"  # 7.0 euros

    virtualCard = api.generateVirtualCard(6, 3)
    print(virtualCard)
    print()
    # Example output :
    # {'num': '5372040132406814000', 'dateCreation': '29/03/2021', 'duree': 0, 'dateEch': '09/21', 'mntSaisi': 3.0, 'mntRestant': 3.0, 'crypto': '855', 'devise': 'EUR'}
