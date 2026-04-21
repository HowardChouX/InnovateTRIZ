---
name: lookup-flet-docs
description: Use when asked to find Flet documentation, API references, or examples in the local docs_flet directory.
---

## Local Documentation

`/home/chou/triz-app/docs_flet/` (Flet v0.84.0 docs)

## Directory Structure

```
docs_flet/
├── controls/          # Flet control docs (*.md)
├── cookbook/           # Cookbook guides
├── getting-started/    # Getting started guides
├── publish/           # Publishing (android.md, etc.)
├── reference/         # API reference
├── services/         # Services docs
├── types/            # Type system docs
├── extend/           # Extension development
├── cli/              # CLI docs
├── fastapi/          # FastAPI integration
└── tutorials/        # Tutorials
```

## Common Lookups

### Controls by Function

| Feature | Path |
|---------|------|
| NavigationBar (bottom nav) | `docs_flet/controls/navigationbar/` |
| ListView (large lists) | `docs_flet/controls/listview.md` |
| GridView (grid) | `docs_flet/controls/gridview.md` |
| TextField (input) | `docs_flet/controls/textfield.md` |
| Container (container) | `docs_flet/controls/container.md` |
| Column/Row (layout) | `docs_flet/controls/column.md` |
| BottomSheet (bottom sheet) | `docs_flet/controls/bottomsheet.md` |
| AlertDialog (dialog) | `docs_flet/controls/alertdialog.md` |
| Snackbar (toast) | `docs_flet/controls/snackbar.md` |
| Switch (toggle) | `docs_flet/controls/switch.md` |
| Slider (slider) | `docs_flet/controls/slider.md` |
| Tabs (tabbed UI) | `docs_flet/controls/tabs/` |
| Chip (tag) | `docs_flet/controls/chip.md` |

### Cookbook Guides

| Topic | Path |
|-------|------|
| Async programming | `docs_flet/cookbook/async-apps.md` |
| Theming | `docs_flet/cookbook/theming.md` |
| Navigation and routing | `docs_flet/cookbook/navigation-and-routing.md` |
| Large lists optimization | `docs_flet/cookbook/large-lists.md` |
| Client storage | `docs_flet/cookbook/client-storage.md` |
| Custom controls | `docs_flet/cookbook/custom-controls.md` |
| Drag and drop | `docs_flet/cookbook/drag-and-drop.md` |

### Android Publishing

| Task | Path |
|------|------|
| APK/AAB build | `docs_flet/publish/android.md` |
| Binary package compatibility | `docs_flet/reference/binary-packages-android-ios.md` |

## Quick Search

### List all control docs
```bash
ls /home/chou/triz-app/docs_flet/controls/*.md | xargs -I {} basename {} .md
```

### Search keyword in docs
```bash
rg -n "<keyword>" /home/chou/triz-app/docs_flet/ --md -g "*.md"
```

### Find specific control
```bash
ls /home/chou/triz-app/docs_flet/controls/ | grep -i <control_name>
```

## Project-Specific Reference

Based on project architecture (see `CLAUDE.md`), common patterns:

1. **Entry**: `ft.app(target=async_main, assets_dir="assets")`
2. **Async event handlers**: `async def` + `await page.update_async()`
3. **Large lists**: `ft.ListView(expand=True)` not `ft.Column`
4. **Navigation**: `ft.NavigationBar` + `page.on_route_change`
5. **Theme**: `page.theme = ft.Theme(color_scheme_seed=...)` or `ft.ColorScheme(...)`

### Key Constraints (Android)

- Pure Python packages or binary packages with Android wheels only
- Build requires JDK 17 (auto-installed to `~/java/`)
- Without keystore, uses debug key for signing

## Priority

**Prefer local `docs_flet`** over web search. Local docs version is Flet v0.84.0.

## Debug Tips

View real-time logs:
```bash
tail -f /home/chou/triz-app/logs/triz_app.log
```

Quick data integrity check:
```bash
cd /home/chou/triz-app && python -c "
from src.data.triz_constants import get_triz_data_loader
loader = get_triz_data_loader()
print(f'params:{len(loader.get_all_params())}, matrix:{len(loader.get_contradiction_matrix())}, principles:{len(loader.get_40_principles())}')
"
```
