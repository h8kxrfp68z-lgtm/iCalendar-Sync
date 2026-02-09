# 🌍 Multilingual Support / Многоязычная поддержка

## Supported Languages / Поддерживаемые языки

iCalendar Sync supports **11 languages** with full translation of all user-facing messages:

| Flag | Language | Code | Native Name |
|------|----------|------|-------------|
| 🇬🇧 | English | `en` | English |
| 🇪🇸 | Spanish | `es` | Español |
| 🇫🇷 | French | `fr` | Français |
| 🇩🇪 | German | `de` | Deutsch |
| 🇮🇹 | Italian | `it` | Italiano |
| 🇷🇺 | Russian | `ru` | Русский |
| 🇳🇱 | Dutch | `nl` | Nederlands |
| 🇸🇪 | Swedish | `sv` | Svenska |
| 🇫🇮 | Finnish | `fi` | Suomi |
| 🇩🇰 | Danish | `da` | Dansk |
| 🇺🇦 | Ukrainian | `uk` | Українська |

## Features / Возможности

### ✅ Translated
- Setup wizard messages
- All CLI prompts and questions
- Success/error notifications
- Conflict warnings
- Help messages

### ❌ Not Translated (By Design)
- Log messages (kept in English for debugging)
- Calendar/event names (user data)
- Technical parameters
- Configuration files

## Usage / Использование

### 1. Automatic Language Detection / Автоопределение

The tool automatically detects your system language:

```bash
# System will detect from your OS locale
icalendar-sync setup
```

### 2. Environment Variable / Переменная окружения

```bash
# Set language explicitly
export ICALENDAR_LANG=ru  # Russian
icalendar-sync setup

export ICALENDAR_LANG=de  # German
icalendar-sync list

export ICALENDAR_LANG=fr  # French
icalendar-sync get --calendar "Travail"
```

### 3. Python API

```python
from icalendar_sync.i18n import set_language, _

# Set language
set_language('es')  # Spanish

# Get translated string
print(_('setup_title'))  # "🔧 Configuración de iCalendar Sync"

# With parameters
print(_('available_calendars', count=5))  # "📅 Calendarios Disponibles (5):"
```

### 4. Temporary Language Override / Временная смена языка

```bash
# One-time command with specific language
ICALENDAR_LANG=uk icalendar-sync list  # Ukrainian
ICALENDAR_LANG=fi icalendar-sync get --calendar "Työ"  # Finnish
```

## Language Priority / Приоритет определения

1. **ICALENDAR_LANG** environment variable
2. **System locale** (detected automatically)
3. **English** (default fallback)

## Examples / Примеры

### 🇷🇺 Russian (Русский)

```bash
export ICALENDAR_LANG=ru
icalendar-sync setup
```

Output:
```
🔧 Настройка iCalendar Sync

Для использования iCalendar Sync необходимо настроить учетные данные iCloud.
⚠️  Используйте пароль для приложения, НЕ обычный пароль Apple ID.

📧 Email iCloud: user@icloud.com
🔑 Пароль для приложения: ****-****-****-****

✅ Учетные данные безопасно сохранены в системной связке ключей
🚀 Теперь вы можете использовать iCalendar Sync!
```

### 🇳🇱 Dutch (Nederlands)

```bash
export ICALENDAR_LANG=nl
icalendar-sync list
```

Output:
```
📅 Beschikbare Agenda's (3):

  • Persoonlijk
  • Werk
  • Familie
```

### 🇸🇪 Swedish (Svenska)

```bash
export ICALENDAR_LANG=sv
icalendar-sync get --calendar "Arbete"
```

Output:
```
📋 Händelser i 'Arbete' (5 hittade):

• Teammöte (2026-02-10 14:00)
• Projektgenomgång (2026-02-11 10:00)
```

### 🇫🇮 Finnish (Suomi)

```bash
export ICALENDAR_LANG=fi
icalendar-sync create --calendar "Työ" --json event.json
```

Output:
```
⚠️  Varoitus: 1 ristiriitainen tapahtuma(a) löydetty:
   - Tiimin kokous (2026-02-10 14:00:00 - 2026-02-10 15:00:00)

Jatka silti? (k/e): k
✅ Tapahtuma 'Projektin deadline' luotu onnistuneesti
```

### 🇩🇰 Danish (Dansk)

```bash
export ICALENDAR_LANG=da
icalendar-sync delete --calendar "Arbejde" --uid "abc123"
```

Output:
```
🗑️  Begivenhed slettet med succes
```

### 🇺🇦 Ukrainian (Українська)

```bash
export ICALENDAR_LANG=uk
icalendar-sync setup
```

Output:
```
🔧 Налаштування iCalendar Sync

Для використання iCalendar Sync потрібно налаштувати облікові дані iCloud.
⚠️  Використовуйте пароль для застосунку, НЕ звичайний пароль Apple ID.

📧 Email iCloud: user@icloud.com
🔑 Пароль для застосунку: ****-****-****-****

✅ Облікові дані безпечно збережено у системній зв'язці ключів
🚀 Тепер ви можете використовувати iCalendar Sync!
```

## Translation Coverage / Покрытие переводов

### Message Categories / Категории сообщений

- **Setup Messages**: 15 strings
- **Calendar Operations**: 4 strings
- **Error Messages**: 30 strings
- **Warnings**: 4 strings
- **Info Messages**: 6 strings

**Total**: ~60 translated strings per language

## Adding New Languages / Добавление языков

To add a new language:

1. Add language code to `SUPPORTED_LANGUAGES` in `i18n.py`
2. Create translation dictionary in `TRANSLATIONS`
3. Translate all ~60 message keys
4. Test with `ICALENDAR_LANG=<code>`
5. Submit pull request

### Template for New Language

```python
TRANSLATIONS['xx'] = {
    'setup_title': '🔧 Your Translation Here',
    'setup_intro': 'Your translation...',
    # ... all other keys
}
```

## Testing / Тестирование

```bash
# Test all languages
for lang in en es fr de it ru nl sv fi da uk; do
  echo "Testing $lang..."
  ICALENDAR_LANG=$lang icalendar-sync list
done

# Test specific language
ICALENDAR_LANG=ru python -c "from icalendar_sync.i18n import _; print(_('setup_title'))"
```

## Known Limitations / Известные ограничения

1. **Yes/No Prompts**: Some languages use different letters (y/n, j/n, k/e, s/n, o/n)
   - English: y/n
   - German: j/n (ja/nein)
   - Finnish: k/e (kyllä/ei)
   - Spanish/Italian: s/n (sí/no, sì/no)
   - French: o/n (oui/non)
   - Russian/Ukrainian: y/n (yes/no for compatibility)
   - Dutch/Swedish/Danish: j/n (ja/nej, ja/nee)

2. **Date/Time Formats**: Currently ISO 8601 only

3. **Number Formats**: No localization (1,000 vs 1.000 vs 1 000)

## Contributing Translations / Участие в переводах

We welcome translation contributions!

**Requirements**:
- Native or fluent speaker
- Maintain consistent tone (professional, helpful)
- Preserve emoji and formatting
- Test with real commands

**Priority Languages** (not yet supported):
- 🇵🇹 Portuguese (pt)
- 🇧🇷 Brazilian Portuguese (pt-br)
- 🇯🇵 Japanese (ja)
- 🇰🇷 Korean (ko)
- 🇨🇳 Chinese Simplified (zh-cn)
- 🇹🇼 Chinese Traditional (zh-tw)
- 🇵🇱 Polish (pl)
- 🇹🇷 Turkish (tr)

## Support / Поддержка

If you find translation errors or have suggestions:

- **GitHub Issues**: [Report translation issues](https://github.com/h8kxrfp68z-lgtm/OpenClaw/issues)
- **Email**: translations@clawhub.ai

---

**Last Updated**: February 9, 2026  
**Version**: 2.3.0  
**Languages**: 11
