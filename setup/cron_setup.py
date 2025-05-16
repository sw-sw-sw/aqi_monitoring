import subprocess

# シェルコマンドを実行
command = "crontab /home/sw/aqi_monitoring/setup/cron_setup.txt && crontab -l"
result = subprocess.run(command, shell=True, capture_output=True, text=True)

if result.returncode != 0:
    print("エラーが発生しました:")
    print(result.stderr)
else:
    print("成功しました:")
    print(result.stdout)
    
# 実行結果を表示
print("標準出力:", result.stdout)
print("標準エラー:", result.stderr)
print("終了コード:", result.returncode)