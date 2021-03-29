<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://www.aumaxpourmoi.fr/">
    <img src="https://www.aumaxpourmoi.fr/wp-content/themes/aumax-front/assets/img/logo-white.png" alt="Logo Aumax pour moi" style="background-color: #450290; padding: 15px; border-radius: 10px;">
  </a>
</p>



<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#features">Features</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

There is only an app available for now and no website, and I prefer to use my computer rather than my phone (it is faster and you can automate things). Moreover I love to do some reverse engineering, so I reversed the aumax android app (`aumax-pour-moi_3.22.1.apk`) using [objection](https://github.com/sensepost/objection) to patch the apk to be able to disable SSL Pinning and place Hooks to observe some function arguments and return values. I also decompiled the apk back to Java code to statically analyse the app. Then I used [mitmproxy](https://mitmproxy.org/) to observe the HTTP network traffic used to call the Aumax API. The hardest thing I did was to reverse their TOPT (Time One Time Password) algorithm. Also, some things was weird since a lot of information (such as the deviceSerialNumber which is unique per app and is used for security purposes) was still logged (the developpers forgot to remove them). I also noticed that during the generation of a new virtual credit cards, a field `signature` (which seemed to be the request signed by some private key) was sent to the server, but not needed (I removed this field and it is still working well).


<!-- FEATURES -->
## Features

Here is what you can do using this python API:
* Connect to your aumax account
* List all your accounts
* List all financial operations on your accounts
* List all your virtual credit card
* List all financial operations made on each virtual credit cards
* Create a virtual credit card with a custom amount on it and a custom number of months during which the card is enabled


<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

(You only need the `requests` python package)

1. If you do NOT want to do sensible operations such as creating a virtual credit card, there is no prerequisites
2. Else, you need to get some of your Android (I don't know how to do this on an iOS device...) device information, such as the serialNumber (unique for each app), the device vendor, and the device model.
   1. To do so, you can use `adb` (check on the Internet what adb is)
   2. We will use `adb` to show the logs of the app, because the developpers of the Aumax app forgot to remove some logging and the information we want are in theses logs...
   3. So once you installed `adb` on your computer, plug your Android device into your computer via usb and type (in a linux shell) : 
    ```sh
    adb logcat fr.aumax.android | grep -E "(Device Info SerialNumber|Device Info Vendor|Device Info Model)"
    ```
   4. Then launch the Aumax app and login : the informations should appear on your shell.
3. You will also need a code named `mCode` which is simply the 6-digits code you use to do sensible operations in the aumax app.
4. Finally, you will need a code named `seedDevice` which is the last code you received by SMS when you added you device as `the trusted device`. If you can't find it, you can regenerate one by doing the following :
   1. Tap on the 3 vertical dots at the top right corner of the Aumax app
   2. Tap on `mon profil`
   3. Tap on `Paramètres`
   4. Tap on `Dissocier mon téléphone`, then tap `Ok`
   5. Then try to create a new virtual credit card, it will ask you to set your device as `the trusted device` and you'll receive a new `seedDevice` by SMS.


### Installation

1. Clone the repo
   ```sh
   git clone git@github.com:CharlieBailly/aumax-python.git
   ```


2. Inspire you from the `example.py` which is also below:

```python
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

```


<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Charlie BAILLY - charliebailly29@gmail.com

Project Link: [https://github.com/CharlieBailly/aumax-python](https://github.com/CharlieBailly/aumax-python)

## Acknowledgements

This ReadMe is inspired from [Best-README-Template](https://github.com/othneildrew/Best-README-Template)


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/CharlieBailly/aumax-python.svg?style=for-the-badge
[contributors-url]: https://github.com/CharlieBailly/aumax-python/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/CharlieBailly/aumax-python.svg?style=for-the-badge
[forks-url]: https://github.com/CharlieBailly/aumax-python/network/members
[stars-shield]: https://img.shields.io/github/stars/CharlieBailly/aumax-python.svg?style=for-the-badge
[stars-url]: https://github.com/CharlieBailly/aumax-python/stargazers
[issues-shield]: https://img.shields.io/github/issues/CharlieBailly/aumax-python.svg?style=for-the-badge
[issues-url]: https://github.com/CharlieBailly/aumax-python/issues
[license-shield]: https://img.shields.io/github/license/CharlieBailly/aumax-python.svg?style=for-the-badge
[license-url]: https://raw.githubusercontent.com/CharlieBailly/aumax-python/main/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/charlie-bailly-aa710a196/
[product-screenshot]: images/screenshot.png
