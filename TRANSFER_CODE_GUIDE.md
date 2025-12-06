# Transfer Code (引き継コード) Guide

## Overview

Transfer codes (引き継コード, hikitsugi code) allow you to transfer your Love Live SIF account between devices. This guide explains how they work and how to safely swap devices or backends.

## How Transfer Codes Work

### What is a Transfer Code?

A transfer code consists of two parts:
1. **Transfer ID**: Your Friend ID (invite_code) - displayed in-game
2. **Transfer Passcode**: A 12-character random code (A-Z, 0-9)

### How They're Generated

1. In-game: Go to Settings → Account Transfer → Generate Transfer Code
   - This calls the `handover/reserveTransfer` endpoint
   - Creates a new 12-character passcode
   - Stores a SHA1 hash in the database: `SHA1(SHA1(transfer_id) + passcode)`

2. Command line: Use `scripts/generate_passcode.py`
   ```bash
   python scripts/generate_passcode.py --user-id <your_user_id>
   ```

### How Transfer Works

When you use a transfer code on a new device:
1. The client sends both Transfer ID and Transfer Passcode
2. Server calculates: `SHA1(SHA1(transfer_id) + passcode)`
3. Server finds the user account with matching `transfer_sha1`
4. **Credentials are swapped** between the old device account and new device account
5. The transfer code is invalidated (`transfer_sha1` set to `None`)

**Important**: Transfer codes are **one-time use only**. After using it, you need to generate a new one.

## Scenarios

### Scenario 1: Swapping Frontend Devices (iPad → iPhone)

**What happens**: You want to play on a different device but keep the same backend server.

**Steps**:
1. **On old device (iPad)**:
   - Open the game
   - Go to Settings → Account Transfer → Generate Transfer Code
   - **Write down** both the Transfer ID and Transfer Passcode
   - Keep the game running (or note you'll need to login again after transfer)

2. **On new device (iPhone)**:
   - Install the game and patch it for your private server
   - Configure it to point to your server (same IP address)
   - Start the game (create a new account if needed)
   - Go to Settings → Account Transfer → Enter Transfer Code
   - Enter the Transfer ID and Transfer Passcode from step 1
   - Your account data will transfer to the new device

**Important Notes**:
- ✅ Your account data stays on the same backend server
- ✅ Only the credentials (key/passwd) are swapped between devices
- ⚠️ The transfer code becomes invalid after use
- ⚠️ The old device will lose access to the account (it gets the new device's account instead)

### Scenario 2: Changing Backend (New Laptop)

**What happens**: You're moving the entire server to a new computer but keeping the same devices.

**Steps**:
1. **On old laptop**:
   - Stop the NPPS4 server
   - Copy the entire `<SIF1>` folder to the new laptop
   - This includes:
     - `data/main.sqlite3` (database with all user accounts)
     - `config.toml` (server configuration)
     - All other files

2. **On new laptop**:
   - Paste the `<SIF1>` folder
   - Make sure `config.toml` points to the correct database path
   - Start the NPPS4 server
   - Your devices can continue playing normally

**Important Notes**:
- ✅ **No transfer code needed** - all account data is in the database
- ✅ All user accounts are preserved
- ✅ Devices don't need to do anything - they just reconnect
- ⚠️ Make sure the server IP address in `config.toml` matches your new network setup
- ⚠️ If your IP address changes, update the client configuration on your devices

### Scenario 3: Changing Both Backend and Frontend

**What happens**: You're moving to a new laptop AND want to use a different device.

**Steps**:
1. Follow **Scenario 2** steps to copy the server to new laptop
2. Follow **Scenario 1** steps to transfer account to new device
3. Make sure the new device points to the new server IP address

## Where Data is Stored

### Backend (Server)

All user data is stored in the database:
- **Location**: `data/main.sqlite3` (default SQLite setup)
- **Contains**: All user accounts, cards, items, progress, etc.
- **Backup**: Just copy this file (and the `-shm` and `-wal` files if they exist)

### Frontend (Device)

Each device stores:
- **Login credentials**: Encrypted key and password
- **Session token**: Temporary authentication token
- **No game data**: All data is on the server

## IP Address Changes

### When Your Server IP Changes

If your IP address changes (e.g., new network, new laptop on different network):

1. **Update server configuration** (if needed):
   - Check `config.toml` for any IP-specific settings
   - The database doesn't store IP addresses, so no changes needed there

2. **Update client configuration on devices**:
   - You need to reconfigure the patched SIF client to point to the new IP
   - Use the SIF patcher tool: https://ethanaobrien.github.io/sif-patcher/
   - Enter your new server IP address and port

3. **No transfer code needed**:
   - Your account data is safe in the database
   - Just update the client configuration and login again

### Important About IP Addresses

- The server doesn't care about IP addresses for account access
- Accounts are identified by `key` and `passwd` credentials
- As long as the device has the correct credentials, it can access the account
- Transfer codes work the same way regardless of IP address

## Safety Tips

1. **Always generate a new transfer code before you need it**
   - Transfer codes are single-use
   - Generate one before switching devices

2. **Write down transfer codes immediately**
   - Don't rely on screenshots (they can be lost)
   - Store them securely (password manager, notes app, etc.)

3. **Backup your database regularly**
   - Copy `data/main.sqlite3` to a safe location
   - This is your entire server - losing it means losing all accounts

4. **Test transfer codes on a test account first**
   - If you're unsure, create a test account and try the transfer process

5. **Keep server backups**
   - When changing backends, keep a backup of the old server
   - You can always go back if something goes wrong

## Command Line Tools

### Generate Transfer Code

```bash
python scripts/generate_passcode.py --user-id <user_id>
```

Or by invite code:
```bash
python scripts/generate_passcode.py --invite-code <invite_code>
```

### Export Account Data

You can also export your account as a backup:
```bash
python scripts/export_account.py --user-id <user_id>
```

This creates a backup file that can be imported later if needed.

## Troubleshooting

### "Transfer code invalid or expired"
- Transfer codes don't expire, but they're single-use
- Make sure you haven't used it already
- Generate a new transfer code

### "Cannot find user"
- Double-check the Transfer ID (Friend ID)
- Make sure you're entering the passcode correctly (case-sensitive, no spaces)

### "Account is locked"
- The account might be locked for security reasons
- Check the database or contact server admin

### Lost transfer code
- Generate a new one (the old one is invalid after use anyway)
- Use `scripts/generate_passcode.py` if you can't access the game

## Summary

- **Frontend swap (iPad → iPhone)**: Use transfer code (one-time use)
- **Backend swap (new laptop)**: Just copy the database file - no transfer code needed
- **IP address change**: Update client configuration - no transfer code needed
- **Data is safe**: All data is in `data/main.sqlite3` - backup this file!

The transfer code system is designed for moving accounts between devices on the same server. When you're just moving the server itself, you're moving all the data, so no transfer is needed.

