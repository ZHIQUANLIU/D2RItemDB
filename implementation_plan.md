# Implementation Plan: Auto-populate Default Item Attributes

This plan adds a feature to automatically fill in the base requirements and stats of an item (like Required Level, Strength, Dexterity, Defense, etc.) when its name is selected in the "Add My Item" page.

## User Review Required

> [!IMPORTANT]
> **Base Stats vs. Variable Stats**: This feature will populate *fixed* base stats (like a weapon's base requirements or a unique item's fixed required level). It will not attempt to guess variable stats (like Enhanced Defense rolls) unless they are fixed in the database.

## Proposed Changes

### [app.py](file:///c:/OpenCode/D2RItemDB/app.py)

#### [NEW] API Endpoint `/api/item-defaults`
- Create a new route accepting `type` and `name` as query parameters.
- Search across the item tables (`weapons`, `armor`, `unique_items`, `set_items`, `misc`, `gems`, `runes`) to find the matching item.
- Return a JSON object mapped to form field names:
  - `req_level` (from `levelreq`)
  - `req_str` (from `reqstr`)
  - `req_dex` (from `reqdex`)
  - `defense` (from `maxac` or `defense`)
  - `damage_min` / `damage_max` (from `mindam` / `maxdam`)
  - `sockets` (from `sockets`)
  - `durability` (from `durability`)

### [my_items_add.html](file:///c:/OpenCode/D2RItemDB/templates/my_items_add.html)

#### [MODIFY] JavaScript logic
- Add an event listener to the `#item_id` input field.
- When the value changes and matches an item in the datalist, trigger a fetch to `/api/item-defaults`.
- Iterate through the returned JSON and update the form fields using the existing `setFormValue` function.
- Add visual feedback (like a brief highlight) to the fields that were auto-populated.

## Open Questions

- **Category Mapping**: If a user selects a name that is only in the Unique table, we should automatically update the "Item Type" dropdown to "Unique" to ensure the form behaves correctly.

## Verification Plan

### Manual Verification
- **Unique Item**: Select "Harlequin Crest" (军帽) -> Check if Level 62 requirement appears.
- **Base Armor**: Select "Archon Plate" (执政官铠甲) -> Check if Str 103 requirement appears.
- **Base Weapon**: Select "Phase Blade" (幻化之刃) -> Check if Dex 136 requirement appears.
- **Switching Types**: Verify that switching item types clearing/updating correctly.
