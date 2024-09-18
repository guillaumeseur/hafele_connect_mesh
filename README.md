# Häfele Connect Mesh Integration for Home Assistant (HACS)
Add Häfele mesh devices to Home Assistant

This repository provides an integration for Home Assistant (HACS) to allow Häfele Connect Mesh devices to be controlled within Home Assistant.

## Requirements

- [Häfele Connect Mesh Gateway](https://www.haefele.de/de/produkt/gateway-haefele-connect-mesh-/P-01698057/)
- Other Häfele Mesh devices

## Setup Guide

### Step 1: Set Up Häfele Connect Mesh on Your Phone

Most users will have already completed this step. If you haven't, or if you encounter any issues, follow these instructions:

1. **Download the Häfele Connect Mesh App:**
   - [Google Play Store](https://play.google.com/store/apps/details?id=de.haefele.app.connect.mesh.v2)
   - [Apple App Store](https://apps.apple.com/de/app/h%C3%A4fele-connect-mesh-2-0/id6469770737)

2. **App Configuration:**
   - Open the app and go to Settings.
   - Create or sign in to your account.
   - Click on 'Set up mode'.

3. **Add Devices:**
   - Go to Dashboard > Devices > + icon.
   - When the connect-mesh gateway is powered on and connected to the internet, it will show in the discovery list. Add the device.

   Note: If the last step doesn't work, the device may still be connected to your phone. Switch back to 'Control mode' on the dashboard, and a blue popup should appear allowing you to connect to the 'cloud'.

4. **Ensure Other Devices Are Connected:**
   - Make sure you have other devices connected that you will need to control through Home Assistant.

5. **Upload App Configuration to Cloud:**

   After making any changes in the app or completing the first setup:
   
   1. Change to 'Control mode' in the app.
   2. Navigate to Gateway > Cloud settings > Synced networks.
   3. Click on the network upload button to sync your configuration with the cloud.

### Troubleshooting

- **Lights on the Gateway:**
  - BLE flickering: Not connected to the Connect Mesh app
    - Reset the gateway device with the physical button and try again.
  - Internet flickering: Not connected to the internet.
    - Check if the cable works and you are signed into an account on the app.

### Step 2: Create an API Token

1. Make sure you signed into your Connect Cloud Account and ensure all gateway lights are on.
2. Go to [Connect Mesh Cloud](https://cloud.connect-mesh.io/) and sign in with the account you created in Step 1.
3. Navigate to the Developer Page (use this [link](https://cloud.connect-mesh.io/developer) as there's no button).
4. Create a new API token:
   - Use the offset to change the expiration date (unit: MONTH, offset: 36, for 3 years).
   - Click on SET before creating the token.
   - Example token: `CMC_ab12cd34_ef56gh78ij90kl12mn34op56qr78st90uv12wx34yz56ab78cd90ef12`.

### Step 3: Add Custom Repository in HACS

1. In Home Assistant Community Store (HACS), add this custom repository.
2. Install Häfele Connect Mesh.

### Step 4: Add the Integration

1. Add the Häfele Connect Mesh integration.
2. Fill in the API token.
3. Select the network you want to add and submit.

You are all set!

## To Do List

- Add a way to change RGB color when API supports this functionality.
- Resolve the issue where name changes through the app don't appear in Home Assistant.
- Investigate the possibility to see states when using a physical button.

---

Feel free to customize it further as per your needs.
