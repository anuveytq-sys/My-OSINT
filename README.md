🔎 My OSINT

My OSINT is a lightweight, modular OSINT (Open-Source Intelligence) toolkit designed for Termux on Android.

It brings multiple OSINT capabilities together behind a simple command-line interface, allowing you to investigate emails, phone numbers, and usernames from one tool.

⚠️ For authorized and lawful use only. Only investigate information you have permission or a legitimate reason to access.

⸻

✨ Features

📧 Email OSINT

* Email presence checks
* Multiple email-service checks
* Holehe-powered account discovery
* SpiderFoot-based email modules
* Structured results and error handling

📱 Phone OSINT

* Phone number information
* PhoneInfoga integration
* SpiderFoot phone module
* Supports international phone formats

👤 Username OSINT

* Username discovery across supported platforms
* User-scanner integration
* Organized scan output

⚡ Modular Architecture

My OSINT is designed around independent modules, making it easier to maintain and extend with additional OSINT capabilities.

⸻

📱 Requirements

* Android device
* Termux
* Internet connection
* ARM64 Android is recommended for the bundled PhoneInfoga binary

⸻

🚀 Installation on Termux

Open Termux and run:

pkg update -y
pkg upgrade -y
pkg install -y git
termux-setup-storage

Allow Termux storage permission when Android asks.

Then clone the repository:

git clone https://github.com/anuveytq-sys/My-OSINT.git

Enter the directory:

cd My-OSINT

Run the installer:

bash install.sh

When the installer asks:

Continue with installation? [y/N]:

Type:

y

The installer will set up the required components and dependencies.

⸻

🛠️ Running My OSINT

📧 Scan an Email

python main.py -e "example@example.com"

📱 Scan a Phone Number

Use an international format:

python main.py -p "+919876543210"

👤 Scan a Username

python main.py -u "example_username"

⸻

📖 Command Help

To view the available options:

python main.py --help

⸻

🧩 Third-Party Components

My OSINT uses third-party open-source projects to provide some of its functionality, including:

* Holehe — email account checks
* user-scanner — username discovery
* PhoneInfoga — phone-number OSINT
* SpiderFoot — OSINT modules

Their respective licenses and notices should be retained where applicable.

⸻

⚠️ Disclaimer

My OSINT is intended for educational, research, security, and other lawful purposes.

Do not use this software to:

* Access private accounts
* Bypass authentication
* Harass or stalk individuals
* Circumvent security controls
* Collect information unlawfully
* Violate the terms of services you use

The results produced by OSINT tools may contain false positives, false negatives, outdated information, or service-side errors. A FOUND result does not by itself prove ownership or identity.

You are responsible for how you use this software and for complying with applicable laws and the terms of the services you query.

⸻

⭐ Support the Project

If you find My OSINT useful:

⭐ Star the repository
🐛 Report bugs
💡 Suggest improvements
🔧 Contribute new modules

⸻

👨‍💻 Author

anuveytq-sys

Built for learning, experimentation, and responsible OSINT research.

⸻

📄 License

My OSINT’s original code is licensed under the MIT License.

Third-party components remain subject to their respective licenses.