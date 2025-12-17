#!/usr/bin/env bash
# Automatic Session File Cleanup
# Prevents large session files from exceeding Claude Code's 25K token Read limit

# Silent operation
exec 2>/dev/null

# Configuration
MAX_FILE_SIZE_KB=400  # ~25K tokens ≈ 400KB (conservative estimate)
SESSION_DIRS=(
    "/mnt/c/Users/Quantum/.claude/memory/session/history"
    "/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/.claude/memory/session/history"
    "/mnt/c/Users/Quantum/Downloads/.claude/memory/session/history"
)

# Archive directory
ARCHIVE_DIR="/mnt/c/Users/Quantum/.claude/memory/archived_sessions"
mkdir -p "$ARCHIVE_DIR"

# Function to archive large files
archive_large_files() {
    local session_dir="$1"

    [ ! -d "$session_dir" ] && return 0

    # Find files larger than limit
    find "$session_dir" -name "*.json" -size +${MAX_FILE_SIZE_KB}k 2>/dev/null | while read -r file; do
        # Create archive filename with timestamp
        local filename=$(basename "$file")
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local archive_file="$ARCHIVE_DIR/${filename%.json}_archived_${timestamp}.json"

        # Move to archive (compress if available)
        if command -v gzip >/dev/null 2>&1; then
            gzip -c "$file" > "${archive_file}.gz" 2>/dev/null
        else
            mv "$file" "$archive_file" 2>/dev/null
        fi

        # Create small placeholder
        echo "{\"archived\": true, \"original_file\": \"$filename\", \"archive_location\": \"$archive_file\", \"reason\": \"Exceeded 25K token limit\"}" > "$file"
    done
}

# Clean each session directory
for dir in "${SESSION_DIRS[@]}"; do
    archive_large_files "$dir"
done

# Also clean up old archived files (keep last 30 days)
find "$ARCHIVE_DIR" -name "*.json*" -mtime +30 -delete 2>/dev/null

exit 0
