from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import requests
import os

# Fungsi untuk memformat ukuran file
def format_size(size):
    size = int(size)
    if size >= 1073741824:
        return f"{size / 1073741824:.2f} GB"
    elif size >= 1048576:
        return f"{size / 1048576:.2f} MB"
    else:
        return f"{size / 1024:.2f} KB"

# Fungsi untuk mengganti nama file menjadi Game Data #n
def extract_filename(url, index):
    return f"Game Data #{index}"

# Fungsi untuk mendapatkan data pembaruan game Genshin Impact
def get_game_updates_gi():
    url = "https://api.mazagung.id/game.php?id=gopR6Cufr3"
    response = requests.get(url)
    data = response.json()

    full_installation_files = []
    old_patches = []
    new_patches = []

    pre_download = data['data']['game_packages'][0].get('pre_download', {})
    main = data['data']['game_packages'][0].get('main', {})
    
    major = pre_download.get('major', {}) or main.get('major', {})
    patches = pre_download.get('patches', []) or main.get('patches', [])

    # Full Installation
    if major:
        version = major['version']
        game_pkgs = major.get('game_pkgs', [])
        for index, game_pkg in enumerate(game_pkgs, start=1):
            filename = extract_filename(game_pkg['url'], index)
            full_installation_files.append({
                'type': filename,
                'version': version,
                'url': game_pkg['url'],
                'size': format_size(game_pkg['size'])
            })

        for audio_pkg in major.get('audio_pkgs', []):
            audio_type = "Unknown"
            if "Audio_Chinese_" in audio_pkg['url']:
                audio_type = "Audio CN"
            elif "Audio_English(US)_" in audio_pkg['url']:
                audio_type = "Audio US"
            elif "Audio_Korean_" in audio_pkg['url']:
                audio_type = "Audio KR"
            elif "Audio_Japanese_" in audio_pkg['url']:
                audio_type = "Audio JP"

            full_installation_files.append({
                'type': audio_type,
                'version': version,
                'url': audio_pkg['url'],
                'size': format_size(audio_pkg['size'])
            })

    # Patches
    for patch in patches:
        patch_data = {
            'version': patch['version'],
            'game_pkgs': [
                {
                    'type': 'Game Data',
                    'url': game_pkg['url'],
                    'size': format_size(game_pkg['size'])
                }
                for game_pkg in patch.get('game_pkgs', [])
            ],
            'audio_pkgs': [
                {
                    'type': "Audio CN" if "audio_zh-cn" in audio_pkg['url'] else
                            "Audio US" if "audio_en-us" in audio_pkg['url'] else
                            "Audio JP" if "audio_ja-jp" in audio_pkg['url'] else
                            "Audio KR" if "audio_ko-kr" in audio_pkg['url'] else
                            "Unknown",
                    'url': audio_pkg['url'],
                    'size': format_size(audio_pkg['size'])
                }
                for audio_pkg in patch.get('audio_pkgs', [])
            ]
        }
        if patch['version'] < major.get('version', ''):
            old_patches.append(patch_data)
        else:
            new_patches.append(patch_data)

    return full_installation_files, old_patches, new_patches, bool(major or patches)

# Fungsi untuk menyimpan pembaruan ke file HTML Genshin Impact
def save_to_html_gi(full_installation_files, old_patches, new_patches, file_path="updates_gi.html"):
    html_content = "<html><body>"
    html_content += "<h1>GENSHIN IMPACT (MANUAL UPDATE)</h1>\n"

    # Full Installation
    html_content += "<h2>Full Installation</h2>\n"
    if full_installation_files:
        grouped_files = {}
        for file in full_installation_files:
            version = file['version']
            if version not in grouped_files:
                grouped_files[version] = []
            grouped_files[version].append(file)

        for version, files in grouped_files.items():
            html_content += f"<h3>Version {version}</h3>\n<ul>"
            for file in files:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No data available for Full Installation.</p>\n"

    # Patches
    html_content += "<h2>Download From Patch</h2>\n"
    if old_patches:
        for patch in old_patches:
            html_content += f"<h3>Version {patch['version']}</h3>\n<ul>"
            for file in patch['game_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            for file in patch['audio_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No old patches available.</p>\n"

    html_content += "<h2>New Patches</h2>\n"
    if new_patches:
        for patch in new_patches:
            html_content += f"<h3>Version {patch['version']}</h3>\n<ul>"
            for file in patch['game_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            for file in patch['audio_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No new patches available.</p>\n"

    html_content += "</body></html>"

    with open(file_path, "w") as file:
        file.write(html_content)

# Fungsi command untuk menampilkan pembaruan Genshin Impact
async def update_gi_command(update: Update, context: CallbackContext):
    full_installation_files, old_patches, new_patches, has_updates = get_game_updates_gi()

    if has_updates:
        save_to_html_gi(full_installation_files, old_patches, new_patches)
        message = "<b>GENSHIN IMPACT (MANUAL UPDATE)</b>\n\n"

        # Full Installation
        message += "- <b>Full Installation</b>\n"
        grouped_files = {}
        for file in full_installation_files:
            version = file['version']
            if version not in grouped_files:
                grouped_files[version] = []
            grouped_files[version].append(file)

        for version, files in grouped_files.items():
            message += f" <b>Version {version}</b>\n"
            for file in files:
                message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
            message += "\n"

        # Old Patches
        message += "- <b>Download From Patch</b>\n"
        if old_patches:
            for patch in old_patches:
                message += f" <b>Version {patch['version']}</b>\n"
                for file in patch['game_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                for file in patch['audio_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                message += "\n"
        else:
            message += " No old patches available.\n\n"

        # New Patches
        message += "***********\n"
        if new_patches:
            for patch in new_patches:
                message += f" <b>Version {patch['version']}</b>\n"
                for file in patch['game_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                for file in patch['audio_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                message += "\n"
        else:
            current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            message += f"Update terakhir pada: {current_time}\n\n"

        await update.message.reply_text(message, parse_mode="HTML")
    else:
        await update.message.reply_text(
            "Tidak ada pembaruan tersedia saat ini.",
            parse_mode="HTML"
        )

# Fungsi untuk mendapatkan data pembaruan game Zenless Zone Zero
def get_game_updates_zzz():
    url = "https://api.mazagung.id/game.php?id=U5hbdsT9W7"
    response = requests.get(url)
    data = response.json()

    full_installation_files = []
    old_patches = []
    new_patches = []

    pre_download = data['data']['game_packages'][0].get('pre_download', {})
    main = data['data']['game_packages'][0].get('main', {})
    
    major = pre_download.get('major', {}) or main.get('major', {})
    patches = pre_download.get('patches', []) or main.get('patches', [])

    # Full Installation
    if major:
        version = major['version']
        game_pkgs = major.get('game_pkgs', [])
        for index, game_pkg in enumerate(game_pkgs, start=1):
            filename = extract_filename(game_pkg['url'], index)
            full_installation_files.append({
                'type': filename,
                'version': version,
                'url': game_pkg['url'],
                'size': format_size(game_pkg['size'])
            })

        for audio_pkg in major.get('audio_pkgs', []):
            audio_type = "Unknown"
            if "audio_zip_Cn" in audio_pkg['url']:
                audio_type = "Audio CN"
            elif "audio_zip_En" in audio_pkg['url']:
                audio_type = "Audio US"
            elif "audio_zip_Kr" in audio_pkg['url']:
                audio_type = "Audio KR"
            elif "audio_zip_Jp" in audio_pkg['url']:
                audio_type = "Audio JP"

            full_installation_files.append({
                'type': audio_type,
                'version': version,
                'url': audio_pkg['url'],
                'size': format_size(audio_pkg['size'])
            })

    # Patches
    for patch in patches:
        patch_data = {
            'version': patch['version'],
            'game_pkgs': [
                {
                    'type': 'Game Data',
                    'url': game_pkg['url'],
                    'size': format_size(game_pkg['size'])
                }
                for game_pkg in patch.get('game_pkgs', [])
            ],
            'audio_pkgs': [
                {
                    'type': "Audio CN" if "audio_zh-cn" in audio_pkg['url'] else
                            "Audio US" if "audio_en-us" in audio_pkg['url'] else
                            "Audio JP" if "audio_ja-jp" in audio_pkg['url'] else
                            "Audio KR" if "audio_ko-kr" in audio_pkg['url'] else
                            "Unknown",
                    'url': audio_pkg['url'],
                    'size': format_size(audio_pkg['size'])
                }
                for audio_pkg in patch.get('audio_pkgs', [])
            ]
        }
        if patch['version'] < major.get('version', ''):
            old_patches.append(patch_data)
        else:
            new_patches.append(patch_data)

    return full_installation_files, old_patches, new_patches, bool(major or patches)

# Fungsi untuk menyimpan pembaruan ke file HTML Zenless Zone Zero
def save_to_html_zzz(full_installation_files, old_patches, new_patches, file_path="updates_zzz.html"):
    html_content = "<html><body>"
    html_content += "<h1>ZENLESS ZONE ZERO (MANUAL UPDATE)</h1>\n"

    # Full Installation
    html_content += "<h2>Full Installation</h2>\n"
    if full_installation_files:
        grouped_files = {}
        for file in full_installation_files:
            version = file['version']
            if version not in grouped_files:
                grouped_files[version] = []
            grouped_files[version].append(file)

        for version, files in grouped_files.items():
            html_content += f"<h3>Version {version}</h3>\n<ul>"
            for file in files:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No data available for Full Installation.</p>\n"

    # Patches
    html_content += "<h2>Download From Patch</h2>\n"
    if old_patches:
        for patch in old_patches:
            html_content += f"<h3>Version {patch['version']}</h3>\n<ul>"
            for file in patch['game_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            for file in patch['audio_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No old patches available.</p>\n"

    html_content += "<h2>New Patches</h2>\n"
    if new_patches:
        for patch in new_patches:
            html_content += f"<h3>Version {patch['version']}</h3>\n<ul>"
            for file in patch['game_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            for file in patch['audio_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No new patches available.</p>\n"

    html_content += "</body></html>"

    with open(file_path, "w") as file:
        file.write(html_content)

# Fungsi command untuk menampilkan pembaruan Zenless Zone Zero
async def update_zzz_command(update: Update, context: CallbackContext):
    full_installation_files, old_patches, new_patches, has_updates = get_game_updates_zzz()

    if has_updates:
        save_to_html_zzz(full_installation_files, old_patches, new_patches)
        message = "<b>ZENLESS ZONE ZERO (MANUAL UPDATE)</b>\n\n"

        # Full Installation
        message += "- <b>Full Installation</b>\n"
        grouped_files = {}
        for file in full_installation_files:
            version = file['version']
            if version not in grouped_files:
                grouped_files[version] = []
            grouped_files[version].append(file)

        for version, files in grouped_files.items():
            message += f" <b>Version {version}</b>\n"
            for file in files:
                message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
            message += "\n"

        # Old Patches
        message += "- <b>Download From Patch</b>\n"
        if old_patches:
            for patch in old_patches:
                message += f" <b>Version {patch['version']}</b>\n"
                for file in patch['game_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                for file in patch['audio_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                message += "\n"
        else:
            message += " No old patches available.\n\n"

        # New Patches
        message += "***********\n"
        if new_patches:
            for patch in new_patches:
                message += f" <b>Version {patch['version']}</b>\n"
                for file in patch['game_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                for file in patch['audio_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                message += "\n"
        else:
            current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            message += f"Update terakhir pada: {current_time}\n\n"

        await update.message.reply_text(message, parse_mode="HTML")
    else:
        await update.message.reply_text(
            "Tidak ada pembaruan tersedia saat ini.",
            parse_mode="HTML"
        )

# Fungsi untuk mendapatkan data pembaruan game Honkai Star Rail
def get_game_updates_hsr():
    url = "https://api.mazagung.id/game.php?id=4ziysqXOQ8"
    response = requests.get(url)
    data = response.json()

    full_installation_files = []
    old_patches = []
    new_patches = []

    pre_download = data['data']['game_packages'][0].get('pre_download', {})
    main = data['data']['game_packages'][0].get('main', {})
    
    major = pre_download.get('major', {}) or main.get('major', {})
    patches = pre_download.get('patches', []) or main.get('patches', [])

    # Full Installation
    if major:
        version = major['version']
        game_pkgs = major.get('game_pkgs', [])
        for index, game_pkg in enumerate(game_pkgs, start=1):
            filename = extract_filename(game_pkg['url'], index)
            full_installation_files.append({
                'type': filename,
                'version': version,
                'url': game_pkg['url'],
                'size': format_size(game_pkg['size'])
            })

        for audio_pkg in major.get('audio_pkgs', []):
            audio_type = "Unknown"
            if "Chinese" in audio_pkg['url']:
                audio_type = "Audio CN"
            elif "English" in audio_pkg['url']:
                audio_type = "Audio US"
            elif "Korean" in audio_pkg['url']:
                audio_type = "Audio KR"
            elif "Japanese" in audio_pkg['url']:
                audio_type = "Audio JP"

            full_installation_files.append({
                'type': audio_type,
                'version': version,
                'url': audio_pkg['url'],
                'size': format_size(audio_pkg['size'])
            })

    # Patches
    for patch in patches:
        patch_data = {
            'version': patch['version'],
            'game_pkgs': [
                {
                    'type': 'Game Data',
                    'url': game_pkg['url'],
                    'size': format_size(game_pkg['size'])
                }
                for game_pkg in patch.get('game_pkgs', [])
            ],
            'audio_pkgs': [
                {
                    'type': "Audio CN" if "audio_zh-cn" in audio_pkg['url'] else
                            "Audio TW" if "audio_zh-tw" in audio_pkg['url'] else
                            "Audio US" if "audio_en-us" in audio_pkg['url'] else
                            "Audio JP" if "audio_ja-jp" in audio_pkg['url'] else
                            "Audio KR" if "audio_ko-kr" in audio_pkg['url'] else
                            "Unknown",
                    'url': audio_pkg['url'],
                    'size': format_size(audio_pkg['size'])
                }
                for audio_pkg in patch.get('audio_pkgs', [])
            ]
        }
        if patch['version'] < major.get('version', ''):
            old_patches.append(patch_data)
        else:
            new_patches.append(patch_data)

    return full_installation_files, old_patches, new_patches, bool(major or patches)

# Fungsi untuk menyimpan pembaruan ke file HTML Honkai Star Rail
def save_to_html_hsr(full_installation_files, old_patches, new_patches, file_path="updates_hsr.html"):
    html_content = "<html><body>"
    html_content += "<h1>HONKAI STAR RAIL (MANUAL UPDATE)</h1>\n"

    # Full Installation
    html_content += "<h2>Full Installation</h2>\n"
    if full_installation_files:
        grouped_files = {}
        for file in full_installation_files:
            version = file['version']
            if version not in grouped_files:
                grouped_files[version] = []
            grouped_files[version].append(file)

        for version, files in grouped_files.items():
            html_content += f"<h3>Version {version}</h3>\n<ul>"
            for file in files:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No data available for Full Installation.</p>\n"

    # Patches
    html_content += "<h2>Download From Patch</h2>\n"
    if old_patches:
        for patch in old_patches:
            html_content += f"<h3>Version {patch['version']}</h3>\n<ul>"
            for file in patch['game_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            for file in patch['audio_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No old patches available.</p>\n"

    html_content += "<h2>New Patches</h2>\n"
    if new_patches:
        for patch in new_patches:
            html_content += f"<h3>Version {patch['version']}</h3>\n<ul>"
            for file in patch['game_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            for file in patch['audio_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No new patches available.</p>\n"

    html_content += "</body></html>"

    with open(file_path, "w") as file:
        file.write(html_content)

# Fungsi command untuk menampilkan pembaruan Honkai Star Rail
async def update_hsr_command(update: Update, context: CallbackContext):
    full_installation_files, old_patches, new_patches, has_updates = get_game_updates_hsr()

    if has_updates:
        save_to_html_hsr(full_installation_files, old_patches, new_patches)
        message = "<b>HONKAI STAR RAIL (MANUAL UPDATE)</b>\n\n"

        # Full Installation
        message += "- <b>Full Installation</b>\n"
        grouped_files = {}
        for file in full_installation_files:
            version = file['version']
            if version not in grouped_files:
                grouped_files[version] = []
            grouped_files[version].append(file)

        for version, files in grouped_files.items():
            message += f" <b>Version {version}</b>\n"
            for file in files:
                message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
            message += "\n"

        # Old Patches
        message += "- <b>Download From Patch</b>\n"
        if old_patches:
            for patch in old_patches:
                message += f" <b>Version {patch['version']}</b>\n"
                for file in patch['game_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                for file in patch['audio_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                message += "\n"
        else:
            message += " No old patches available.\n\n"

        # New Patches
        message += "***********\n"
        if new_patches:
            for patch in new_patches:
                message += f" <b>Version {patch['version']}</b>\n"
                for file in patch['game_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                for file in patch['audio_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                message += "\n"
        else:
            current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            message += f"Update terakhir pada: {current_time}\n\n"

        await update.message.reply_text(message, parse_mode="HTML")
    else:
        await update.message.reply_text(
            "Tidak ada pembaruan tersedia saat ini.",
            parse_mode="HTML"
        )

# Fungsi untuk mendapatkan data pembaruan game Honkai Impact 3
def get_game_updates_honkai(server_url):
    response = requests.get(server_url)
    data = response.json()

    full_installation_files = []
    old_patches = []
    new_patches = []

    pre_download = data['data']['game_packages'][0].get('pre_download', {})
    main = data['data']['game_packages'][0].get('main', {})
    
    major = pre_download.get('major', {}) or main.get('major', {})
    patches = pre_download.get('patches', []) or main.get('patches', [])

    # Full Installation
    if major:
        version = major['version']
        game_pkgs = major.get('game_pkgs', [])
        for index, game_pkg in enumerate(game_pkgs, start=1):
            filename = extract_filename(game_pkg['url'], index)
            full_installation_files.append({
                'type': filename,
                'version': version,
                'url': game_pkg['url'],
                'size': format_size(game_pkg['size'])
            })

    # Patches
    for patch in patches:
        patch_data = {
            'version': patch['version'],
            'game_pkgs': [
                {
                    'type': 'Game Data',
                    'url': game_pkg['url'],
                    'size': format_size(game_pkg['size'])
                }
                for game_pkg in patch.get('game_pkgs', [])
            ]
        }
        if patch['version'] < major.get('version', ''):
            old_patches.append(patch_data)
        else:
            new_patches.append(patch_data)

    return full_installation_files, old_patches, new_patches, bool(major or patches)

# Fungsi untuk menyimpan pembaruan ke file HTML Honkai Impact 3
def save_to_html_honkai(full_installation_files, old_patches, new_patches, file_path="updates_honkai.html"):
    html_content = "<html><body>"
    html_content += "<h1>HONKAI IMPACT 3 (MANUAL UPDATE)</h1>\n"

    # Full Installation
    html_content += "<h2>Full Installation</h2>\n"
    if full_installation_files:
        grouped_files = {}
        for file in full_installation_files:
            version = file['version']
            if version not in grouped_files:
                grouped_files[version] = []
            grouped_files[version].append(file)

        for version, files in grouped_files.items():
            html_content += f"<h3>Version {version}</h3>\n<ul>"
            for file in files:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No data available for Full Installation.</p>\n"

    # Patches
    html_content += "<h2>Download From Patch</h2>\n"
    if old_patches:
        for patch in old_patches:
            html_content += f"<h3>Version {patch['version']}</h3>\n<ul>"
            for file in patch['game_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No old patches available.</p>\n"

    html_content += "<h2>New Patches</h2>\n"
    if new_patches:
        for patch in new_patches:
            html_content += f"<h3>Version {patch['version']}</h3>\n<ul>"
            for file in patch['game_pkgs']:
                html_content += f"<li><a href=\"{file['url']}\">{file['type']}</a> ({file['size']})</li>\n"
            html_content += "</ul>"
    else:
        html_content += "<p>No new patches available.</p>\n"

    html_content += "</body></html>"

    with open(file_path, "w") as file:
        file.write(html_content)    



# Daftar server Honkai Impact 3
HONKAI_SERVERS = {
    'Global': "https://api.mazagung.id/game.php?id=5TIVvvcwtM",
    'Japan': "https://api.mazagung.id/game.php?id=g0mMIvshDb",
    'Korea': "https://api.mazagung.id/game.php?id=uxB4MC7nzC",
    'Overseas': "https://api.mazagung.id/game.php?id=bxPTXSET5t",
    'Asia': "https://api.mazagung.id/game.php?id=wkE5P5WsIf"
}

# Fungsi untuk menampilkan pilihan server Honkai Impact 3
async def update_honkai_command(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Global", callback_data='honkai_Global')],
        [InlineKeyboardButton("Japan", callback_data='honkai_Japan')],
        [InlineKeyboardButton("Korea", callback_data='honkai_Korea')],
        [InlineKeyboardButton("Overseas", callback_data='honkai_Overseas')],
        [InlineKeyboardButton("Asia", callback_data='honkai_Asia')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Pilih server Honkai Impact 3:", reply_markup=reply_markup)

# Fungsi untuk menangani callback dari pilihan server
async def honkai_server_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    # Jika tombol "Kembali" ditekan, kembali ke daftar server
    if query.data == "honkai_back":
        keyboard = [
            [InlineKeyboardButton("Global", callback_data='honkai_Global')],
            [InlineKeyboardButton("Japan", callback_data='honkai_Japan')],
            [InlineKeyboardButton("Korea", callback_data='honkai_Korea')],
            [InlineKeyboardButton("Overseas", callback_data='honkai_Overseas')],
            [InlineKeyboardButton("Asia", callback_data='honkai_Asia')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Gunakan query.message.edit_text agar tidak terjadi error
        await query.message.edit_text("Pilih server Honkai Impact 3:", reply_markup=reply_markup)
        return

    server = query.data.split('_')[1]
    server_url = HONKAI_SERVERS[server]

    full_installation_files, old_patches, new_patches, has_updates = get_game_updates_honkai(server_url)

    if has_updates:
        save_to_html_honkai(full_installation_files, old_patches, new_patches, file_path=f"updates_honkai_{server}.html")
        message = f"<b>HONKAI IMPACT 3 ({server}) (MANUAL UPDATE)</b>\n\n"

        # Full Installation
        message += "- <b>Full Installation</b>\n"
        grouped_files = {}
        for file in full_installation_files:
            version = file['version']
            if version not in grouped_files:
                grouped_files[version] = []
            grouped_files[version].append(file)

        for version, files in grouped_files.items():
            message += f" <b>Version {version}</b>\n"
            for file in files:
                message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
            message += "\n"

        # Old Patches
        message += "- <b>Download From Patch</b>\n"
        if old_patches:
            for patch in old_patches:
                message += f" <b>Version {patch['version']}</b>\n"
                for file in patch['game_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                message += "\n"
        else:
            message += " No old patches available.\n\n"

        # New Patches
        message += "***********\n"
        if new_patches:
            for patch in new_patches:
                message += f" <b>Version {patch['version']}</b>\n"
                for file in patch['game_pkgs']:
                    message += f"  <a href=\"{file['url']}\">{file['type']}</a> ({file['size']}) \n"
                message += "\n"
        else:
            current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            message += f"Update terakhir pada: {current_time}\n\n"

        # Tambahkan tombol kembali ke daftar server
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data='honkai_back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(message, parse_mode="HTML", reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data='honkai_back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text("Tidak ada pembaruan tersedia saat ini.", parse_mode="HTML", reply_markup=reply_markup)



# Fungsi utama bot
def main():
    BOT_TOKEN = "BOT TOKEN KAMU"
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("updateGI", update_gi_command))
    app.add_handler(CommandHandler("updateZZZ", update_zzz_command))
    app.add_handler(CommandHandler("updateHSR", update_hsr_command))
    app.add_handler(CommandHandler("updatehonkai", update_honkai_command))
    app.add_handler(CallbackQueryHandler(honkai_server_callback, pattern='^honkai_'))
    app.run_polling()

if __name__ == "__main__":
    main()
