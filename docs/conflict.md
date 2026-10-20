# Один конфлікт, два вирішення

Відповідальний: @w1xes. [PR #2](https://github.com/w1xes/team-devops-handbook/pull/2)
та [PR #3](https://github.com/w1xes/team-devops-handbook/pull/3) створено від
спільної бази `6dc7aa5`, у якій `.editorconfig` ще не було. Це дві альтернативи
**одного** автора, а не незалежні роботи двох учасників.

| Гілка | Налаштування shell | Результат |
| --- | --- | --- |
| `feature/w1xes-editor-settings` | `indent_size = 4` | PR #2 злитий першим |
| `feature/w1xes-editor-conflict` | `indent_size = 2` | під час merge актуальної main виник add/add конфлікт |

## Фактичний конфлікт

`git merge origin/main` завершився кодом **1**, `git status --short` показав
`AA .editorconfig`. Повний [вивід merge](../assets/conflict/merge-command.txt)
і [вміст конфліктного файла](../assets/conflict/unresolved-editorconfig.txt)
збережено до виправлення. Суть ділянки:

```text
[*.sh]
  <<<<<<< HEAD
indent_size = 2
  =======
indent_size = 4
  >>>>>>> origin/main
```

Перед маркерами вище додано відступ лише для безпечного прикладу в Git;
точний вміст із позначенням кожного рядка — у доданому журналі.

## Помилкове вирішення: синтаксис коректний, результат неправильний

Залишити обидві секції, першу зі злитої main, другу — зі своєї гілки:

```ini
[*.sh]
indent_size = 4

[*.sh]
indent_size = 2
```

Стандартний парсер EditorConfig приймає файл; остання відповідна секція
перевизначає попередню. Shell-файл отримує **2** пробіли, всупереч узгодженим
4 у `docs/editor-config.md`. Отже, відсутність конфліктних маркерів і помилок
синтаксису не означає правильне вирішення. Такий варіант збережено тільки як
[демонстраційний fixture](../assets/conflict/wrong.editorconfig), не як робочу конфігурацію.

## Правильне вирішення

Залишено одну секцію `[*.sh]` з `indent_size = 4`, решту налаштувань збережено.
Причина — погоджений формат shell/Python і відсутність дубльованого прихованого
перевизначення. Альтернативні 2 пробіли були допустимі для shell, але рішення
не повинно мовчки змінювати вже прийнятий контракт довідника.

Після заміни файла виконано `git add .editorconfig` і створено merge-коміт
`fix(editorconfig): resolve real add-add configuration conflict`; force-push,
rebase та переписування вже прорецензованих комітів не використовувалися.

## Перевірка наслідків

Обидва повні fixtures перевірено пакетом **EditorConfig 0.17.1** у тимчасових
теках з власною `.editorconfig` і шляхом `example.sh`:

| Варіант | Парсинг | Ефективний `indent_size` |
| --- | --- | --- |
| Помилковий, дві секції | успішний | `2` |
| Правильний, одна секція | успішний | `4` |

[Фактичні властивості парсера](../assets/conflict/parser-results.json).
Робоча `.editorconfig` побайтово збігається з
[правильним fixture](../assets/conflict/correct.editorconfig).
Початкові альтернативи також збережено в `assets/conflict/branch-{a,b}.editorconfig`.
