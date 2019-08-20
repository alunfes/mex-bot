from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# スクリプトのあるディレクトリ以外から実行される場合（cron等での実行）、
# まず最初にカレントディレクトリを、スクリプトのあるディレクトリに変更する。
# （スクリプト自身のディレクトリに、client_secrets.json と settings.yaml が存在する必要あり）
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Googleドライブに接続
gauth = GoogleAuth()
gauth.CommandLineAuth()
drive = GoogleDrive(gauth)

# ***** 以下の説明では、この部分のみ処理ごとに記述 *****
# ルートフォルダにテキストファイルを作成
file = drive.CreateFile({'title': '新規テキストファイル.txt'})
file.SetContentString("Hello World !\n")
file.Upload()