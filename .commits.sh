#!/bin/bash

# Get all commit hashes and timestamps
commits=$(git log --format="%H %at" --reverse)

# Arrays to store commits that need updating
declare -a to_update_hashes
declare -a to_update_times
declare -a new_times

# Process each commit
while read -r hash timestamp; do
    # Convert Unix timestamp to date components
    day=$(date -r "$timestamp" "+%u")  # 1-7, where 1 is Monday
    hour=$(date -r "$timestamp" "+%H")
    
    # Check if commit is between 9:00-17:00 on weekdays (1-5)
    if [ "$day" -le 5 ] && [ "$hour" -ge 9 ] && [ "$hour" -lt 17 ]; then
        to_update_hashes+=("$hash")
        to_update_times+=("$timestamp")
    fi
done <<< "$commits"

# If we have commits to update
if [ ${#to_update_hashes[@]} -gt 0 ]; then
    # Calculate time range for new timestamps (5:00-7:30)
    start_time=$(date -j -f "%H:%M" "05:00" "+%H")*3600
    end_time=$(date -j -f "%H:%M" "07:30" "+%H")*3600+1800
    time_range=$((end_time - start_time))
    
    # Calculate new timestamps maintaining relative ordering
    for i in "${!to_update_times[@]}"; do
        # Calculate position in range (0 to 1) based on original ordering
        position=$(echo "scale=4; $i/${#to_update_times[@]}" | bc)
        
        # Calculate new time within our target range
        offset=$(echo "scale=4; $position * $time_range" | bc | cut -d. -f1)
        new_time=$((start_time + offset))
        
        # Keep the original date, just update the time
        orig_date=$(date -r "${to_update_times[$i]}" "+%Y-%m-%d")
        new_timestamp=$(date -j -f "%Y-%m-%d %H:%M:%S" "$orig_date $(date -r $new_time "+%H:%M:%S")" "+%s")
        new_times+=("$new_timestamp")
    done
    
    # Create filter-branch command
    filter_command="git filter-branch --env-filter '"
    for i in "${!to_update_hashes[@]}"; do
        filter_command+="if [ \$GIT_COMMIT = ${to_update_hashes[$i]} ]; then
            export GIT_AUTHOR_DATE='@${new_times[$i]}'
            export GIT_COMMITTER_DATE='@${new_times[$i]}'
        fi
        "
    done
    filter_command+="' --force HEAD"
    
    # Execute the filter-branch command
    eval "$filter_command"
    
    echo "Updated ${#to_update_hashes[@]} commits"
else
    echo "No commits need updating"
fi
