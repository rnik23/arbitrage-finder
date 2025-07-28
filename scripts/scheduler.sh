#!/bin/bash

# Simple scheduler script for running arbitrage finder
# Alternative to cron-based scheduling

echo "🕐 Starting Arbitrage Finder Scheduler..."

# Function to run arbitrage finder
run_arbitrage() {
    local sport=$1
    local bookmakers=$2
    echo "🎯 Running arbitrage scan for $sport..."
    
    python src/main_production.py \
        --sport "$sport" \
        --save-to-db \
        --include-bookmakers $bookmakers \
        --game-status all
    
    echo "✅ Completed scan for $sport"
    echo "---"
}

# Main scheduling loop
while true; do
    current_time=$(date '+%H:%M')
    day_of_week=$(date '+%u')  # 1=Monday, 7=Sunday
    
    case $current_time in
        # Every 15 minutes: MLB (during season)
        *:00|*:15|*:30|*:45)
            run_arbitrage "baseball_mlb" "DraftKings FanDuel BetMGM"
            ;;
    esac
    
    case $current_time in
        # Every 30 minutes: WNBA (during season)
        *:00|*:30)
            run_arbitrage "basketball_wnba" "DraftKings FanDuel BetMGM"
            ;;
    esac
    
    case $current_time in
        # Every hour: NBA (during season)
        *:00)
            run_arbitrage "basketball_nba" "DraftKings FanDuel BetMGM"
            ;;
    esac
    
    # On Sundays, run NFL more frequently
    if [ "$day_of_week" -eq 7 ]; then
        case $current_time in
            *:00|*:30)
                run_arbitrage "americanfootball_nfl" "DraftKings FanDuel BetMGM"
                ;;
        esac
    else
        case $current_time in
            # Every 2 hours: NFL (other days)
            *:00)
                if [ $(date '+%H') -eq 12 ] || [ $(date '+%H') -eq 14 ] || [ $(date '+%H') -eq 16 ] || [ $(date '+%H') -eq 18 ] || [ $(date '+%H') -eq 20 ]; then
                    run_arbitrage "americanfootball_nfl" "DraftKings FanDuel BetMGM"
                fi
                ;;
        esac
    fi
    
    # Sleep for 1 minute before checking again
    sleep 60
done
