# Project-Scoped Rules for USI Tracker

- **Progress Reporting in Console**: Whenever creating or modifying scripts that operate on lists of files/records (e.g. bulk processors, index builders, backfills), always include a clear progress reporting mechanism to the console/stdout (e.g., using `tqdm`, custom logs every N steps, or percentage progress indicators).

- **Updating Scrapers Dependency**: The default and mandatory method to update the `usi-scrapers` library in this project is to run the helper script `scripts/update_scrapers.sh`. Never manually run raw pip installs or pull updates without this script.


- **UI Controls Placement**: Buttons that perform actions or change view presentation (grid/list toggles, filters, back, refresh) go in the global `ActionBar`; view titles go in `NavbarTitle` (`getTitle()` in `app.jsx`). Views must not render their own `<h1>`, back buttons, or controls duplicating ActionBar. Share state through the DataBus. See `GEMINI.md` (Shell Layout Pattern).
