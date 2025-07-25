# Multi-Media Sections Support

This document explains how to use multiple Media sections simultaneously in BlurayPoster.

## Overview

BlurayPoster now supports running multiple Media sections at the same time. This allows you to:
- Run both FileCatcher (HTTP API) and Emby integration simultaneously
- Add custom Media executors alongside existing ones
- Handle different media sources through different Media sections
- **Maintain backward compatibility** with existing configurations

## Why Multiple Media Sections?

This approach is **much better** than multiple executors under one Media section because:

### ✅ **Perfect Backward Compatibility**
- Existing configurations work **without any changes**
- No need to restructure existing Media sections
- All existing parameters stay at the same level

### ✅ **Cleaner Configuration**
- Each Media section has its own complete configuration
- No parameter indentation issues
- Easier to understand and maintain

### ✅ **Simple Migration**
- Users just add a new Media section (Media2, Media3, etc.)
- Existing Media section remains completely untouched
- Minimal configuration changes required

## Configuration

### Single Media Section (Existing Format)

The original configuration format continues to work unchanged:

```yaml
Media:
  Executor: media.emby.Emby
  Server: http://your-emby-server:8096
  ApiKey: your-api-key
  # ... all existing parameters stay the same
```

### Multiple Media Sections (New Format)

To add additional Media sections, simply add Media2, Media3, etc.:

```yaml
# First Media section - Emby (unchanged)
Media:
  Executor: media.emby.Emby
  Server: http://your-emby-server:8096
  ApiKey: your-api-key
  # ... all existing Emby parameters

# Second Media section - FileCatcher (new)
Media2:
  Executor: media.filecatcher.FileCatcher
  # FileCatcher specific configuration

# Third Media section - Another executor (optional)
Media3:
  Executor: media.other_executor.OtherExecutor
  # Other executor specific configuration
```

## Example Configurations

### Example 1: Emby + FileCatcher

```yaml
# Keep existing Emby configuration unchanged
Media:
  Executor: media.emby.Emby
  Server: http://your-emby-server:8096
  ApiKey: your-api-key
  # ... all other Emby parameters

# Add FileCatcher as a new Media section
Media2:
  Executor: media.filecatcher.FileCatcher
  # FileCatcher runs on port 7507 by default
```

### Example 2: Multiple FileCatcher Instances

```yaml
Media:
  Executor: media.emby.Emby
  # ... Emby configuration

Media2:
  Executor: media.filecatcher.FileCatcher
  # First FileCatcher instance

Media3:
  Executor: media.filecatcher.FileCatcher
  # Second FileCatcher instance
  # Note: You'll need to modify FileCatcher to support different ports
```

## Implementation Details

### Changes Made

1. **Modified `initialize_components()` function** in `bluray_poster.py`:
   - Now scans for all Media sections (Media, Media2, Media3, etc.)
   - Supports both single Media section (backward compatibility) and multiple Media sections
   - Handles errors for individual Media sections gracefully

2. **Updated main loop** in `bluray_poster.py`:
   - Calls `start_before()` and `start()` on each Media section
   - Provides detailed logging for each Media section
   - Continues running even if some Media sections fail

### Error Handling

- If a Media section fails to initialize, it logs an error but continues with other sections
- If all Media sections fail to initialize, the application exits
- Each Media section's `start_before()` and `start()` methods are called independently

### Logging

The application now provides detailed logging for multiple Media sections:

```
INFO: Media initialized successfully: media.emby.Emby
INFO: Media2 initialized successfully: media.filecatcher.FileCatcher
INFO: Successfully initialized 2 Media section(s)
INFO: Media section 1 start_before() completed
INFO: Media section 2 start_before() completed
INFO: Media section 1 start() completed
INFO: Media section 2 start() completed
INFO: Main application running with 2 Media section(s)
```

## Usage Examples

### Migration from Single to Multiple

1. **Your existing config stays exactly the same**:
   ```yaml
   Media:
     Executor: media.emby.Emby
     Server: http://your-emby-server:8096
     ApiKey: your-api-key
     # ... all existing parameters
   ```

2. **Just add a new Media section**:
   ```yaml
   Media:
     Executor: media.emby.Emby
     Server: http://your-emby-server:8096
     ApiKey: your-api-key
     # ... all existing parameters

   Media2:
     Executor: media.filecatcher.FileCatcher
   ```

3. **Start the application** - both sections will run simultaneously

### Testing Multiple Media Sections

1. **Test Emby**: Trigger playback from Emby interface
2. **Test FileCatcher**: Send HTTP POST to `http://your-server:7507/play`
3. **Both should work independently** and control the same Blu-ray player

## Advantages Over Multiple Executors Approach

| Aspect | Multiple Media Sections | Multiple Executors |
|--------|------------------------|-------------------|
| **Backward Compatibility** | ✅ Perfect - no changes needed | ❌ Requires restructuring |
| **Configuration Complexity** | ✅ Simple - just add new sections | ❌ Complex - nested parameters |
| **Migration Effort** | ✅ Minimal - just add Media2 | ❌ High - restructure everything |
| **Parameter Indentation** | ✅ None - same level as before | ❌ Deep nesting required |
| **Maintenance** | ✅ Easy to understand | ❌ Harder to maintain |

## Limitations and Considerations

1. **Shared Resources**: All Media sections share the same Player, TV, and AV instances
2. **Port Conflicts**: If multiple sections try to use the same port, conflicts may occur
3. **Error Isolation**: Errors in one Media section don't affect others
4. **Configuration**: Each Media section can have its own complete configuration

## Troubleshooting

### Common Issues

1. **"No valid Media sections found"**: Check that at least one Media section has a valid `Executor` field
2. **"Error importing module"**: Ensure the Media executor module exists and is properly formatted
3. **Port conflicts**: Check that no two sections are trying to use the same port

### Debug Mode

To debug issues, set the log level to debug:

```yaml
LogLevel: debug
```

This will provide more detailed logging about the initialization and operation of each Media section.

## Future Enhancements

Potential improvements for multi-media support:
- Per-section configuration validation
- Section-specific error handling and recovery
- Load balancing between sections
- Section health monitoring and restart capabilities
- Section-specific logging levels 