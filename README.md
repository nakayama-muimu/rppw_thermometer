# Raspberry Pi Pico W で温度センサーを作る

## 方針

- 温度センサーをADCにつなぎ，測定する
  - 内蔵のセンサーも併用する
- 一定間隔で測定し，WiFiでネット接続し，クラウドで記録する
  - PC接続でなくスタンドアローンで動作するようにする
- micropython で書く

## 使ったセンサーと接続先

- MCP9700A-E/TO
  - 秋月で税込60円
  - 動作電圧が，Picoの供給する3.3VでOK
    - センサーによっては4V以上を要求するものもあるので注意
- ADC(0)につなぐ，接続は次の通り

センサー足|Pico W のピン
--|--
左：V DD|36
中：V OUT|31
右：GND|33

## 処理の流れ

### Raspberry Pi Pico W 側での処理

- WiFiつなぐ
- ntpで時刻調整する
  - 証明書の処理で必要だった
  - 時刻合わせしないと，未来に発行された証明書になってしまう
- machine.Timerで測定etc.の処理を定期実行する
  - 温度は1秒間隔で10回測定し，平均値をとる
  - クラウドに投げる
  - 日付が変わっていたら，再度，ntp同期を実施する
    - その際，一度タイマーを止めて，ntp同期を実施し，再度，タイマーを設定する必要あり

### クラウド側の処理

- AWS IoT Core で受信する
- DynamoDB に入れる
  - こんな感じで記録される

  sensor_id|datetime|temperature_external|temperature_internal
  --|--|--|--
  picoW_01|2024-06-25T23:22:22+09:00|27.83538|31.81947
  picoW_01|2024-06-25T23:22:52+09:00|27.87567|31.86628
  picoW_01|2024-06-25T23:23:22+09:00|27.81927|31.72584

## 構築手順

1. micropython を Pico W に入れる
1. AWS IoT Core で 'thing' を登録
   - 証明書をダウンロードしておく
   - CAファイルも必要なのでゲットしておく
1. 証明書を openssl で変換する
   - DER形式にする
   - private key の変換は注意が必要（後述）
1. Pico W に umqtt.simpleを入れる
1. Pico W に必要なファイルを入れる
1. Pico W で main.py を実行する
1. AWS IoT Core で受信できているか確認
   - MQTT テストクライアント > トピックをサブスクライブ で確認
1. DynamoDB のテーブルを作成
1. AWS IoT Core で DynamoDB に入れる処理を用意
   - メッセージのルーティング > ルール で設定する

## メモ

- 温度センサーのバラつき
  - 内蔵の温度センサーは，初回測定時に低い値になる場合があった
  - 一方で使っていると外部センサーより高くなった
  - 同じ構成をもう１つ作ったら，外部センサーのほうが高くなった
- そもそもの精度は？
  - センサー素子そのものの誤差
  - 供給電圧3.3Vがどれくらい正確か？

## umqtt.simple version 1.4.0 での変更点の対応

世の中の情報は，1.3.x のものがほとんど。
だが，1.4.0 で大きく変わり，SSL Contextを自分で用意する方式になった

- AWS IoT Core で発行したもののうち，以下を DER 形式に変換して使う
  - XXX...-certificate.pem.crt
  - XXX...-private.pem.key
  - AmazonRootCA1.pem
- 上記のうち，private keyは，`openssl rsa ...` ではなく，`openssl pkey...`　で変換する必要がある
- ファイル名を渡せば開いて読み込んでくれるので，1.3.xのように自分でオープンする必要はない

なお，AWS IoTの画面の，接続 > 1個のデバイスを接続，で登録した場合，ファイル名が異なる

- 接続キットのZipを解凍すると出てくる証明書は，デバイスIDがファイル名に入っている
- 接続確認用のスクリプトを実行してCAをダウンロードすると，root-CA.crt で保存されていた

## 課題, TODO

- メモリ不足になる時がある
  - 何度も実行→中止をしていると発生する(?)
  - Pico W の電源再投入が一番確実（USB抜いて差し直す）
  - 本当はきちんと調べてGC実行を入れたりすべきであろう
