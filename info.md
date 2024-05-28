Häfele Connect Mesh Integration for Home Assistant (HACS)
Add Häfele mesh devices to Home Assistant

This repository provides an integration for Home Assistant (HACS) to allow Häfele Connect Mesh devices to be controlled within Home Assistant.

Requirements
Häfele Connect Mesh Gateway
Other Häfele Mesh devices
Setup Guide
Step 1: Set Up Häfele Connect Mesh on Your Phone
Most users will have already completed this step. If you haven't, or if you encounter any issues, follow these instructions:

Download the Häfele Connect Mesh App:

Google Play Store
Apple App Store
App Configuration:

Open the app and go to Settings.
Create or sign in to your account.
Click on 'Set up mode'.
Add Devices:

Go to Dashboard > Devices > + icon.
When the connect-mesh gateway is powered on and connected to the internet, it will show in the discovery list. Add the device.
Note: If the last step doesn't work, the device may still be connected to your phone. Switch back to 'Control mode' on the dashboard, and a blue popup should appear allowing you to connect to the 'cloud'.

Ensure Other Devices Are Connected:

Make sure you have other devices connected that you will need to control through Home Assistant.
Troubleshooting
Lights on the Gateway:
BLE flickering: Not connected to the Connect Mesh app
Reset the gateway device with the physical button and try again.
Internet flickering: Not connected to the internet.
Check if the cable works and you are signed into an account on the app.
Step 2: Create an API Token
Make sure you signed into your Connect Cloud Account and ensure all gateway lights are on.
Go to Connect Mesh Cloud and sign in with the account you created in Step 1.
Navigate to the Developer Page (use this link as there's no button).
Create a new API token:
Use the offset to change the expiration date (unit: MONTH, offset: 36, for 3 years).
Click on SET before creating the token.
Example token: CMC_ab12cd34_ef56gh78ij90kl12mn34op56qr78st90uv12wx34yz56ab78cd90ef12.
Step 3: Add Custom Repository in HACS
In Home Assistant Community Store (HACS), add this custom repository.
Install Häfele Connect Mesh.
Step 4: Add the Integration
Add the Häfele Connect Mesh integration.
Fill in the API token.
Select the network you want to add and submit.
You are all set!

To Do List
Add a way to change RGB color and Multiwhite temperature.
Expand the compatible device list.
Resolve the issue where name changes through the app don't appear.
Investigate the possibility to see states when using a physical button.
Feel free to customize it further as per your needs.