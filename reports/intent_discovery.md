# AppleSupport Intent Taxonomy Discovery Report

Analyzed 12,000 customer support initial messages.

## 1. Intent Taxonomy Overview (9 Data-Grounded Intents)

| Intent Name | Escalation Policy | Diagnostic Keywords | Key Historical Support Pattern |
| :--- | :--- | :--- | :--- |
| `battery_power` | **AUTO_HANDLE** | battery, drain, draining, charge, charging | Ask what version of iOS is installed under Settings > General > About. |
| `software_update` | **AUTO_HANDLE** | update, ios, updating, install, download | Recommend connecting to reliable Wi-Fi and connecting to power. |
| `apple_id_account` | **ESCALATE** | apple id, password, locked, login, account | Direct customer to iforgot.apple.com for self-service password recovery. |
| `audio_bluetooth` | **AUTO_HANDLE** | bluetooth, airpods, headphones, sound, speaker | Instruct user to forget device in Settings > Bluetooth and re-pair. |
| `screen_hardware` | **ESCALATE** | screen, cracked, broken, display, touch | Provide Apple Support App link or locate.apple.com to book a Genius Bar appointment. |
| `wifi_cellular` | **AUTO_HANDLE** | wifi, wi-fi, cellular, service, signal | Advise toggling Airplane Mode on for 30 seconds and off. |
| `billing_subscriptions` | **ESCALATE** | charge, charged, billing, bill, refund | Direct customer to reportaproblem.apple.com to review purchase history and submit refund claims. |
| `app_system_performance` | **AUTO_HANDLE** | app, apps, crash, crashing, freeze | Instruct user on how to force close the app and restart device. |
| `general_inquiry_feedback` | **AUTO_HANDLE** | trade in, compatible, compatibility, feature, store hours | Provide official Apple specs or support page link. |

## 2. Intent Details & Boundary Conditions

### `battery_power`
**Description:** Issues related to fast battery drain, sudden shutdown, charging failure, overheating, or battery health degradation.

**Default Escalation Policy:** `auto_handle`

**Escalate If:** swollen battery, smoke or physical burn danger, hardware replacement needed out of warranty

**Positive Examples:**
- *"My iPhone battery is draining from 100% to 20% in two hours after the update."*
- *"Why won't my iPhone charge past 80% when plugged in?"*
- *"My phone keeps shutting off randomly with 30% battery remaining."*
- *"The phone gets burning hot whenever I connect the charger."*

**Boundary Cases:**
> If a user reports battery drain immediately following an iOS update, classify as battery_power if battery is the primary complaint, but software_update if they report the update installation failed or broke multiple apps.

**Historical Resolution Pattern:**
- Ask what version of iOS is installed under Settings > General > About.
- Direct user to check Settings > Battery > Battery Health to inspect Maximum Capacity.
- Recommend reviewing battery usage by app to spot background activity.

---

### `software_update`
**Description:** Problems updating iOS/macOS, update failed/stuck, verification errors, or storage space errors during update.

**Default Escalation Policy:** `auto_handle`

**Escalate If:** bricked device requiring DFU restore with data loss risk, beta software bugs requiring developer profile assistance

**Positive Examples:**
- *"My iOS update has been stuck on 'Estimating time remaining' for 3 hours."*
- *"It says unable to verify update because I'm no longer connected to internet."*
- *"I don't have enough storage space to download iOS 11."*
- *"My phone is stuck on the Apple logo after updating last night."*

**Boundary Cases:**
> If the phone is stuck in a bootloop / Apple logo following an update, diagnostic steps can be auto-handled (recovery mode), but persistent bricking escalates to human support.

**Historical Resolution Pattern:**
- Recommend connecting to reliable Wi-Fi and connecting to power.
- Advise restarting the device and trying the update through iTunes / Finder on Mac.
- Provide link to Apple Support article for iOS update recovery mode.

---

### `apple_id_account`
**Description:** Account security, Apple ID login, two-factor authentication, forgotten password, or activation lock.

**Default Escalation Policy:** `escalate`

**Escalate If:** identity verification required, account takeover or security breach, disabled account requiring financial/identity proof

**Positive Examples:**
- *"My Apple ID has been locked for security reasons and I can't reset it."*
- *"I am not receiving my 2-factor authentication code on my phone."*
- *"How do I recover my iCloud password if I forgot my trusted phone number?"*
- *"My account says disabled in App Store and iTunes."*

**Boundary Cases:**
> Password reset guidance (iforgot.apple.com) is automated; but account takeover, compromised credentials, or disabled accounts with security holds require escalation.

**Historical Resolution Pattern:**
- Direct customer to iforgot.apple.com for self-service password recovery.
- For account security holds or verification failures, escalate to Apple Support phone/DM team.

---

### `audio_bluetooth`
**Description:** Issues with AirPods, Bluetooth accessories pairing/disconnecting, microphone, speaker distortion, or call audio.

**Default Escalation Policy:** `auto_handle`

**Escalate If:** hardware failure of speaker/mic requiring repair, lost single AirPod replacement request

**Positive Examples:**
- *"My left AirPod has no sound coming out even though it's charged."*
- *"Bluetooth keeps disconnecting from my car every 5 minutes."*
- *"People can't hear me on phone calls unless I put them on speakerphone."*
- *"Static and crackling noise in my headphones."*

**Boundary Cases:**
> If Bluetooth disconnects along with Wi-Fi dropping, classify as wifi_connectivity if network chip/settings are the culprit.

**Historical Resolution Pattern:**
- Instruct user to forget device in Settings > Bluetooth and re-pair.
- Provide steps to reset AirPods (press and hold setup button on back of case).
- Suggest testing voice memos to isolate hardware microphone vs app permissions.

---

### `screen_hardware`
**Description:** Physical damage, cracked screen, unresponsive touchscreen, display glitches, camera hardware, or Genius Bar repair booking.

**Default Escalation Policy:** `escalate`

**Escalate If:** physical repair quotation needed, warranty/AppleCare+ claim processing, in-person Genius Bar scheduling

**Positive Examples:**
- *"I dropped my iPhone and the screen is shattered, how do I get it fixed?"*
- *"The touch screen is completely unresponsive on the right half."*
- *"There are vertical green lines across my display."*
- *"How do I make an appointment at the Apple Store Genius Bar?"*

**Boundary Cases:**
> If touchscreen freeze is caused by a frozen app, reboot guidance is auto-handled; if physical glass crack or digitizer hardware failure, escalate to repair booking.

**Historical Resolution Pattern:**
- Provide Apple Support App link or locate.apple.com to book a Genius Bar appointment.
- Inform customer to back up device before bringing it in for screen repair.

---

### `wifi_cellular`
**Description:** Wi-Fi disconnecting/not joining, cellular 'No Service' / 'Searching', dropped calls, or mobile data issues.

**Default Escalation Policy:** `auto_handle`

**Escalate If:** greyed-out Wi-Fi indicating baseband hardware failure, SIM failure requiring carrier or hardware replacement

**Positive Examples:**
- *"My phone keeps showing 'No Service' even with my SIM card inserted."*
- *"Wi-Fi toggle is greyed out in Settings."*
- *"My phone connects to Wi-Fi but says 'No Internet Connection'."*
- *"Cellular data stops working unless I toggle Airplane Mode."*

**Boundary Cases:**
> If carrier-specific network outage (e.g. AT&T or Verizon down), advise contacting carrier; if device network settings issue, guide reset network settings.

**Historical Resolution Pattern:**
- Advise toggling Airplane Mode on for 30 seconds and off.
- Instruct user to perform Reset Network Settings in Settings > General > Reset.
- Check for Carrier Settings Update in Settings > General > About.

---

### `billing_subscriptions`
**Description:** App Store charges, unauthorized purchases, subscription cancellations, refund requests, or credit card payment declines.

**Default Escalation Policy:** `escalate`

**Escalate If:** financial dispute or chargeback, unauthorized card fraud, refund status inquiries requiring account lookup

**Positive Examples:**
- *"I was charged $9.99 for a subscription I cancelled last week."*
- *"There is an unauthorized purchase on my credit card from iTunes."*
- *"How do I request a refund for an app that doesn't work?"*
- *"My payment method was declined in the App Store."*

**Boundary Cases:**
> Guiding the user to reportaproblem.apple.com for self-service refund requests is automated; processing financial disputes or investigating credit card fraud escalates to human agents.

**Historical Resolution Pattern:**
- Direct customer to reportaproblem.apple.com to review purchase history and submit refund claims.
- Explain how to manage and cancel subscriptions under Settings > [User Name] > Subscriptions.
- Escalate to billing support specialist via DM or phone for disputed transactions.

---

### `app_system_performance`
**Description:** App crashes, freezing, sluggish system UI, keyboard lag, storage full warnings, or camera app black screen.

**Default Escalation Policy:** `auto_handle`

**Escalate If:** kernel panics / spontaneous reboots persisting after factory restore, hardware camera sensor failure

**Positive Examples:**
- *"Instagram and Twitter keep crashing to home screen immediately upon opening."*
- *"The keyboard has a terrible 2-second lag when typing messages."*
- *"My camera app just shows a black screen when I open it."*
- *"Phone is running extremely slow and unresponsive."*

**Boundary Cases:**
> If app crashes occur only on one third-party app, advise updating app or contacting third-party dev; if system-wide freeze, guide force restart.

**Historical Resolution Pattern:**
- Instruct user on how to force close the app and restart device.
- Guide user to check for app updates in the App Store.
- Recommend checking available storage in Settings > General > iPhone Storage.

---

### `general_inquiry_feedback`
**Description:** General questions about product features, device compatibility, trade-in values, retail store hours, or feedback.

**Default Escalation Policy:** `auto_handle`

**Escalate If:** trade-in dispute or lost shipment, complaints requiring managerial escalation

**Positive Examples:**
- *"Does the Apple Watch Series 3 work with iPhone 6?"*
- *"What is the trade-in value for an iPhone 7 in good condition?"*
- *"What time does the Fifth Avenue Apple Store close today?"*
- *"Can I use two different eSIM profiles on the same device?"*

**Boundary Cases:**
> General specification and policy questions can be auto-handled using official guidelines; trade-in appraisal disputes or order cancellations escalate.

**Historical Resolution Pattern:**
- Provide official Apple specs or support page link.
- Direct customer to apple.com/retail for store hours and Genius Bar availability.

---

