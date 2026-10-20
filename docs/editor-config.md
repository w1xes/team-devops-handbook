# Спільні налаштування редактора та Git

Відповідальний: @w1xes. Конфігурації розраховані на Python, POSIX shell,
Markdown і Makefile у наступних лабораторних із консольними утилітами.

## `.editorconfig`

EditorConfig застосовує редактор із підтримкою стандарту або плагіном;
сам Git не переформатовує файли. Ближчий файл і пізніша відповідна секція
перевизначають попередні значення.

| Ключ / секція | Значення | Чому для цього довідника |
| --- | --- | --- |
| `root` | `true` | не успадковувати випадкові налаштування батьківської теки |
| `[*].charset` | `utf-8` | український текст і переносимість без локальних кодувань |
| `end_of_line` | `lf` | shell-скрипти Linux не повинні отримувати CRLF у shebang |
| `insert_final_newline` | `true` | текстові UNIX-інструменти очікують завершений останній рядок |
| `trim_trailing_whitespace` | `true` | уникати невидимих змін; pre-commit перевіряє індекс |
| `indent_style` | `space` | стабільний вигляд незалежно від ширини табуляції |
| `indent_size` | `2` | компактні YAML/JSON і вкладені списки Markdown |
| `[*.py].indent_size` | `4` | конвенція Python/PEP 8, структура блоків видима |
| `[*.sh].indent_size` | `4` | узгоджені з Python багаторядкові блоки умов і циклів |
| `[*.md].trim_trailing_whitespace` | `false` | два кінцеві пробіли можуть означати жорсткий перенос Markdown |
| `[Makefile].indent_style` | `tab` | рецепти Make потребують справжню табуляцію |
| `[Makefile].indent_size` | `tab` | не перетворювати обов'язкову табуляцію на пробіли |

Налаштування для `.py`/`.sh` відрізняються від Markdown/YAML, Makefile має
окремий стиль. Ширину 4 для shell обрано для спільного читання скриптів з Python,
а не через вимогу синтаксису shell: 2 також синтаксично коректно. Саме таку
семантичну різницю демонструє окрема вправа з конфліктом.

У Markdown EditorConfig зберігає осмислені кінцеві пробіли, але загальний
`pre-commit` забороняє їх у нових комітах. Для явного переносу в цьому репозиторії
використовуємо `<br>` або окремий абзац; це свідомо суворіше за можливості редактора.

### Перевірка стандартним парсером

```sh
python3 -m venv /tmp/handbook-editorconfig
/tmp/handbook-editorconfig/bin/pip install EditorConfig==0.17.1
/tmp/handbook-editorconfig/bin/python - <<'PY'
from pathlib import Path
from editorconfig import get_properties
for name in ('example.py', 'example.sh', 'example.md', 'Makefile'):
    print(name, dict(get_properties(str(Path(name).resolve()))))
PY
```

Очікуємо `indent_size=4` для Python і shell, `2` для Markdown,
`indent_style=tab` для Makefile; `trim_trailing_whitespace=false` лише для Markdown.

## `.gitignore`

| Правила | Що і чому виключаємо |
| --- | --- |
| `.env`, `.env.*`, `!.env.example` | локальні змінні та секрети; дозволено тільки очищений приклад |
| `__pycache__/`, `*.py[cod]` | байткод і кеші Python, які відтворюються автоматично |
| `.venv/`, `venv/` | локальне середовище Python, залежне від машини |
| `*.tar`, `*.tar.gz`, `*.tgz`, `*.zip` | архіви результатів і резервні копії, не джерельні файли |
| `*.exe`, `*.o`, `/build/`, `/dist/` | результати компіляції; виконувані файли без розширення зберігаємо у `build/` |
| `.vscode/`, `.idea/`, `*.swp`, `.DS_Store` | локальні налаштування IDE, тимчасові файли й метадані ОС |
| `/CHANGELOG.md` | згенерований звіт за поточною історією, а не ручний документ |

Не ігноруємо всі виконувані файли: shell-скрипти й хуки потрібно версіонувати.
`.gitignore` не прибирає вже відстежувані файли й не захищає секрет після push.
У разі витоку треба відкликати секрет; самого додавання шаблону недостатньо.

### Перевірка на реальних артефактах

Виконувати після коміту потрібних змін: початковий `git status --short` має бути
порожнім. Файли створюємо в новій тимчасовій теці всередині клону.

```sh
fixture=$(mktemp -d .ignore-check.XXXXXX)
mkdir -p "$fixture/__pycache__" build
printf 'sample\n' > "$fixture/source.txt"
tar -czf "$fixture/sample.tar.gz" -C "$fixture" source.txt
printf 'LAB_EXAMPLE=dummy\n' > "$fixture/.env"
printf 'cache\n' > "$fixture/__pycache__/example.pyc"
printf 'int main(void) { return 0; }\n' | cc -x c -o build/ignore-check -
rm "$fixture/source.txt"
git check-ignore "$fixture/sample.tar.gz" "$fixture/.env" \
    "$fixture/__pycache__/example.pyc" build/ignore-check
git status --short
# Приберіть лише створені цією вправою файли, не чужий build/.
rm "$fixture/sample.tar.gz" "$fixture/.env" "$fixture/__pycache__/example.pyc"
rmdir "$fixture/__pycache__" "$fixture"
rm build/ignore-check
```

`git check-ignore` має перелічити всі чотири артефакти, а `git status` — залишитися
порожнім. Шлях `build/ignore-check` повинен бути вільним до запуску; не
перезаписуйте існуючий результат іншої роботи.
