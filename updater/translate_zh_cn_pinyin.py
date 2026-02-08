import os
import json
import time
import re
from pathlib import Path
import pandas as pd
from deep_translator import GoogleTranslator
from pypinyin import lazy_pinyin

BASE = Path(__file__).resolve().parent.parent
DRAFT = BASE / 'draft' / 'zh_cn'
XLSX = DRAFT / 'transcript_zh_cn.xlsx'
CACHE_PATH = DRAFT / 'translate_cache_zh_cn.json'
OUT_XLSX = DRAFT / 'transcript_zh_cn.xlsx'

BATCH_SIZE = int(os.getenv('ZH_BATCH_SIZE', '40'))
SLEEP_SEC = float(os.getenv('ZH_SLEEP_SEC', '0.25'))
MAX_NEW = int(os.getenv('ZH_MAX_NEW', '0'))  # 0 = unlimited

translator = GoogleTranslator(source='en', target='zh-CN')


def load_cache():
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding='utf-8')


def to_pinyin(text: str) -> str:
    py = lazy_pinyin(text)
    return ' '.join(py).strip()


def format_hanzi_pinyin(hanzi: str) -> str:
    hanzi = (hanzi or '').strip()
    if not hanzi:
        return ''
    py = to_pinyin(hanzi)
    if not py:
        return hanzi
    return f"{hanzi} [{py}]"


def should_skip(s: str) -> bool:
    if s is None:
        return True
    s = str(s).strip()
    if not s:
        return True
    # placeholders / tokens are safer unchanged
    if '<!ANY_TRANSLATED' in s or '<col' in s or '</col>' in s or '<Num' in s:
        return True
    return False


def translate_batch(texts):
    try:
        res = translator.translate_batch(texts)
        if isinstance(res, list) and len(res) == len(texts):
            return res
    except Exception:
        pass

    out = []
    for t in texts:
        try:
            z = translator.translate(t)
            out.append(z)
        except Exception:
            out.append('')
        time.sleep(SLEEP_SEC)
    return out


def main():
    if not XLSX.exists():
        raise SystemExit(f'Missing file: {XLSX}')

    cache = load_cache()
    xls = pd.ExcelFile(XLSX)

    pending = []
    locations = []

    # gather untranslated rows
    for sheet in xls.sheet_names:
        df = pd.read_excel(XLSX, sheet_name=sheet)
        if 'translation' not in df.columns:
            continue
        for i, row in df.iterrows():
            eng = str(row.get('english', '') if pd.notna(row.get('english', '')) else '')
            trans = str(row.get('translation', '') if pd.notna(row.get('translation', '')) else '')

            if should_skip(eng):
                continue

            if trans.strip():
                # enforce hanzi + pinyin format even for existing values
                if '[' not in trans or ']' not in trans:
                    cache.setdefault(eng, trans)
                continue

            if eng in cache and cache[eng].strip():
                continue

            pending.append(eng)
            locations.append((sheet, i, eng))

    # de-duplicate while preserving order
    seen = set()
    uniq = []
    for t in pending:
        if t not in seen:
            seen.add(t)
            uniq.append(t)

    if MAX_NEW > 0:
        uniq = uniq[:MAX_NEW]

    print(f'Need new translations: {len(uniq)}')

    # translate
    for i in range(0, len(uniq), BATCH_SIZE):
        batch = uniq[i:i+BATCH_SIZE]
        res = translate_batch(batch)
        for en, zh in zip(batch, res):
            if zh.strip():
                cache[en] = format_hanzi_pinyin(zh)
        if i % (BATCH_SIZE * 10) == 0:
            save_cache(cache)
            print(f'Progress: {i}/{len(uniq)}')

    save_cache(cache)

    # write back workbook
    with pd.ExcelWriter(OUT_XLSX, engine='openpyxl') as writer:
        for sheet in xls.sheet_names:
            df = pd.read_excel(XLSX, sheet_name=sheet)
            if 'translation' in df.columns and 'english' in df.columns:
                for i, row in df.iterrows():
                    eng = str(row.get('english', '') if pd.notna(row.get('english', '')) else '')
                    if eng in cache and str(df.at[i, 'translation']).strip() in ('', 'nan'):
                        df.at[i, 'translation'] = cache[eng]
                    elif eng in cache and ('[' not in str(df.at[i, 'translation']) or ']' not in str(df.at[i, 'translation'])):
                        df.at[i, 'translation'] = cache[eng]
            df.to_excel(writer, sheet_name=sheet, index=False)

    print('Updated transcript_zh_cn.xlsx with Hanzi + Pinyin formatting')


if __name__ == '__main__':
    main()
