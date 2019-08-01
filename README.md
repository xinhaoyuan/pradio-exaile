PRadio frontend as an Exaile plugin

# Usage

Put `pradio/` into `$HOME/.local/share/exaile/plugins`. Create the directory if not existed.

Or run `install.sh`.

# Configure

Self-explanatory example in `$HOME/.config/exaile/settings.ini`:

```
[plugin/pradio]
enabled = L: ['dbfm']
dbfm = L: ['python3', '-m', 'dbfm']
```

`dbfm` (https://github.com/xinhaoyuan/dbfm) is a PRadio backend for douban.fm.
