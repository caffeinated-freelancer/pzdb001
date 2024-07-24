
# Change Log

## [1.0.1] - 2024-7-24

### Added
- 增加 ChangeLog 關於 1.0.0 版, config.yaml 檔的修改
- 更新 config-sample.yaml 檔 
- config.yaml 檔增加的部份如下

```yaml
# Google 試算表相關設定
google:
  spreadsheets:
    # 當前的班級成員
    class_members:
      # 可調整欄位名稱
      fields_map:
        sn: '總序'
        studentId: '學員編號(公式)'
        className: '班級'
        classGroup: '組別'
        fullName: '姓名'
        dharmaName: '法名'
        gender: '性別'
        senior: '學長'
        deacon: '執事'
        # 可多筆升班意願
        nextClasses:
          - '學員上課班別'
          - '發心上第二班禪修班'

# MS Excel 的相關詋定
excel:
  # 學員基本資料更新
  member_details_update:
    spreadsheet_folder: '{WORKSPACE}\學員資料更新'
    header_row: 1
```

### Fixed
- 修正主程式測試用的 Flag 被開啟的問題
 
## [1.0.0] - 2024-7-24
 
### Added

- 增加讀取 B 表, 重新產生學長電聯表, 同時對未分配組別的學員做人數少的組優先的分配。
- 增加學員基本資料的匯出及匯入更新的功能。
- 增加 Change Log。
- 讀取 Google Spreadsheet 時, 也可以讀取公式。
- 增加讀取 Access 資料庫中, 已領取福慧卡的名單。(規格未明確, 暫時只做到此)
 
### Changed

- 新班 A, B 表樣版調整
- - 「自動編班資訊」改為「備註」。在 A 表產出時提供編班參考資訊, 改成 B 表時, 可以人工填上需要資訊。
- - 增加「B 表處理備註」, 程式處理 B 表時的處理資訊會寫在這裡, 「備註」的部份則保留不動。
 
### Fixed

- 修改介紹人的學員身份檢查時，忽略基本資料是否存在此姓名。
- 修正 Log Level 設定無法在 stderr 上生效的問題。
- 修正讀取 Google 的升班調查中, 升班意願轉成 set 的 BUG。
- 修正介紹人有兩個班以上時, 以學長/副學長為優先。
 
## [0.1.3] - 2024-7-18
  
### Added

- 介紹人電聯表"喫茶趣"欄位未顯示。
- 介紹人電聯表每換介紹人時, 增加表頭一次。
- 升班調查改直接讀取 Google 試算表。其中, 程式使用的欄位名稱可透過設定檔調整。
- 增加 TODO
 
### Changed
  
- 學長升班分班資料在低班而在高班沒能分配到原班。
- - 說明: 僅調整那些上課班名跟意願班名相同的至上課班級。
- BUG: 介紹人電聯表兒童班問題(沒有學長, 還是應由介紹人連絡)。
 
### Fixed
 