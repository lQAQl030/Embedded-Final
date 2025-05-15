from matplotlib import font_manager

# 常見中文字體名稱
chinese_fonts_keywords = ["Noto", "WenQuanYi", "AR PL", "SimHei", "MS", "PingFang", "Heiti", "Kai", "Ming"]

# 搜尋中文字體
candidates = []
for font in font_manager.findSystemFonts(fontpaths=None, fontext='ttf'):
    name = font_manager.FontProperties(fname=font).get_name()
    if any(keyword in name for keyword in chinese_fonts_keywords):
        candidates.append((name, font))

# 顯示結果
if candidates:
    print("✅ 找到這些可能支援中文的字體：")
    for name, path in candidates:
        print(f" - {name} ({path})")
else:
    print("❌ 沒找到支援中文的系統字體")