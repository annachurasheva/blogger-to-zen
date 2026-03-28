# Scraper Script Plan

## Menu System
1. Enter site address
2. Enter tag
3. Exit

## File Organization
- Output directory: `output_samples/Проект R`
- Site folder: `site_name` (spaces converted to underscores)
- Tag folder: `tag_name` (spaces converted to underscores)
- Output files: `.md` and `.json`

## Output Format
- `.md` file: Contains page titles and content
- `.json` file: Contains page data structure

## Repeat Option
- Save last site address for repeat use
- Allow tag correction

## Integration
- Use existing `src/rss_fetcher.py` structure
- Add error handling for invalid inputs

## Testing
- Validate folder creation
- Test with sample site and tag values

## Documentation
- Include usage