import re
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
XLSX = BASE / 'draft' / 'zh_cn' / 'transcript_zh_cn.xlsx'
OUT = Path(__file__).resolve().parent / 'char_lists' / 'all_char_zh_cn.txt'

# Keep CJK Unified Ideographs + common punctuation used in zh text rendering
PATTERN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf，。！？；：、（）《》“”‘’…—·【】]')


def main():
    xls = pd.ExcelFile(XLSX)
    chars = set()
    for s in xls.sheet_names:
        df = pd.read_excel(XLSX, sheet_name=s)
        if 'translation' not in df.columns:
            continue
        for val in df['translation'].fillna(''):
            txt = str(val)
            # remove pinyin part inside [ ... ]
            txt = re.sub(r'\[[^\]]*\]', '', txt)
            for ch in PATTERN.findall(txt):
                chars.add(ch)

    # deterministic order
    ordered = ''.join(sorted(chars))
    OUT.write_text(ordered + '\n', encoding='utf-8')
    print(f'Wrote {len(chars)} chars to {OUT}')


if __name__ == '__main__':
    main()
