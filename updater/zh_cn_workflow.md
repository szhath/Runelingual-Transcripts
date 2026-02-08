# zh_cn (Mandarin + Pinyin) workflow

## 1) Machine-translate with Hanzi + Pinyin

```bash
cd updater
PYTHONUNBUFFERED=1 ZH_BATCH_SIZE=40 ZH_SLEEP_SEC=0.2 ZH_MAX_NEW=0 python3 translate_zh_cn_pinyin.py
```

- Output updates `draft/zh_cn/transcript_zh_cn.xlsx`
- Format in `translation` column: `汉字 [pin yin]`

## 2) Generate TSV from XLIFF/XLSX

```bash
cd updater
printf '7\nx\n' | python3 generate_tsv.py
```

## 3) Build Chinese character list for char image generation

```bash
cd updater
python3 build_char_list_zh_cn.py
```

Writes: `updater/char_lists/all_char_zh_cn.txt`

## 4) Generate char zip (optional, for image-based rendering)

- Font is prepared in `updater/fonts/zh_cn/Hiragino Sans GB.ttc`

Run:

```bash
cd updater
python3 update_char_images.py
```

When prompted:
- choose language index for `zh_cn`
- choose the `Hiragino Sans GB.ttc` font index

Output:
- `draft/zh_cn/char_zh_cn.zip`

## 5) Copy draft package to public (without pushing)

```bash
rsync -av --exclude '*.xlsx' draft/zh_cn/ public/zh_cn/
python3 updater/update_hash.py
```
